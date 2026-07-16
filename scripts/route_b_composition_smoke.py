from __future__ import annotations

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
from skinsmith.generator import ProceduralTextureGenerator  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer, load_obj  # noqa: E402
from skinsmith.spec import DesignSpec  # noqa: E402
from skinsmith.uv_asset import asset_uv_seam_error, build_uv_seam_pairs  # noqa: E402
from skinsmith.uv_compositor import ComponentStyle, UVComposer  # noqa: E402


def main() -> None:
    route_config = json.loads(
        (PROJECT_ROOT / "config" / "route_b.json").read_text(encoding="utf-8")
    )
    asset_spec = AssetSpec.load(
        PROJECT_ROOT / "config" / "assets" / "ak47_cs2.json", PROJECT_ROOT
    )
    asset_spec.verify_mesh()
    mask_dir = PROJECT_ROOT / "runs" / "route_b_asset_prep"
    if not mask_dir.exists():
        raise SystemExit("Run scripts/prepare_ak47_route_b.py first")

    themes = json.loads((PROJECT_ROOT / "config" / "themes.json").read_text(encoding="utf-8"))
    theme_name = str(route_config["source_theme"])
    theme = themes[theme_name]
    design = DesignSpec(
        theme_name=theme_name,
        description=theme["description"],
        palette=tuple(theme["palette"]),
        motif=theme["motif"],
        size=int(route_config["source_size"]),
        candidate_count=1,
        seed=20260714,
    )
    source = ProceduralTextureGenerator().generate(design, design.seed)
    region_names = [region.name for region in asset_spec.semantic_regions]
    if asset_spec.default_region.name not in region_names:
        region_names.append(asset_spec.default_region.name)
    masks = {
        name: Image.open(mask_dir / f"mask_{name}.png").convert("L") for name in region_names
    }
    styles = {
        name: ComponentStyle.from_dict(values)
        for name, values in route_config["component_styles"].items()
    }
    base_color = tuple(int(value) for value in route_config["base_color"])
    composer = UVComposer(
        styles,
        base_color=base_color,
        transition_sigma=float(route_config["transition_sigma"]),
        edge_safe_pixels=float(route_config["selected_edge_safe_pixels"]),
    )
    composition = composer.compose(source, masks)

    output_dir = PROJECT_ROOT / "runs" / "route_b_composition_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    source.save(output_dir / "source_generic_texture.png")
    before_path = output_dir / "route_b_before_asset_seam.png"
    after_path = output_dir / "route_b_after_asset_seam.png"
    composition.before_asset_seam_correction.save(before_path)
    composition.after_asset_seam_correction.save(after_path)
    composition.after_asset_seam_correction.save(
        output_dir / "route_b_after_asset_seam__route-b__custom-paint-job.tga"
    )
    composition.edge_safety_map.save(output_dir / "edge_safety_map.png")

    renderer = ObjMultiViewRenderer(asset_spec.mesh_path)
    before_previews = renderer.render(
        composition.before_asset_seam_correction, output_dir, "route_b_before"
    )
    after_previews = renderer.render(
        composition.after_asset_seam_correction, output_dir, "route_b_after"
    )
    mesh = load_obj(asset_spec.mesh_path)
    seam_pairs = build_uv_seam_pairs(mesh)
    before_asset_seam = asset_uv_seam_error(
        composition.before_asset_seam_correction, mesh, seam_pairs
    )
    after_asset_seam = asset_uv_seam_error(
        composition.after_asset_seam_correction, mesh, seam_pairs
    )
    before_score = evaluate_candidate(
        "route_b_before", composition.before_asset_seam_correction, before_previews
    )
    after_score = evaluate_candidate(
        "route_b_after", composition.after_asset_seam_correction, after_previews
    )
    before_total = float(before_asset_seam["total_error"])
    after_total = float(after_asset_seam["total_error"])
    log = {
        "stage": "route_b_component_composition_smoke",
        "status": "technical_path_test_not_final_art",
        "asset_spec": asset_spec.to_log_dict(),
        "design_spec": design.to_dict(),
        "composition": {
            "base_color": list(base_color),
            "route_b_config": str(PROJECT_ROOT / "config" / "route_b.json"),
            "transition_sigma": route_config["transition_sigma"],
            "edge_safe_pixels": route_config["selected_edge_safe_pixels"],
            "styles": {name: style.__dict__ for name, style in styles.items()},
        },
        "before_asset_seam": before_asset_seam,
        "after_asset_seam": after_asset_seam,
        "asset_seam_absolute_improvement": before_total - after_total,
        "asset_seam_relative_improvement": (before_total - after_total) / max(before_total, 1e-8),
        "before_score": before_score.to_dict(),
        "after_score": after_score.to_dict(),
        "outputs": sorted(path.name for path in output_dir.iterdir() if path.is_file()),
    }
    (output_dir / "composition_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "before_asset_seam": before_asset_seam,
        "after_asset_seam": after_asset_seam,
        "relative_improvement": log["asset_seam_relative_improvement"],
        "before_multiview": before_score.multi_view.total_score,
        "after_multiview": after_score.multi_view.total_score,
        "output_dir": str(output_dir),
    }, indent=2))
if __name__ == "__main__":
    main()
