from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skinsmith.evaluation import evaluate_candidate  # noqa: E402
from skinsmith.game_asset_adapter import GameAssetAdapter  # noqa: E402
from skinsmith.uv_asset import asset_uv_seam_error, build_uv_seam_pairs  # noqa: E402
from skinsmith.uv_compositor import (  # noqa: E402
    apply_uv_edge_safety,
    apply_uv_seam_graph_safety,
    apply_uv_seam_pair_averaging,
)


def main() -> None:
    output = ROOT / "runs" / "m4a4_game_asset_adapter_transfer"
    raw = Image.open(output / "uv_baked_raw.png").convert("RGB")
    valid_mask = Image.open(output / "uv_valid_mask.png").convert("L")
    adapter = GameAssetAdapter.load(
        ROOT / "config" / "assets" / "m4a4_cs2.json", ROOT
    )
    adapter.verify()
    mesh = adapter.load_mesh()
    seam_pairs = build_uv_seam_pairs(mesh)
    renderer = adapter.renderer()
    base_color = (10, 10, 10)
    widths = (0.0, 0.5, 1.0, 1.5, 2.0)
    raw_paths = renderer.render(raw, output / "edge_calibration", "width_0")
    raw_score = evaluate_candidate("width_0", raw, raw_paths)
    minimum_view = raw_score.multi_view.total_score * 0.95
    records: list[dict] = []
    selected_image: Image.Image | None = None
    for width in widths:
        if width == 0:
            image = raw
            paths = raw_paths
            score = raw_score
        else:
            image, edge_map = apply_uv_edge_safety(
                raw,
                {"uv_coverage": valid_mask},
                base_color=base_color,
                edge_safe_pixels=width,
            )
            stem = f"width_{str(width).replace('.', '_')}"
            image.save(output / "edge_calibration" / f"{stem}.png")
            edge_map.save(output / "edge_calibration" / f"{stem}_edge_map.png")
            paths = renderer.render(image, output / "edge_calibration", stem)
            score = evaluate_candidate(stem, image, paths)
        seam = asset_uv_seam_error(image, mesh, seam_pairs)
        feasible = (
            seam["total_error"] <= 0.01
            and score.multi_view.total_score >= minimum_view
        )
        records.append(
            {
                "edge_safe_pixels_at_512": width,
                "method": "all_island_edges",
                "equivalent_pixels_at_2048": width * 4,
                "asset_seam_error": seam["total_error"],
                "multi_view_score": score.multi_view.total_score,
                "multi_view_retention": score.multi_view.total_score
                / raw_score.multi_view.total_score,
                "feasible": feasible,
            }
        )
    for width in (1.0, 2.0, 3.0, 4.0):
        image, influence = apply_uv_seam_graph_safety(
            raw,
            mesh,
            seam_pairs,
            base_color=base_color,
            seam_safe_pixels=width,
        )
        stem = f"seam_graph_{str(width).replace('.', '_')}"
        image.save(output / "edge_calibration" / f"{stem}.png")
        influence.save(output / "edge_calibration" / f"{stem}_influence.png")
        paths = renderer.render(image, output / "edge_calibration", stem)
        score = evaluate_candidate(stem, image, paths)
        seam = asset_uv_seam_error(image, mesh, seam_pairs)
        feasible = (
            seam["total_error"] <= 0.01
            and score.multi_view.total_score >= minimum_view
        )
        records.append(
            {
                "edge_safe_pixels_at_512": width,
                "method": "true_seam_graph_only",
                "equivalent_pixels_at_2048": width * 4,
                "asset_seam_error": seam["total_error"],
                "multi_view_score": score.multi_view.total_score,
                "multi_view_retention": score.multi_view.total_score
                / raw_score.multi_view.total_score,
                "feasible": feasible,
            }
        )
    for radius, samples in ((0, 32), (0, 64), (1, 32), (1, 64)):
        image, changed = apply_uv_seam_pair_averaging(
            raw,
            mesh,
            seam_pairs,
            radius_pixels=radius,
            samples_per_edge=samples,
        )
        stem = f"pair_average_r{radius}_s{samples}"
        image.save(output / "edge_calibration" / f"{stem}.png")
        changed.save(output / "edge_calibration" / f"{stem}_changed.png")
        paths = renderer.render(image, output / "edge_calibration", stem)
        score = evaluate_candidate(stem, image, paths)
        seam = asset_uv_seam_error(image, mesh, seam_pairs)
        feasible = (
            seam["total_error"] <= 0.01
            and score.multi_view.total_score >= minimum_view
        )
        records.append(
            {
                "edge_safe_pixels_at_512": radius,
                "method": f"paired_colour_average_{samples}_samples",
                "equivalent_pixels_at_2048": radius * 4,
                "asset_seam_error": seam["total_error"],
                "multi_view_score": score.multi_view.total_score,
                "multi_view_retention": score.multi_view.total_score
                / raw_score.multi_view.total_score,
                "feasible": feasible,
            }
        )
    iterative, _ = apply_uv_seam_pair_averaging(
        raw,
        mesh,
        seam_pairs,
        radius_pixels=0,
        samples_per_edge=64,
    )
    for iterations in range(2, 7):
        iterative, changed = apply_uv_seam_pair_averaging(
            iterative,
            mesh,
            seam_pairs,
            radius_pixels=0,
            samples_per_edge=64,
        )
        stem = f"pair_average_iter_{iterations}"
        iterative.save(output / "edge_calibration" / f"{stem}.png")
        changed.save(output / "edge_calibration" / f"{stem}_changed.png")
        seam = asset_uv_seam_error(iterative, mesh, seam_pairs)
        if seam["total_error"] <= 0.01:
            paths = renderer.render(iterative, output / "edge_calibration", stem)
            score = evaluate_candidate(stem, iterative, paths)
            view_score = score.multi_view.total_score
            retention = view_score / raw_score.multi_view.total_score
        else:
            view_score = None
            retention = None
        records.append(
            {
                "edge_safe_pixels_at_512": 0,
                "method": f"paired_colour_average_iter_{iterations}",
                "equivalent_pixels_at_2048": 0,
                "asset_seam_error": seam["total_error"],
                "multi_view_score": view_score,
                "multi_view_retention": retention,
                "feasible": bool(
                    view_score is not None
                    and view_score >= minimum_view
                ),
            }
        )
    feasible_records = [record for record in records if record["feasible"]]
    selected = (
        max(feasible_records, key=lambda record: record["multi_view_score"])
        if feasible_records
        else None
    )
    if selected is not None:
        width = selected["edge_safe_pixels_at_512"]
        if selected["method"] == "true_seam_graph_only":
            selected_image, _ = apply_uv_seam_graph_safety(
                raw,
                mesh,
                seam_pairs,
                base_color=base_color,
                seam_safe_pixels=width,
            )
        elif selected["method"].startswith("paired_colour_average"):
            selected_image = raw
            if "_iter_" in selected["method"]:
                iterations = int(selected["method"].rsplit("_", 1)[-1])
                for _ in range(iterations):
                    selected_image, _ = apply_uv_seam_pair_averaging(
                        selected_image,
                        mesh,
                        seam_pairs,
                        radius_pixels=0,
                        samples_per_edge=64,
                    )
            else:
                samples = int(selected["method"].split("_")[-2])
                selected_image, _ = apply_uv_seam_pair_averaging(
                    raw,
                    mesh,
                    seam_pairs,
                    radius_pixels=int(width),
                    samples_per_edge=samples,
                )
        else:
            selected_image, _ = apply_uv_edge_safety(
                raw,
                {"uv_coverage": valid_mask},
                base_color=base_color,
                edge_safe_pixels=width,
            )
        selected_image.save(output / "selected_transfer_texture_512.png")
    with (output / "edge_calibration.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    result = {
        "status": "pass" if selected else "no_feasible_width",
        "asset_id": adapter.spec.asset_id,
        "fixed_candidate": "uv_baked_raw.png",
        "thresholds": {
            "asset_seam_error_maximum": 0.01,
            "minimum_multiview_retention": 0.95,
            "raw_multiview_score": raw_score.multi_view.total_score,
            "minimum_multiview_score": minimum_view,
        },
        "records": records,
        "selected": selected,
        "interpretation": (
            "M4A4 requires adapter-specific edge calibration; AK's equivalent "
            "8 px setting is not assumed transferable."
        ),
    }
    (output / "transfer_validation.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
