from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np
from PIL import Image

from .asset_spec import AssetSpec
from .obj_renderer import ObjMesh
from .uv_asset import semantic_face_labels
from .weapon_space import UVGeometryMaps


_ROLE_ORDER = {"background": 0, "connector": 1, "secondary": 2, "hero": 3}
_ROLE_OPACITY = {"background": 1.0, "connector": 0.72, "secondary": 0.72, "hero": 0.96}


def has_explicit_composition_graph(bundle: Mapping[str, Any]) -> bool:
    weapon = bundle.get("weapon_theme")
    graph = weapon.get("composition_graph") if isinstance(weapon, Mapping) else None
    groups = graph.get("groups") if isinstance(graph, Mapping) else None
    return (
        isinstance(groups, (list, tuple))
        and bool(groups)
        and str(graph.get("strategy", "legacy_semantic_roles"))
        != "legacy_semantic_roles"
    )


def compose_groups_in_uv_regions(
    bundle: Mapping[str, Any],
    mesh: ObjMesh,
    maps: UVGeometryMaps,
    spec: AssetSpec,
    content_images: Mapping[str, Image.Image],
    *,
    base_color: tuple[int, int, int],
    diagnostic_dir: Path | None = None,
) -> Image.Image:
    """Fit each generated group only into its declared mesh-derived UV regions."""

    weapon = bundle.get("weapon_theme")
    graph = weapon.get("composition_graph") if isinstance(weapon, Mapping) else None
    groups = graph.get("groups") if isinstance(graph, Mapping) else None
    if not isinstance(groups, (list, tuple)) or not groups:
        raise ValueError("explicit composition graph is required")

    face_labels, regions = semantic_face_labels(
        mesh,
        spec.semantic_regions,
        spec.default_region,
    )
    region_index = {region.name: index for index, region in enumerate(regions)}
    pixel_labels = np.full(maps.face_index.shape, -1, dtype=np.int32)
    pixel_labels[maps.valid_mask] = face_labels[maps.face_index[maps.valid_mask]]

    height, width = maps.valid_mask.shape
    result = np.empty((height, width, 3), dtype=np.float32)
    result[:] = np.asarray(base_color, dtype=np.float32)
    diagnostic_dir = Path(diagnostic_dir) if diagnostic_dir is not None else None
    if diagnostic_dir is not None:
        diagnostic_dir.mkdir(parents=True, exist_ok=True)

    ordered = sorted(
        (dict(group) for group in groups),
        key=lambda group: (
            _ROLE_ORDER.get(str(group.get("semantic_role")), 9),
            str(group.get("group_id")),
        ),
    )
    for group in ordered:
        group_id = str(group.get("group_id", "")).strip()
        role = str(group.get("semantic_role", "")).strip()
        mode = str(group.get("composition_mode", "")).strip()
        components = tuple(str(value) for value in group.get("components", ()))
        surfaces = {str(value) for value in group.get("surfaces", ())}
        if not group_id or not components:
            raise ValueError("composition group is incomplete")
        unknown = set(components) - region_index.keys()
        if unknown:
            raise ValueError(
                f"composition group {group_id} has no UV regions for {sorted(unknown)}"
            )

        group_mask = np.isin(
            pixel_labels,
            np.asarray([region_index[name] for name in components], dtype=np.int32),
        )
        group_mask &= _surface_mask(maps, surfaces)
        if not np.any(group_mask):
            raise ValueError(f"composition group {group_id} has an empty UV target")
        source = _group_source(content_images, group_id)
        source = _normalize_source(source, spanning=mode == "spanning")
        sampled = _sample_source_to_group(
            source,
            maps,
            group_mask,
            mirror_on_right=bool(group.get("mirror_on_right", True)),
        )
        alpha = sampled[..., 3] / 255.0
        alpha *= group_mask.astype(np.float32)
        alpha *= _ROLE_OPACITY.get(role, 0.8)
        source_rgb = sampled[..., :3]
        if role == "background":
            blended = source_rgb
        else:
            blended = 255.0 - (255.0 - result) * (255.0 - source_rgb) / 255.0
        result = result * (1.0 - alpha[..., None]) + blended * alpha[..., None]

        if diagnostic_dir is not None:
            Image.fromarray(group_mask.astype(np.uint8) * 255, mode="L").save(
                diagnostic_dir / f"uv_group_mask_{group_id}.png"
            )
            overlay = np.empty((height, width, 4), dtype=np.uint8)
            overlay[..., :3] = np.rint(np.clip(source_rgb, 0, 255)).astype(np.uint8)
            overlay[..., 3] = np.rint(np.clip(alpha, 0, 1) * 255).astype(np.uint8)
            Image.fromarray(overlay, mode="RGBA").save(
                diagnostic_dir / f"uv_group_fitted_{group_id}.png"
            )

    result[~maps.valid_mask] = np.asarray(base_color, dtype=np.float32)
    return Image.fromarray(np.rint(np.clip(result, 0, 255)).astype(np.uint8), mode="RGB")


