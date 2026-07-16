from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import cv2
import numpy as np
from PIL import Image

from .obj_renderer import ObjMesh
from .uv_asset import UVSeamPair


@dataclass(frozen=True)
class ComponentStyle:
    blur_sigma: float = 0.0
    rotation_quadrants: int = 0
    contrast: float = 1.0
    saturation: float = 1.0
    motif_strength: float = 1.0

    @classmethod
    def from_dict(cls, data: Mapping[str, float | int]) -> "ComponentStyle":
        return cls(
            blur_sigma=float(data.get("blur_sigma", 0.0)),
            rotation_quadrants=int(data.get("rotation_quadrants", 0)),
            contrast=float(data.get("contrast", 1.0)),
            saturation=float(data.get("saturation", 1.0)),
            motif_strength=float(data.get("motif_strength", 1.0)),
        )


@dataclass(frozen=True)
class UVCompositionResult:
    before_asset_seam_correction: Image.Image
    after_asset_seam_correction: Image.Image
    edge_safety_map: Image.Image


class UVComposer:
    """Compose one source texture under semantic masks and UV-edge constraints."""

    def __init__(
        self,
        styles: Mapping[str, ComponentStyle],
        *,
        base_color: tuple[int, int, int],
        transition_sigma: float = 8.0,
        edge_safe_pixels: float = 16.0,
    ) -> None:
        if transition_sigma < 0:
            raise ValueError("transition_sigma cannot be negative")
        if edge_safe_pixels <= 0:
            raise ValueError("edge_safe_pixels must be positive")
        self.styles = dict(styles)
        self.base_color = tuple(int(channel) for channel in base_color)
        self.transition_sigma = float(transition_sigma)
        self.edge_safe_pixels = float(edge_safe_pixels)

    def compose(
        self,
        source: Image.Image,
        masks: Mapping[str, Image.Image],
    ) -> UVCompositionResult:
        if not masks:
            raise ValueError("At least one semantic mask is required")
        names = tuple(masks)
        arrays = [np.asarray(masks[name].convert("L"), dtype=np.float32) / 255.0 for name in names]
        shape = arrays[0].shape
        if any(mask.shape != shape for mask in arrays):
            raise ValueError("All semantic masks must have the same dimensions")
        height, width = shape
        source_rgb = np.asarray(
            source.convert("RGB").resize((width, height), Image.Resampling.LANCZOS),
            dtype=np.uint8,
        )

        hard_union = np.maximum.reduce(arrays) > 0.5
        if not np.any(hard_union):
            raise ValueError("Semantic masks contain no paintable pixels")
        soft_masks = [
            cv2.GaussianBlur(mask, (0, 0), self.transition_sigma)
            if self.transition_sigma > 0
            else mask
            for mask in arrays
        ]
        weight_sum = np.maximum(np.sum(soft_masks, axis=0), 1e-8)
        base = np.empty((height, width, 3), dtype=np.float32)
        base[:] = self.base_color
        composed = np.zeros_like(base)
        for name, soft_mask in zip(names, soft_masks, strict=True):
            style = self.styles.get(name, ComponentStyle())
            styled = _style_source(source_rgb, style, self.base_color).astype(np.float32)
            weight = (soft_mask / weight_sum)[..., None]
            composed += styled * weight
        before = np.where(hard_union[..., None], composed, base)

        corrected_image, edge_map = apply_uv_edge_safety(
            Image.fromarray(np.clip(before, 0, 255).astype(np.uint8), mode="RGB"),
            masks,
            base_color=self.base_color,
            edge_safe_pixels=self.edge_safe_pixels,
        )

        return UVCompositionResult(
            before_asset_seam_correction=Image.fromarray(
                np.clip(before, 0, 255).astype(np.uint8), mode="RGB"
            ),
            after_asset_seam_correction=corrected_image,
            edge_safety_map=edge_map,
        )


