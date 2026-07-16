from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.asset_spec import AssetSpec  # noqa: E402
from skinsmith.component_feedback import (  # noqa: E402
    diagnose_component_detail,
    make_detail_reduction_style,
    measure_component_views,
    render_component_visibility,
)
from skinsmith.evaluation import evaluate_candidate  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer, load_obj  # noqa: E402
from skinsmith.refinement import decide_refinement  # noqa: E402
from skinsmith.selection import (  # noqa: E402
    Constraint,
    Objective,
    constraint_first_pareto_select,
)
from skinsmith.uv_asset import asset_uv_seam_error, build_uv_seam_pairs  # noqa: E402
from skinsmith.uv_compositor import ComponentStyle, UVComposer  # noqa: E402


def main() -> None:
    route_config = json.loads(
        (PROJECT_ROOT / "config" / "route_b.json").read_text(encoding="utf-8")
    )
    refinement_config = route_config["route_c_local_refinement"]
    asset_spec = AssetSpec.load(PROJECT_ROOT / route_config["asset_spec"], PROJECT_ROOT)
    asset_spec.verify_mesh()
    source_dir = PROJECT_ROOT / "runs" / "route_b_composition_smoke"
    mask_dir = PROJECT_ROOT / "runs" / "route_b_asset_prep"
    output_dir = PROJECT_ROOT / "runs" / "route_c_local_refinement"
    output_dir.mkdir(parents=True, exist_ok=True)

    source = Image.open(source_dir / "source_generic_texture.png").convert("RGB")
    round_0_texture = Image.open(source_dir / "route_b_after_asset_seam.png").convert("RGB")
    round_0_previews = [
        source_dir / f"route_b_after_{view}.png" for view in asset_spec.camera_views
    ] + [source_dir / "route_b_after_multiview.png"]
    region_names = [region.name for region in asset_spec.semantic_regions] + [
        asset_spec.default_region.name
    ]
    masks = {
        name: Image.open(mask_dir / f"mask_{name}.png").convert("L") for name in region_names
    }
    styles = {
        name: ComponentStyle.from_dict(values)
        for name, values in route_config["component_styles"].items()
    }
    detail_targets = {
        name: float(value) for name, value in refinement_config["detail_targets"].items()
    }
    renderer = ObjMultiViewRenderer(asset_spec.mesh_path)
    visibility = render_component_visibility(
        renderer,
        {name: masks[name] for name in detail_targets},
        output_dir / "visibility",
    )
    round_0_per_view, round_0_components, round_0_balance = measure_component_views(
        round_0_previews, visibility, detail_targets
    )
    diagnosis = diagnose_component_detail(round_0_components)
    if diagnosis.target_component is None:
        raise RuntimeError(f"No local correction target was diagnosed: {diagnosis.reason}")

    mesh = load_obj(asset_spec.mesh_path)
    seam_pairs = build_uv_seam_pairs(mesh)
    round_0_standard = evaluate_candidate("round_0_route_b", round_0_texture, round_0_previews)
    round_0_seam = asset_uv_seam_error(round_0_texture, mesh, seam_pairs)
    score_weights = refinement_config["agent_score_weights"]
    round_0_agent_score = _agent_score(
        round_0_standard.texture_score,
        round_0_standard.multi_view.total_score,
        round_0_balance,
        score_weights,
    )

    candidates: list[dict] = []
    decision_metrics: dict[str, dict[str, float]] = {}
    composer_parameters = {
        "base_color": tuple(int(value) for value in route_config["base_color"]),
        "transition_sigma": float(route_config["transition_sigma"]),
        "edge_safe_pixels": float(route_config["selected_edge_safe_pixels"]),
    }
    for candidate_index, intensity in enumerate(
        refinement_config["candidate_intensities"], start=1
    ):
        candidate_id = f"round_1_candidate_{candidate_index:02d}"
        candidate_dir = output_dir / candidate_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        corrected_styles = dict(styles)
        corrected_styles[diagnosis.target_component] = make_detail_reduction_style(
            styles[diagnosis.target_component], int(intensity)
        )
        composition = UVComposer(corrected_styles, **composer_parameters).compose(source, masks)
        texture = composition.after_asset_seam_correction
        texture_path = candidate_dir / "texture.png"
        texture.save(texture_path)
        previews = renderer.render(texture, candidate_dir, candidate_id)
        per_view, components, balance = measure_component_views(
            previews, visibility, detail_targets
        )
        standard = evaluate_candidate(candidate_id, texture, previews)
        asset_seam = asset_uv_seam_error(texture, mesh, seam_pairs)
        agent_score = _agent_score(
            standard.texture_score,
            standard.multi_view.total_score,
            balance,
            score_weights,
        )
        locality = _locality_metrics(
            round_0_texture,
            texture,
            masks[diagnosis.target_component],
            int(route_config["transition_sigma"]),
        )
        metrics = {
            "asset_seam_error": float(asset_seam["total_error"]),
            "multi_view_score": float(standard.multi_view.total_score),
            "texture_score": float(standard.texture_score),
            "component_detail_balance": float(balance),
            "agent_score": float(agent_score),
        }
        decision_metrics[candidate_id] = metrics
        candidates.append(
            {
                "candidate_id": candidate_id,
                "intensity": int(intensity),
                "action": diagnosis.action,
                "target_component": diagnosis.target_component,
                "style_before": styles[diagnosis.target_component].__dict__,
                "style_after": corrected_styles[diagnosis.target_component].__dict__,
                "metrics": metrics,
                "asset_seam": asset_seam,
                "component_metrics": [record.to_dict() for record in components],
                "component_view_metrics": [record.to_dict() for record in per_view],
                "locality": locality,
                "texture": str(texture_path),
                "previews": [str(path) for path in previews],
            }
        )

    minimum_multiview = (
        round_0_standard.multi_view.total_score
        * float(refinement_config["minimum_multiview_retention"])
    )
    selection = constraint_first_pareto_select(
        decision_metrics,
        (
            Constraint(
                "asset_seam_error",
                maximum=float(refinement_config["asset_seam_error_maximum"]),
            ),
            Constraint("multi_view_score", minimum=minimum_multiview),
        ),
        (
            Objective("agent_score", maximize=True),
            Objective("asset_seam_error", maximize=False),
        ),
    )
    round_1_best = next(
        candidate for candidate in candidates if candidate["candidate_id"] == selection.selected_id
    )
    refinement = decide_refinement(
        round_0_agent_score,
        float(round_1_best["metrics"]["agent_score"]),
        float(refinement_config["minimum_agent_score_improvement"]),
    )
    selected_texture = (
        Image.open(round_1_best["texture"]).convert("RGB")
        if refinement.accepted
        else round_0_texture
    )
    selected_texture.save(output_dir / "selected_texture.png")
    selected_texture.save(
        output_dir / "selected_texture__route-c__custom-paint-job.tga"
    )

    round_0_record = {
        "candidate_id": "round_0_route_b",
        "texture": str(source_dir / "route_b_after_asset_seam.png"),
        "previews": [str(path) for path in round_0_previews],
        "asset_seam": round_0_seam,
        "texture_score": round_0_standard.texture_score,
        "multi_view_score": round_0_standard.multi_view.total_score,
        "component_detail_balance": round_0_balance,
        "agent_score": round_0_agent_score,
        "component_metrics": [record.to_dict() for record in round_0_components],
        "component_view_metrics": [record.to_dict() for record in round_0_per_view],
    }
    log = {
        "stage": "route_c_render_conditioned_local_refinement",
        "status": "accepted_round_1" if refinement.accepted else "rolled_back_to_round_0",
        "asset_spec": asset_spec.to_log_dict(),
        "route_config": str(PROJECT_ROOT / "config" / "route_b.json"),
        "maximum_refinement_rounds": 1,
        "round_1_candidate_count": len(candidates),
        "minimum_improvement": refinement_config["minimum_agent_score_improvement"],
        "component_detail_targets": detail_targets,
        "agent_score_weights": score_weights,
        "diagnosis": diagnosis.to_dict(),
        "round_0": round_0_record,
        "round_1_candidates": candidates,
        "round_1_selection": selection.to_dict(),
        "refinement_decision": refinement.to_dict(),
        "selected": {
            "round": refinement.selected_round,
            "candidate_id": selection.selected_id if refinement.accepted else "round_0_route_b",
            "texture": str(output_dir / "selected_texture.png"),
        },
    }
    (output_dir / "agent_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _write_summary(output_dir / "run_summary.csv", round_0_record, candidates, log["selected"])
    print(json.dumps({
        "diagnosis": diagnosis.to_dict(),
        "round_0_agent_score": round_0_agent_score,
        "round_1_candidates": [
            {"candidate_id": item["candidate_id"], **item["metrics"], "locality": item["locality"]}
            for item in candidates
        ],
        "selection": selection.to_dict(),
        "refinement": refinement.to_dict(),
        "output_dir": str(output_dir),
    }, indent=2))


def _agent_score(
    texture_score: float,
    multi_view_score: float,
    component_balance: float,
    weights: dict,
) -> float:
    return float(
        float(weights["texture_score"]) * texture_score
        + float(weights["multi_view_score"]) * multi_view_score
        + float(weights["component_detail_balance"]) * component_balance
    )


def _locality_metrics(
    before: Image.Image,
    after: Image.Image,
    target_mask: Image.Image,
    transition_pixels: int,
) -> dict[str, float | int]:
    before_array = np.asarray(before.convert("RGB"), dtype=np.int16)
    after_array = np.asarray(after.convert("RGB"), dtype=np.int16)
    changed = np.max(np.abs(before_array - after_array), axis=2) > 1
    mask = np.asarray(target_mask.convert("L"), dtype=np.uint8) > 127
    radius = max(1, transition_pixels * 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    allowed = cv2.dilate(mask.astype(np.uint8), kernel) > 0
    changed_count = int(np.count_nonzero(changed))
    outside_count = int(np.count_nonzero(changed & ~allowed))
    return {
        "changed_pixel_count": changed_count,
        "changed_pixel_fraction": changed_count / changed.size,
        "changed_outside_target_halo_count": outside_count,
        "changed_outside_target_halo_fraction_of_changes": outside_count
        / max(changed_count, 1),
        "target_halo_radius_pixels": radius,
    }


def _write_summary(path: Path, round_0: dict, candidates: list[dict], selected: dict) -> None:
    rows = [
        {
            "round": 0,
            "candidate_id": round_0["candidate_id"],
            "target_component": "",
            "intensity": "",
            "asset_seam_error": round_0["asset_seam"]["total_error"],
            "multi_view_score": round_0["multi_view_score"],
            "texture_score": round_0["texture_score"],
            "component_detail_balance": round_0["component_detail_balance"],
            "agent_score": round_0["agent_score"],
            "selected": selected["candidate_id"] == round_0["candidate_id"],
        }
    ]
    rows.extend(
        {
            "round": 1,
            "candidate_id": candidate["candidate_id"],
            "target_component": candidate["target_component"],
            "intensity": candidate["intensity"],
            "asset_seam_error": candidate["metrics"]["asset_seam_error"],
            "multi_view_score": candidate["metrics"]["multi_view_score"],
            "texture_score": candidate["metrics"]["texture_score"],
            "component_detail_balance": candidate["metrics"]["component_detail_balance"],
            "agent_score": candidate["metrics"]["agent_score"],
            "selected": selected["candidate_id"] == candidate["candidate_id"],
        }
        for candidate in candidates
    )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