def _group_source(
    content_images: Mapping[str, Image.Image],
    group_id: str,
) -> Image.Image:
    matches = [
        image
        for layer_id, image in content_images.items()
        if layer_id == group_id or layer_id.startswith(f"{group_id}__")
    ]
    if not matches:
        raise KeyError(f"no generated source is bound to composition group {group_id}")
    return matches[0].convert("RGBA")


def _normalize_source(image: Image.Image, *, spanning: bool) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    alpha = rgba[..., 3]
    points = np.column_stack(np.nonzero(alpha > 8))
    if len(points) < 8:
        return image.convert("RGBA")
    if spanning:
        xy = points[:, ::-1].astype(np.float32)
        centered = xy - xy.mean(axis=0, keepdims=True)
        covariance = centered.T @ centered
        values, vectors = np.linalg.eigh(covariance)
        major = vectors[:, int(np.argmax(values))]
        angle = float(np.degrees(np.arctan2(major[1], major[0])))
        if angle > 90:
            angle -= 180
        if angle < -90:
            angle += 180
        image = image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
        alpha = rgba[..., 3]
    y, x = np.nonzero(alpha > 8)
    if len(x) == 0:
        return image.convert("RGBA")
    padding = max(4, round(min(image.size) * 0.02))
    box = (
        max(0, int(x.min()) - padding),
        max(0, int(y.min()) - padding),
        min(image.width, int(x.max()) + padding + 1),
        min(image.height, int(y.max()) + padding + 1),
    )
    return image.crop(box).convert("RGBA")


def _surface_mask(maps: UVGeometryMaps, surfaces: set[str]) -> np.ndarray:
    if not surfaces:
        raise ValueError("composition group surfaces must not be empty")
    normal = maps.canonical_normal
    side_dominant = np.abs(normal[..., 2]) >= np.abs(normal[..., 1])
    left = side_dominant & (normal[..., 2] < 0)
    right = side_dominant & ~left
    top = ~side_dominant
    selected = np.zeros(maps.valid_mask.shape, dtype=bool)
    if "left" in surfaces:
        selected |= left
    if "right" in surfaces:
        selected |= right
    if "top" in surfaces:
        selected |= top
    return selected & maps.valid_mask


def _sample_source_to_group(
    source: Image.Image,
    maps: UVGeometryMaps,
    group_mask: np.ndarray,
    *,
    mirror_on_right: bool,
) -> np.ndarray:
    source_array = np.asarray(source.convert("RGBA"), dtype=np.uint8)
    position = maps.canonical_position
    target_positions = position[group_mask]
    minimum = target_positions.min(axis=0)
    maximum = target_positions.max(axis=0)
    span = np.maximum(maximum - minimum, 1e-6)
    u = np.clip((position[..., 0] - minimum[0]) / span[0], 0.0, 1.0)
    side_v = np.clip(1.0 - (position[..., 1] - minimum[1]) / span[1], 0.0, 1.0)
    top_v = np.clip(1.0 - (position[..., 2] - minimum[2]) / span[2], 0.0, 1.0)
    normal = maps.canonical_normal
    right = normal[..., 2] >= 0
    if mirror_on_right:
        side_u = np.where(right, 1.0 - u, u)
    else:
        side_u = u
    top_u = u
    side = cv2.remap(
        source_array,
        (side_u * (source.width - 1)).astype(np.float32),
        (side_v * (source.height - 1)).astype(np.float32),
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
    top = cv2.remap(
        source_array,
        (top_u * (source.width - 1)).astype(np.float32),
        (top_v * (source.height - 1)).astype(np.float32),
        cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )
    side_weight = np.abs(normal[..., 2]) ** 4.0
    top_weight = np.abs(normal[..., 1]) ** 4.0
    total = np.maximum(side_weight + top_weight, 1e-8)
    mixed = (
        side.astype(np.float32) * side_weight[..., None]
        + top.astype(np.float32) * top_weight[..., None]
    ) / total[..., None]
    mixed[~group_mask] = 0.0
    return mixed