def apply_uv_edge_safety(
    image: Image.Image,
    masks: Mapping[str, Image.Image],
    *,
    base_color: tuple[int, int, int],
    edge_safe_pixels: float,
) -> tuple[Image.Image, Image.Image]:
    """Apply only the UV-edge correction so fixed candidates can be swept offline."""

    if edge_safe_pixels < 0:
        raise ValueError("edge_safe_pixels cannot be negative")
    if not masks:
        raise ValueError("At least one semantic mask is required")
    arrays = [np.asarray(mask.convert("L"), dtype=np.float32) / 255.0 for mask in masks.values()]
    shape = arrays[0].shape
    if any(mask.shape != shape for mask in arrays):
        raise ValueError("All semantic masks must have the same dimensions")
    height, width = shape
    source = np.asarray(
        image.convert("RGB").resize((width, height), Image.Resampling.LANCZOS),
        dtype=np.float32,
    )
    hard_union = np.maximum.reduce(arrays) > 0.5
    base = np.empty((height, width, 3), dtype=np.float32)
    base[:] = base_color
    if edge_safe_pixels == 0:
        edge_factor = hard_union.astype(np.float32)
    else:
        distance = cv2.distanceTransform(hard_union.astype(np.uint8), cv2.DIST_L2, 5)
        # OpenCV assigns distance 1 to the first interior pixel. Subtracting it
        # makes the sampled UV boundary exactly equal to the shared base colour.
        distance = np.maximum(distance - 1.0, 0.0)
        edge_factor = np.clip(distance / edge_safe_pixels, 0.0, 1.0)
        edge_factor = edge_factor * edge_factor * (3.0 - 2.0 * edge_factor)
    corrected = base * (1.0 - edge_factor[..., None]) + source * edge_factor[..., None]
    corrected = np.where(hard_union[..., None], corrected, base)
    return (
        Image.fromarray(np.clip(corrected, 0, 255).astype(np.uint8), mode="RGB"),
        Image.fromarray(np.rint(edge_factor * 255.0).astype(np.uint8), mode="L"),
    )


def apply_uv_seam_graph_safety(
    image: Image.Image,
    mesh: ObjMesh,
    seam_pairs: Iterable[UVSeamPair],
    *,
    base_color: tuple[int, int, int],
    seam_safe_pixels: float,
) -> tuple[Image.Image, Image.Image]:
    """Blend true paired UV seams without darkening unrelated open island edges."""

    if seam_safe_pixels < 0:
        raise ValueError("seam_safe_pixels cannot be negative")
    source = np.asarray(image.convert("RGB"), dtype=np.float32)
    height, width = source.shape[:2]
    seam_lines = np.zeros((height, width), dtype=np.uint8)
    for pair in seam_pairs:
        for indices in (pair.uv_indices_a, pair.uv_indices_b):
            uv = mesh.texcoords[np.asarray(indices)]
            if not np.all((uv >= 0.0) & (uv <= 1.0)):
                continue
            points = np.column_stack(
                (
                    uv[:, 0] * (width - 1),
                    (1.0 - uv[:, 1]) * (height - 1),
                )
            )
            points = np.rint(points).astype(np.int32)
            cv2.line(
                seam_lines,
                tuple(points[0]),
                tuple(points[1]),
                255,
                1,
                cv2.LINE_AA,
            )
    if seam_safe_pixels == 0 or not np.any(seam_lines):
        influence = np.zeros((height, width), dtype=np.float32)
    else:
        distance = cv2.distanceTransform(
            (seam_lines == 0).astype(np.uint8), cv2.DIST_L2, 5
        )
        influence = np.clip(1.0 - distance / seam_safe_pixels, 0.0, 1.0)
        influence = influence * influence * (3.0 - 2.0 * influence)
    base = np.empty_like(source)
    base[:] = base_color
    corrected = source * (1.0 - influence[..., None]) + base * influence[..., None]
    return (
        Image.fromarray(np.clip(corrected, 0, 255).astype(np.uint8), mode="RGB"),
        Image.fromarray(np.rint(influence * 255.0).astype(np.uint8), mode="L"),
    )


