from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.asset_spec import AssetSpec  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer, load_obj  # noqa: E402
from skinsmith.uv_asset import (  # noqa: E402
    render_semantic_uv_assets,
    render_topology_component_atlas,
    semantic_assignment_statistics,
    semantic_face_labels,
    summarize_uv_asset,
    topology_component_statistics,
)


def main() -> None:
    spec_path = PROJECT_ROOT / "config" / "assets" / "ak47_cs2.json"
    spec = AssetSpec.load(spec_path, PROJECT_ROOT)
    verified_hash = spec.verify_mesh()
    mesh = load_obj(spec.mesh_path)
    face_labels, regions = semantic_face_labels(mesh, spec.semantic_regions, spec.default_region)
    assets = render_semantic_uv_assets(mesh, face_labels, regions, spec.texture_size)

    output_dir = PROJECT_ROOT / "runs" / "route_b_asset_prep"
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, image in assets.items():
        image.save(output_dir / f"{name}.png")

    component_atlas, component_colors = render_topology_component_atlas(
        mesh, spec.texture_size
    )
    component_atlas.save(output_dir / "topology_component_calibration.png")
    _make_legend(
        [(f"component_{index:02d}", color) for index, color in enumerate(component_colors)],
        output_dir / "topology_component_legend.png",
        columns=4,
    )
    _make_legend(
        [(region.name, region.color) for region in regions],
        output_dir / "semantic_legend.png",
        columns=2,
    )

    renderer = ObjMultiViewRenderer(spec.mesh_path)
    renderer.render(assets["semantic_atlas"], output_dir, "semantic_calibration")
    renderer.render(component_atlas, output_dir, "topology_component_calibration")

    mask_stack = np.stack(
        [np.asarray(assets[f"mask_{region.name}"]) > 127 for region in regions]
    )
    semantic_coverage = {
        "assigned_face_count": int(len(face_labels)),
        "assigned_face_fraction": 1.0,
        "uv_union_pixel_count": int(np.count_nonzero(mask_stack.any(axis=0))),
        "uv_union_pixel_fraction": float(np.count_nonzero(mask_stack.any(axis=0)))
        / mask_stack.shape[1]
        / mask_stack.shape[2],
        "uv_multi_label_pixel_count": int(np.count_nonzero(mask_stack.sum(axis=0) > 1)),
        "uv_multi_label_pixel_fraction": float(np.count_nonzero(mask_stack.sum(axis=0) > 1))
        / mask_stack.shape[1]
        / mask_stack.shape[2],
        "maximum_pixel_label_count": int(mask_stack.sum(axis=0).max()),
    }

    log = {
        "stage": "route_b_asset_preparation",
        "purpose": "Bind one asset version and derive reproducible semantic UV masks.",
        "asset_spec": spec.to_log_dict(),
        "verified_mesh_sha256": verified_hash,
        "uv_asset": summarize_uv_asset(mesh, spec.mesh_path),
        "semantic_assignments": semantic_assignment_statistics(face_labels, regions, assets),
        "semantic_coverage": semantic_coverage,
        "topology_components": topology_component_statistics(mesh),
        "outputs": sorted(path.name for path in output_dir.glob("*.png")),
        "manual_status": "pending visual inspection of semantic component boundaries",
    }
    (output_dir / "asset_prep_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "asset_id": spec.asset_id,
        "mesh_sha256": verified_hash,
        "semantic_assignments": log["semantic_assignments"],
        "output_dir": str(output_dir),
    }, indent=2, ensure_ascii=False))


def _make_legend(
    entries: list[tuple[str, tuple[int, int, int]]],
    path: Path,
    columns: int,
) -> None:
    cell_width = 240
    cell_height = 38
    rows = (len(entries) + columns - 1) // columns
    image = Image.new("RGB", (cell_width * columns, 24 + cell_height * rows), "#151719")
    draw = ImageDraw.Draw(image)
    for index, (label, color) in enumerate(entries):
        column = index % columns
        row = index // columns
        x = column * cell_width + 12
        y = row * cell_height + 16
        draw.rectangle((x, y, x + 24, y + 24), fill=color)
        draw.text((x + 34, y + 5), label, fill="#F2F4F7")
    image.save(path)


if __name__ == "__main__":
    main()
