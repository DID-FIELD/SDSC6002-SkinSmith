from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.uv_asset import (  # noqa: E402
    asset_uv_seam_error,
    build_uv_seam_pairs,
    load_and_summarize,
    render_uv_diagnostics,
)


def main() -> None:
    model_path = PROJECT_ROOT / "third_party" / "valve_geometry" / "weapon_rif_ak47.obj"
    texture_path = (
        PROJECT_ROOT
        / "runs"
        / "diffusion_refinement"
        / "round_0"
        / "candidates"
        / "candidate_02_seamless.png"
    )
    if not model_path.exists():
        raise SystemExit(f"Missing local model: {model_path}")
    if not texture_path.exists():
        raise SystemExit(f"Missing accepted baseline texture: {texture_path}")

    output_dir = PROJECT_ROOT / "runs" / "uv_asset_diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)
    mesh, summary = load_and_summarize(model_path)
    seam_pairs = build_uv_seam_pairs(mesh)
    diagnostics = render_uv_diagnostics(mesh)
    for name, image in diagnostics.items():
        image.save(output_dir / f"{name}.png")

    with Image.open(texture_path) as texture:
        summary["accepted_baseline_texture"] = str(texture_path)
        summary["accepted_baseline_uv_seam"] = asset_uv_seam_error(texture, mesh, seam_pairs)
    summary["diagnostic_outputs"] = {
        name: str(output_dir / f"{name}.png") for name in diagnostics
    }
    (output_dir / "uv_asset_log.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
