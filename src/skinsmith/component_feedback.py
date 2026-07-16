from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Mapping

import cv2
import numpy as np
from PIL import Image

from .obj_renderer import ObjMultiViewRenderer
from .uv_compositor import ComponentStyle


@dataclass(frozen=True)
class ComponentViewMetrics:
    component: str
    view: str
    visible_pixels: int
    detail_pixels: int
    detail_density: float
    mean_luminance: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ComponentAggregateMetrics:
    component: str
    visible_views: int
    visible_pixels: int
    detail_density: float
    target_detail_density: float
    target_score: float
    relative_excess: float
    mean_luminance: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ComponentDiagnosis:
    action: str
    target_component: str | None
    relative_excess: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def render_component_visibility(
    renderer: ObjMultiViewRenderer,
    masks: Mapping[str, Image.Image],
    output_dir: Path,
) -> dict[str, list[Path]]:
    """Render reusable white-on-black visibility maps for semantic components."""

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, list[Path]] = {}
    for component, mask in masks.items():
        if not np.any(np.asarray(mask.convert("L")) > 127):
            continue
        texture = Image.merge("RGB", (mask.convert("L"),) * 3)
        outputs[component] = renderer.render(
            texture, output_dir, f"visibility_{component}"
        )
    return outputs


def measure_component_views(
    candidate_previews: list[Path],
    visibility_previews: Mapping[str, list[Path]],
    detail_targets: Mapping[str, float],
) -> tuple[list[ComponentViewMetrics], list[ComponentAggregateMetrics], float]:
    """Measure rendered detail inside component visibility maps, excluding silhouettes."""

    candidate_by_view = {
        _view_name(path): path for path in candidate_previews if not path.stem.endswith("_multiview")
    }
    per_view: list[ComponentViewMetrics] = []
    aggregates: list[ComponentAggregateMetrics] = []
    kernel = np.ones((3, 3), dtype=np.uint8)
    for component, paths in visibility_previews.items():
        component_records: list[ComponentViewMetrics] = []
        for visibility_path in paths:
            if visibility_path.stem.endswith("_multiview"):
                continue
            view = _view_name(visibility_path)
            if view not in candidate_by_view:
                continue
            candidate = np.asarray(Image.open(candidate_by_view[view]).convert("RGB"), dtype=np.uint8)
            visibility = np.asarray(Image.open(visibility_path).convert("L"), dtype=np.uint8)
            visible = visibility > 80
            eroded = cv2.erode(visible.astype(np.uint8), kernel, iterations=1) > 0
            if np.count_nonzero(eroded) >= 32:
                visible = eroded
            visible_pixels = int(np.count_nonzero(visible))
            if visible_pixels < 32:
                continue
            gray = cv2.cvtColor(candidate, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 80, 160) > 0
            detail_pixels = int(np.count_nonzero(edges & visible))
            record = ComponentViewMetrics(
                component=component,
                view=view,
                visible_pixels=visible_pixels,
                detail_pixels=detail_pixels,
                detail_density=detail_pixels / visible_pixels,
                mean_luminance=float(gray[visible].mean()) / 255.0,
            )
            per_view.append(record)
            component_records.append(record)
        if not component_records:
            continue
        visible_total = sum(record.visible_pixels for record in component_records)
        detail_density = sum(record.detail_pixels for record in component_records) / visible_total
        luminance = sum(
            record.mean_luminance * record.visible_pixels for record in component_records
        ) / visible_total
        target = float(detail_targets[component])
        target_score = max(0.0, 1.0 - abs(detail_density - target) / max(target, 1e-8))
        aggregates.append(
            ComponentAggregateMetrics(
                component=component,
                visible_views=len(component_records),
                visible_pixels=visible_total,
                detail_density=detail_density,
                target_detail_density=target,
                target_score=target_score,
                relative_excess=(detail_density - target) / max(target, 1e-8),
                mean_luminance=luminance,
            )
        )
    balance = float(np.mean([record.target_score for record in aggregates])) if aggregates else 0.0
    return per_view, aggregates, balance


def diagnose_component_detail(
    aggregates: list[ComponentAggregateMetrics],
) -> ComponentDiagnosis:
    if not aggregates:
        return ComponentDiagnosis("none", None, 0.0, "No component was visible in measurable views")
    worst = max(aggregates, key=lambda record: (record.relative_excess, record.component))
    if worst.relative_excess <= 0:
        return ComponentDiagnosis(
            "none",
            None,
            worst.relative_excess,
            "All visible components are at or below their detail targets",
        )
    return ComponentDiagnosis(
        "reduce_component_detail",
        worst.component,
        worst.relative_excess,
        (
            f"{worst.component} rendered detail density {worst.detail_density:.6f} exceeds "
            f"target {worst.target_detail_density:.6f} by {worst.relative_excess:.2%}"
        ),
    )


def make_detail_reduction_style(style: ComponentStyle, intensity: int) -> ComponentStyle:
    if intensity not in (1, 2):
        raise ValueError("Local correction intensity must be 1 or 2")
    return replace(
        style,
        blur_sigma=style.blur_sigma + 4.0 * intensity,
        contrast=style.contrast * (1.0 - 0.04 * intensity),
        motif_strength=style.motif_strength * (1.0 - 0.12 * intensity),
    )


def _view_name(path: Path) -> str:
    return path.stem.rsplit("_", 1)[-1]
