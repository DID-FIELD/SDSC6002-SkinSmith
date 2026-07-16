from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.evaluation import evaluate_candidate  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer  # noqa: E402
from skinsmith.preview import TiledPreviewRenderer  # noqa: E402
from skinsmith.seamless import make_seamless, seam_error  # noqa: E402
from skinsmith.uv_asset import (  # noqa: E402
    asset_uv_seam_error,
    build_uv_seam_pairs,
    load_and_summarize,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate one Route-A source through tiling, AK UV mapping, and multiview rendering."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--model",
        type=Path,
        default=PROJECT_ROOT / "third_party" / "valve_geometry" / "weapon_rif_ak47.obj",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "runs" / "route_a_generated_preview",
    )
    args = parser.parse_args()

    source = args.source.resolve()
    model = args.model.resolve()
    if not source.is_file():
        raise SystemExit(f"Missing Route-A source: {source}")
    if not model.is_file():
        raise SystemExit(f"Missing weapon model: {model}")
    args.output.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as opened:
        raw = opened.convert("RGB")
    repaired = make_seamless(raw)
    repaired_path = args.output / "route_a_seamless.png"
    repaired.save(repaired_path)

    tiled = TiledPreviewRenderer()
    raw_tile_paths = tiled.render(raw, args.output, "route_a_raw")
    repaired_tile_paths = tiled.render(repaired, args.output, "route_a_seamless")

    renderer = ObjMultiViewRenderer(model)
    raw_preview_paths = renderer.render(raw, args.output, "route_a_raw_ak47")
    repaired_preview_paths = renderer.render(
        repaired, args.output, "route_a_seamless_ak47"
    )

    mesh, mesh_summary = load_and_summarize(model)
    seam_pairs = build_uv_seam_pairs(mesh)
    raw_score = evaluate_candidate("route_a_raw", raw, raw_preview_paths)
    repaired_score = evaluate_candidate(
        "route_a_seamless", repaired, repaired_preview_paths
    )
    log = {
        "route": "A",
        "acceptance_status": "diagnostic_pending_visual_review",
        "source": str(source),
        "source_sha256": _sha256(source),
        "source_size": list(raw.size),
        "model": str(model),
        "model_sha256": _sha256(model),
        "square_boundary_seam": {
            "raw": seam_error(raw),
            "repaired": seam_error(repaired),
        },
        "asset_uv_seam": {
            "raw": asset_uv_seam_error(raw, mesh, seam_pairs),
            "repaired": asset_uv_seam_error(repaired, mesh, seam_pairs),
        },
        "scores": {
            "raw": raw_score.to_dict(),
            "repaired": repaired_score.to_dict(),
        },
        "mesh_summary": mesh_summary,
        "outputs": {
            "repaired_texture": str(repaired_path),
            "raw_tile_preview": str(raw_tile_paths[0]),
            "repaired_tile_preview": str(repaired_tile_paths[0]),
            "raw_ak47_previews": [str(path) for path in raw_preview_paths],
            "repaired_ak47_previews": [str(path) for path in repaired_preview_paths],
        },
    }
    log_path = args.output / "route_a_preview_log.json"
    log_path.write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "log": str(log_path),
                "raw_square_seam": log["square_boundary_seam"]["raw"],
                "repaired_square_seam": log["square_boundary_seam"]["repaired"],
                "raw_asset_uv_seam": log["asset_uv_seam"]["raw"],
                "repaired_asset_uv_seam": log["asset_uv_seam"]["repaired"],
                "repaired_total_score": repaired_score.total_score,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
