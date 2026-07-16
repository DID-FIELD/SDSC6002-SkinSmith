from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.asset_spec import AssetSpec  # noqa: E402
from skinsmith.evaluation import evaluate_candidate  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer, load_obj  # noqa: E402
from skinsmith.selection import (  # noqa: E402
    Constraint,
    Objective,
    constraint_first_pareto_select,
    weighted_rank,
)
from skinsmith.uv_asset import asset_uv_seam_error, build_uv_seam_pairs  # noqa: E402
from skinsmith.uv_compositor import apply_uv_edge_safety  # noqa: E402


def main() -> None:
    route_config = json.loads(
        (PROJECT_ROOT / "config" / "route_b.json").read_text(encoding="utf-8")
    )
    widths = tuple(int(value) for value in route_config["edge_sweep"]["widths"])
    asset_seam_maximum = float(
        route_config["edge_sweep"]["asset_seam_error_maximum"]
    )
    minimum_multiview_retention = float(
        route_config["edge_sweep"]["minimum_multiview_retention"]
    )
    spec = AssetSpec.load(PROJECT_ROOT / "config" / "assets" / "ak47_cs2.json", PROJECT_ROOT)
    spec.verify_mesh()
    source_path = (
        PROJECT_ROOT
        / "runs"
        / "route_b_composition_smoke"
        / "route_b_before_asset_seam.png"
    )
    mask_dir = PROJECT_ROOT / "runs" / "route_b_asset_prep"
    if not source_path.exists() or not mask_dir.exists():
        raise SystemExit("Run Route-B asset preparation and composition smoke first")
    region_names = [region.name for region in spec.semantic_regions] + [spec.default_region.name]
    masks = {
        name: Image.open(mask_dir / f"mask_{name}.png").convert("L") for name in region_names
    }
    source = Image.open(source_path).convert("RGB")
    base_color = tuple(int(value) for value in route_config["base_color"])
    mesh = load_obj(spec.mesh_path)
    seam_pairs = build_uv_seam_pairs(mesh)
    renderer = ObjMultiViewRenderer(spec.mesh_path)
    output_dir = PROJECT_ROOT / "runs" / "route_b_edge_sweep"
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    decision_metrics: dict[str, dict[str, float]] = {}
    for width in widths:
        candidate_id = f"width_{width:02d}"
        candidate_dir = output_dir / candidate_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        corrected, edge_map = apply_uv_edge_safety(
            source,
            masks,
            base_color=base_color,
            edge_safe_pixels=width,
        )
        texture_path = candidate_dir / "texture.png"
        corrected.save(texture_path)
        edge_map.save(candidate_dir / "edge_safety_map.png")
        previews = renderer.render(corrected, candidate_dir, candidate_id)
        asset_seam = asset_uv_seam_error(corrected, mesh, seam_pairs)
        score = evaluate_candidate(candidate_id, corrected, previews)
        metrics = {
            "asset_seam_error": float(asset_seam["total_error"]),
            "multi_view_score": float(score.multi_view.total_score),
            "texture_score": float(score.texture_score),
        }
        decision_metrics[candidate_id] = metrics
        records.append(
            {
                "candidate_id": candidate_id,
                "edge_safe_pixels": width,
                **metrics,
                "asset_seam_color_error": float(asset_seam["color_error"]),
                "asset_seam_gradient_error": float(asset_seam["gradient_error"]),
                "mean_view_detail": sum(
                    view.detail_score for view in score.multi_view.views
                )
                / len(score.multi_view.views),
                "mean_view_luminance": sum(
                    view.mean_luminance for view in score.multi_view.views
                )
                / len(score.multi_view.views),
            }
        )

    raw_multiview = decision_metrics["width_00"]["multi_view_score"]
    minimum_multiview = raw_multiview * minimum_multiview_retention
    constraints = (
        Constraint("asset_seam_error", maximum=asset_seam_maximum),
        Constraint("multi_view_score", minimum=minimum_multiview),
    )
    objectives = tuple(
        Objective(str(item["metric"]), maximize=bool(item["maximize"]))
        for item in route_config["pareto_objectives_in_fixed_priority"]
    )
    decision = constraint_first_pareto_select(decision_metrics, constraints, objectives)
    objective_directions = {objective.metric: objective.maximize for objective in objectives}
    weighted_objectives = {
        Objective(metric, maximize=objective_directions[metric]): float(weight)
        for metric, weight in route_config["weighted_baseline"].items()
    }
    weighted = weighted_rank(
        decision_metrics,
        weighted_objectives,
    )
    weighted_selected = weighted[0][0]
    selected_dir = output_dir / decision.selected_id
    selected_image = Image.open(selected_dir / "texture.png").convert("RGB")
    selected_image.save(output_dir / "selected_constraint_pareto.png")
    selected_image.save(
        output_dir / "selected_constraint_pareto__route-b__custom-paint-job.tga"
    )

    with (output_dir / "edge_sweep.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    log = {
        "stage": "route_b_edge_safety_sweep",
        "status": "selected_operating_point",
        "asset_spec": spec.to_log_dict(),
        "fixed_candidate": str(source_path),
        "route_b_config": str(PROJECT_ROOT / "config" / "route_b.json"),
        "widths": list(widths),
        "hard_constraints": {
            "asset_seam_error_maximum": asset_seam_maximum,
            "minimum_multiview_retention": minimum_multiview_retention,
            "raw_multiview_score": raw_multiview,
            "minimum_multiview_score": minimum_multiview,
        },
        "objectives_in_fixed_priority": [
            {"metric": objective.metric, "maximize": objective.maximize}
            for objective in objectives
        ],
        "records": records,
        "constraint_pareto_decision": decision.to_dict(),
        "weighted_baseline": {
            "weights": route_config["weighted_baseline"],
            "ranking": [{"candidate_id": key, "score": value} for key, value in weighted],
            "selected_id": weighted_selected,
            "selected_is_hard_constraint_feasible": weighted_selected in decision.feasible_ids,
        },
    }
    (output_dir / "edge_sweep_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "records": records,
        "hard_constraints": log["hard_constraints"],
        "constraint_pareto": decision.to_dict(),
        "weighted_selected": weighted_selected,
        "output_dir": str(output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()
