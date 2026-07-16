from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .seamless import seam_error
from .spec import CandidateScore, MultiViewScore, SemanticScore, ViewMetrics


def evaluate_candidate(
    candidate_id: str,
    image: Image.Image,
    preview_paths: list[Path] | None = None,
    semantic: SemanticScore | None = None,
) -> CandidateScore:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    seam = seam_error(image)
    contrast = min(float(gray.std()) / 64.0, 1.0)
    saturation_mean = float(hsv[..., 1].mean()) / 255.0
    saturation_score = max(0.0, 1.0 - abs(saturation_mean - 0.52) / 0.52)

    edges = cv2.Canny(gray, 80, 160)
    coverage = min(float(np.count_nonzero(edges)) / edges.size / 0.18, 1.0)

    seam_score = max(0.0, 1.0 - seam / 0.35)
    texture_score = 0.40 * seam_score + 0.25 * contrast + 0.20 * saturation_score + 0.15 * coverage
    multi_view = evaluate_multiview(preview_paths) if preview_paths else None
    if multi_view is not None and semantic is not None:
        total = 0.45 * texture_score + 0.30 * multi_view.total_score + 0.25 * semantic.total_score
    elif multi_view is not None:
        total = 0.65 * texture_score + 0.35 * multi_view.total_score
    elif semantic is not None:
        total = 0.75 * texture_score + 0.25 * semantic.total_score
    else:
        total = texture_score
    return CandidateScore(
        candidate_id=candidate_id,
        seam_score=seam_score,
        contrast_score=contrast,
        saturation_score=saturation_score,
        coverage_score=coverage,
        texture_score=float(texture_score),
        multi_view=multi_view,
        semantic=semantic,
        total_score=float(total),
    )


def evaluate_multiview(preview_paths: list[Path]) -> MultiViewScore:
    """Measure whether a texture remains readable across individual weapon views."""

    view_metrics: list[ViewMetrics] = []
    for path in preview_paths:
        if path.stem.endswith("_multiview"):
            continue
        rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
        corners = np.concatenate((rgb[:8, :8], rgb[:8, -8:], rgb[-8:, :8], rgb[-8:, -8:]), axis=0)
        background = np.median(corners.reshape(-1, 3), axis=0)
        color_distance = np.linalg.norm(rgb.astype(np.float32) - background, axis=2)
        mask = color_distance > 18.0
        foreground_count = int(np.count_nonzero(mask))
        if foreground_count < 32:
            raise ValueError(f"Preview contains no measurable foreground: {path}")

        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        contrast = min(float(gray[mask].std()) / 64.0, 1.0)
        saturation_mean = float(hsv[..., 1][mask].mean()) / 255.0
        saturation = max(0.0, 1.0 - abs(saturation_mean - 0.52) / 0.52)
        edges = cv2.Canny(gray, 80, 160) > 0
        detail = min(float(np.count_nonzero(edges & mask)) / foreground_count / 0.22, 1.0)
        view_metrics.append(
            ViewMetrics(
                view_name=path.stem.rsplit("_", 1)[-1],
                foreground_ratio=foreground_count / mask.size,
                contrast_score=contrast,
                saturation_score=saturation,
                detail_score=detail,
                mean_luminance=float(gray[mask].mean()) / 255.0,
            )
        )

    if len(view_metrics) < 2:
        raise ValueError("Multi-view evaluation requires at least two individual views")

    luminance = np.asarray([view.mean_luminance for view in view_metrics], dtype=np.float32)
    consistency = max(0.0, 1.0 - float(luminance.std()) / 0.20)
    contrast = float(np.mean([view.contrast_score for view in view_metrics]))
    saturation = float(np.mean([view.saturation_score for view in view_metrics]))
    detail = float(np.mean([view.detail_score for view in view_metrics]))
    total = 0.30 * contrast + 0.25 * saturation + 0.30 * detail + 0.15 * consistency
    return MultiViewScore(
        views=tuple(view_metrics),
        consistency_score=consistency,
        total_score=float(total),
    )