def apply_uv_seam_pair_averaging(
    image: Image.Image,
    mesh: ObjMesh,
    seam_pairs: Iterable[UVSeamPair],
    *,
    radius_pixels: int = 1,
    samples_per_edge: int = 32,
) -> tuple[Image.Image, Image.Image]:
    """Make paired seam texels agree by averaging their original local colours."""

    if radius_pixels < 0:
        raise ValueError("radius_pixels cannot be negative")
    if samples_per_edge < 2:
        raise ValueError("samples_per_edge must be at least 2")
    source = np.asarray(image.convert("RGB"), dtype=np.float32)
    height, width = source.shape[:2]
    accumulated = np.zeros_like(source, dtype=np.float32)
    weights = np.zeros((height, width), dtype=np.float32)
    positions = np.linspace(0.0, 1.0, samples_per_edge, dtype=np.float32)[:, None]
    offsets = [
        (dy, dx)
        for dy in range(-radius_pixels, radius_pixels + 1)
        for dx in range(-radius_pixels, radius_pixels + 1)
        if dx * dx + dy * dy <= radius_pixels * radius_pixels
    ] or [(0, 0)]
    for pair in seam_pairs:
        edge_a = mesh.texcoords[np.asarray(pair.uv_indices_a)]
        edge_b = mesh.texcoords[np.asarray(pair.uv_indices_b)]
        if not (
            np.all((edge_a >= 0.0) & (edge_a <= 1.0))
            and np.all((edge_b >= 0.0) & (edge_b <= 1.0))
        ):
            continue
        uv_a = edge_a[0] * (1.0 - positions) + edge_a[1] * positions
        uv_b = edge_b[0] * (1.0 - positions) + edge_b[1] * positions
        pixels_a = np.rint(
            np.column_stack(
                (uv_a[:, 0] * (width - 1), (1.0 - uv_a[:, 1]) * (height - 1))
            )
        ).astype(np.int32)
        pixels_b = np.rint(
            np.column_stack(
                (uv_b[:, 0] * (width - 1), (1.0 - uv_b[:, 1]) * (height - 1))
            )
        ).astype(np.int32)
        colors = (
            source[pixels_a[:, 1], pixels_a[:, 0]]
            + source[pixels_b[:, 1], pixels_b[:, 0]]
        ) * 0.5
        for pixels in (pixels_a, pixels_b):
            for dy, dx in offsets:
                x = np.clip(pixels[:, 0] + dx, 0, width - 1)
                y = np.clip(pixels[:, 1] + dy, 0, height - 1)
                np.add.at(accumulated, (y, x), colors)
                np.add.at(weights, (y, x), 1.0)
    changed = weights > 0
    corrected = source.copy()
    corrected[changed] = accumulated[changed] / weights[changed, None]
    return (
        Image.fromarray(np.clip(corrected, 0, 255).astype(np.uint8), mode="RGB"),
        Image.fromarray(changed.astype(np.uint8) * 255, mode="L"),
    )


def _style_source(
    source: np.ndarray,
    style: ComponentStyle,
    base_color: tuple[int, int, int],
) -> np.ndarray:
    image = np.rot90(source, style.rotation_quadrants % 4).copy()
    if style.blur_sigma > 0:
        image = cv2.GaussianBlur(image, (0, 0), style.blur_sigma)
    adjusted = image.astype(np.float32)
    mean = adjusted.mean(axis=(0, 1), keepdims=True)
    adjusted = (adjusted - mean) * style.contrast + mean
    hsv = cv2.cvtColor(np.clip(adjusted, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    hsv = hsv.astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * style.saturation, 0, 255)
    adjusted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
    base = np.asarray(base_color, dtype=np.float32)[None, None, :]
    return base * (1.0 - style.motif_strength) + adjusted * style.motif_strength
