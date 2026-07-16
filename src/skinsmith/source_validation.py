from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class SourceValidation:
    role: str
    passed: bool
    technical_passed: bool
    semantic_status: str
    reasons: tuple[str, ...]
    metrics: dict[str, float | int | str]

    def to_dict(self) -> dict:
        return asdict(self)


class SemanticSourceReviewer(Protocol):
    def __call__(self, role: str, prompt: str, image: Image.Image) -> tuple[bool, str]:
        ...


class SourceAssetValidator:
    """Provider-neutral structural gate for generated Route-B role images."""

    def __init__(
        self,
        semantic_reviewer: SemanticSourceReviewer | None = None,
        *,
        minimum_size: int = 256,
    ) -> None:
        self.semantic_reviewer = semantic_reviewer
        self.minimum_size = int(minimum_size)
        if self.minimum_size < 64:
            raise ValueError("minimum_size must be at least 64")

    def validate(
        self,
        role: str,
        prompt: str,
        image: Image.Image,
    ) -> SourceValidation:
        if role not in {
            "hero",
            "secondary",
            "connector",
            "background",
            "master_artwork",
        }:
            raise ValueError(f"unsupported source role: {role}")
        rgb_image = image.convert("RGB")
        rgb = np.asarray(rgb_image, dtype=np.float32)
        height, width = rgb.shape[:2]
        border_width = max(2, round(min(width, height) * 0.04))
        border_mask = np.zeros((height, width), dtype=bool)
        border_mask[:border_width] = True
        border_mask[-border_width:] = True
        border_mask[:, :border_width] = True
        border_mask[:, -border_width:] = True
        border = rgb[border_mask]
        background = np.median(border, axis=0)
        distance = np.linalg.norm(rgb - background, axis=2)
        foreground = distance > 28.0
        foreground_ratio = float(foreground.mean())
        foreground_edge_ratio = (
            float(np.count_nonzero(foreground & border_mask))
            / max(int(np.count_nonzero(foreground)), 1)
        )
        border_std = float(border.std())
        image_std = float(rgb.std())
        gray = rgb.mean(axis=2)
        gradient_x = np.abs(np.diff(gray, axis=1))
        gradient_y = np.abs(np.diff(gray, axis=0))
        detail_density = float(
            (
                np.count_nonzero(gradient_x > 10.0)
                + np.count_nonzero(gradient_y > 10.0)
            )
            / max(gradient_x.size + gradient_y.size, 1)
        )
        local_detail_densities: list[float] = []
        local_grid_size = 6
        for grid_y in range(local_grid_size):
            y0 = grid_y * height // local_grid_size
            y1 = (grid_y + 1) * height // local_grid_size
            for grid_x in range(local_grid_size):
                x0 = grid_x * width // local_grid_size
                x1 = (grid_x + 1) * width // local_grid_size
                tile = gray[y0:y1, x0:x1]
                tile_gradient_x = np.abs(np.diff(tile, axis=1))
                tile_gradient_y = np.abs(np.diff(tile, axis=0))
                local_detail_densities.append(
                    float(
                        (
                            np.count_nonzero(tile_gradient_x > 10.0)
                            + np.count_nonzero(tile_gradient_y > 10.0)
                        )
                        / max(tile_gradient_x.size + tile_gradient_y.size, 1)
                    )
                )
        low_detail_patch_ratio = float(
            np.mean(np.asarray(local_detail_densities) < 0.03)
        )
        minimum_local_detail_density = float(min(local_detail_densities))
        reasons: list[str] = []
        aspect_ratio = width / max(height, 1)
        if role == "master_artwork":
            if not 1.45 <= aspect_ratio <= 2.05:
                reasons.append(
                    "master artwork must use a landscape aspect ratio near 16:9"
                )
        elif width != height:
            reasons.append("source image must be square")
        if min(width, height) < self.minimum_size:
            reasons.append(
                f"source image must be at least {self.minimum_size} pixels per side"
            )

        if role == "master_artwork":
            if image_std < 18.0:
                reasons.append("master artwork lacks sufficient tonal or colour variation")
            if detail_density < 0.06:
                reasons.append("master artwork lacks sufficient local detail density")
            if low_detail_patch_ratio > 0.10:
                reasons.append(
                    "master artwork reserves too many large low-detail or empty regions"
                )
        elif role == "background":
            if image_std < 3.0:
                reasons.append("background field is nearly uniform and contains no usable material variation")
        else:
            maximum_ratio = {"hero": 0.62, "secondary": 0.48, "connector": 0.42}[role]
            maximum_edge = {"hero": 0.12, "secondary": 0.10, "connector": 0.08}[role]
            maximum_border_std = {"hero": 48.0, "secondary": 42.0, "connector": 38.0}[role]
            if foreground_ratio < 0.005:
                reasons.append(f"{role} source contains no measurable isolated motif")
            if foreground_ratio > maximum_ratio:
                reasons.append(f"{role} source behaves like a full material field or slab")
            if foreground_edge_ratio > maximum_edge:
                reasons.append(f"{role} motif touches too much of the square boundary")
            if border_std > maximum_border_std:
                reasons.append(f"{role} source lacks a sufficiently removable uniform border")

        technical_passed = not reasons
        if self.semantic_reviewer is None:
            semantic_passed = True
            semantic_status = (
                "not_run_master_forbidden_content_review_unavailable"
                if role == "master_artwork"
                else "not_run_requires_mapped_and_human_or_multimodal_review"
            )
        elif not technical_passed:
            semantic_passed = False
            semantic_status = "not_run_technical_gate_failed"
        else:
            semantic_passed, semantic_status = self.semantic_reviewer(
                role, prompt, rgb_image
            )
            if not semantic_passed:
                reasons.append(f"semantic reviewer rejected source: {semantic_status}")
        return SourceValidation(
            role=role,
            passed=technical_passed and semantic_passed,
            technical_passed=technical_passed,
            semantic_status=semantic_status,
            reasons=tuple(reasons),
            metrics={
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "foreground_ratio": foreground_ratio,
                "foreground_edge_ratio": foreground_edge_ratio,
                "border_std": border_std,
                "image_std": image_std,
                "detail_density": detail_density,
                "low_detail_patch_ratio": low_detail_patch_ratio,
                "minimum_local_detail_density": minimum_local_detail_density,
            },
        )
