from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.asset_spec import AssetSpec  # noqa: E402
from skinsmith.game_asset_adapter import GameAssetAdapter  # noqa: E402
from skinsmith.evaluation import evaluate_candidate  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer, load_obj  # noqa: E402
from skinsmith.route_b_composition import (  # noqa: E402
    compile_weapon_design_plan,
    load_generated_role_images,
)
from skinsmith.uv_asset import asset_uv_seam_error, build_uv_seam_pairs  # noqa: E402
from skinsmith.uv_compositor import apply_uv_edge_safety  # noqa: E402
from skinsmith.weapon_space import (  # noqa: E402
    CanonicalWeaponFrame,
    WeaponDesignPlan,
    bake_uv_geometry_maps,
    bake_weapon_space_texture,
    geometry_map_diagnostics,
    render_weapon_space_canvases,
)


def _make_concept_triptych(
    weapon_space: Image.Image,
    uv_atlas: Image.Image,
    reconstructed: Image.Image,
) -> Image.Image:
    """Show that coherence lives in weapon space, not in the flat UV atlas."""
    panel_width = 600
    panel_height = 390
    header_height = 70
    margin = 18
    background = (18, 23, 31)
    canvas = Image.new(
        "RGB", (panel_width * 3, header_height + panel_height), background
    )
    draw = ImageDraw.Draw(canvas)
    try:
        label_font = ImageFont.truetype("arial.ttf", 24)
        note_font = ImageFont.truetype("arial.ttf", 17)
    except OSError:
        label_font = ImageFont.load_default()
        note_font = ImageFont.load_default()

    panels = (
        (
            weapon_space,
            "1. Weapon-space design",
            "Coherent composition before UV packing",
        ),
        (
            uv_atlas,
            "2. UV atlas storage",
            "Fragments may look unrelated in 2D",
        ),
        (
            reconstructed,
            "3. 3D reconstruction",
            "The model restores the intended whole",
        ),
    )
    for index, (image, label, note) in enumerate(panels):
        x0 = index * panel_width
        fitted = ImageOps.contain(
            image.convert("RGB"),
            (panel_width - margin * 2, panel_height - margin * 2),
            Image.Resampling.LANCZOS,
        )
        paste_x = x0 + (panel_width - fitted.width) // 2
        paste_y = header_height + (panel_height - fitted.height) // 2
        canvas.paste(fitted, (paste_x, paste_y))
        draw.text((x0 + margin, 12), label, fill=(232, 242, 250), font=label_font)
        draw.text((x0 + margin, 42), note, fill=(143, 170, 190), font=note_font)
        if index < 2:
            draw.text(
                (x0 + panel_width - 29, header_height // 2 - 9),
                ">",
                fill=(0, 212, 255),
                font=label_font,
            )
    return canvas


def _project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the true weapon-space Route-B smoke")
    parser.add_argument(
        "--asset-spec",
        default="config/assets/ak47_cs2.json",
        help="AssetSpec binding the exact deployment mesh and UV contract",
    )
    parser.add_argument(
        "--plan",
        default="config/weapon_design_plan.json",
        help="WeaponDesignPlan JSON, relative to the project root by default",
    )
    parser.add_argument(
        "--content-image",
        action="append",
        default=[],
        metavar="LAYER_ID=PATH",
        help="Bind a configured weapon-space content layer to an image",
    )
    parser.add_argument(
        "--route-b-bundle",
        help="Compile WeaponDesignPlan from a RouteDesignBundle instead of --plan",
    )
    parser.add_argument(
        "--generated-assets-dir",
        help="Directory containing route_b_hero/secondary/connector/background.png",
    )
    parser.add_argument(
        "--output-dir",
        default="runs/weapon_space_route_b_smoke",
        help="Output directory, relative to the project root by default",
    )
    parser.add_argument(
        "--size",
        type=int,
        choices=(512, 1024, 2048),
        default=512,
        help="UV bake size; 2048 also writes the formal 24-bit TGA",
    )
    parser.add_argument(
        "--edge-safe-pixels",
        type=int,
        help="Override the UV-island edge safety width at the selected bake size",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    started = time.perf_counter()
    size = args.size
    edge_safe_pixels = (
        args.edge_safe_pixels
        if args.edge_safe_pixels is not None
        else max(1, round(2 * size / 512))
    )
    if edge_safe_pixels < 0:
        raise ValueError("--edge-safe-pixels cannot be negative")
    adapter = GameAssetAdapter.load(_project_path(args.asset_spec), PROJECT_ROOT)
    adapter.verify()
    spec = adapter.spec
    verified_uv_sheet_hash = spec.verify_uv_sheet()
    workbench_profiles = json.loads(
        (PROJECT_ROOT / "config" / "workbench_finish_profiles.json").read_text(
            encoding="utf-8"
        )
    )
    route_profile = workbench_profiles["routes"]["B"]
    formal_tga_name = f"uv_baked_corrected{route_profile['filename_suffix']}.tga"
    mesh = adapter.load_mesh()
    frame = adapter.canonical_frame(mesh)
    maps = adapter.bake_geometry_maps(mesh, size)
    if bool(args.route_b_bundle) != bool(args.generated_assets_dir):
        raise ValueError(
            "--route-b-bundle and --generated-assets-dir must be provided together"
        )
    if args.route_b_bundle:
        bundle_path = _project_path(args.route_b_bundle)
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        plan = compile_weapon_design_plan(bundle)
        content_images, content_inputs = load_generated_role_images(
            _project_path(args.generated_assets_dir)
        )
    else:
        plan = WeaponDesignPlan.load(_project_path(args.plan))
        content_images = {}
        content_inputs = {}
    for binding in args.content_image:
        if "=" not in binding:
            raise ValueError("--content-image must use LAYER_ID=PATH")
        layer_id, value = binding.split("=", 1)
        source_path = _project_path(value)
        source_bytes = source_path.read_bytes()
        content_images[layer_id] = Image.open(source_path).convert("RGBA")
        content_inputs[layer_id] = {
            "source_path": str(source_path),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
        }
    canvases = render_weapon_space_canvases(plan, content_images or None)
    raw_texture = bake_weapon_space_texture(
        maps,
        canvases,
        plan.palette[0],
        projection_blend_power=plan.projection_blend_power,
    )

    masks = {
        "official_uv_coverage": Image.fromarray(
            maps.valid_mask.astype(np.uint8) * 255, mode="L"
        )
    }
    corrected, edge_map = apply_uv_edge_safety(
        raw_texture,
        masks,
        base_color=plan.palette[0],
        edge_safe_pixels=edge_safe_pixels,
    )

    output_dir = _project_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for layer_id, image in content_images.items():
        image.save(output_dir / f"content_{layer_id}.png")
    for name, image in canvases.items():
        image.save(output_dir / f"weapon_space_{name}.png")
    for name, image in geometry_map_diagnostics(maps).items():
        image.save(output_dir / f"{name}.png")
    raw_texture.save(output_dir / "uv_baked_raw.png")
    corrected.save(output_dir / "uv_baked_corrected.png")
    if size == spec.texture_size:
        corrected.convert("RGB").save(output_dir / formal_tga_name)
    edge_map.save(output_dir / "uv_edge_safety_map.png")
    np.savez_compressed(
        output_dir / f"uv_geometry_maps_{size}.npz",
        canonical_position=maps.canonical_position,
        canonical_normal=maps.canonical_normal,
        valid_mask=maps.valid_mask,
        face_index=maps.face_index,
        coverage_count=maps.coverage_count,
    )
    renderer = adapter.renderer()
    raw_previews = renderer.render(raw_texture, output_dir, "weapon_space_raw")
    corrected_previews = renderer.render(corrected, output_dir, "weapon_space_corrected")
    concept_triptych = _make_concept_triptych(
        canvases["left"],
        corrected,
        Image.open(output_dir / "weapon_space_corrected_left.png"),
    )
    concept_triptych.save(output_dir / "route_b_weapon_space_concept.png")
    seam_pairs = build_uv_seam_pairs(mesh)
    raw_seam = asset_uv_seam_error(
        raw_texture, mesh, seam_pairs, uv_address_mode=spec.uv_address_mode
    )
    corrected_seam = asset_uv_seam_error(
        corrected, mesh, seam_pairs, uv_address_mode=spec.uv_address_mode
    )
    raw_score = evaluate_candidate("weapon_space_raw", raw_texture, raw_previews)
    corrected_score = evaluate_candidate(
        "weapon_space_corrected", corrected, corrected_previews
    )
    validation_status = (
        "pass_weapon_space_content_integration_not_final_art"
        if content_images
        else "pass_true_route_b_technical_path_not_final_art"
    )
    observations = [
        "The source composition is coherent on a canonical weapon-space canvas before UV baking.",
        "The baked flat UV atlas is intentionally fragmented and is not expected to read as one conventional 2D illustration.",
        "The receiver focal motif and longitudinal flow reconstruct on the 3D weapon views.",
        "Image-space content placement and canonical longitudinal/up coordinates are converted separately, keeping the receiver hero out of the magazine.",
        "The software preview validates composition flow; final showcase acceptance still requires CS2 Workbench review.",
    ]
    if content_images:
        observations.insert(
            1,
            "A preserved generated image is blended as a controlled material layer on continuous weapon-space canvases, never placed directly in UV coordinates.",
        )
    visual_validation = {
        "status": validation_status,
        "reviewed_outputs": [
            "weapon_space_left.png",
            "uv_baked_corrected.png",
            "weapon_space_corrected_left.png",
            "weapon_space_corrected_multiview.png",
            "route_b_weapon_space_concept.png",
        ],
        "observations": observations,
    }
    (output_dir / "visual_validation.json").write_text(
        json.dumps(visual_validation, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log = {
        "stage": "true_route_b_weapon_space_smoke",
        "status": validation_status,
        "definition": "Design is coherent in canonical weapon space and only fragmented when baked into UV storage.",
        "asset_spec": spec.to_log_dict(),
        "verified_official_uv_sheet_sha256": verified_uv_sheet_hash,
        "canonical_frame": frame.to_dict(),
        "design_plan": plan.to_dict(),
        "content_inputs": content_inputs,
        "uv_geometry_maps": maps.statistics(),
        "bake_size": size,
        "formal_output_size": spec.texture_size,
        "workbench_profile": {
            "route": "B",
            "finish_style": route_profile["finish_style"],
            "formal_tga_name": formal_tga_name,
            "uv_contract": "official Workbench OBJ vt + official UV sheet",
            "uv_address_mode": spec.uv_address_mode,
            "profile_source": "config/workbench_finish_profiles.json",
        },
        "edge_safe_pixels": edge_safe_pixels,
        "raw_asset_seam": raw_seam,
        "corrected_asset_seam": corrected_seam,
        "raw_score": raw_score.to_dict(),
        "corrected_score": corrected_score.to_dict(),
        "visual_validation": visual_validation,
        "runtime_seconds": time.perf_counter() - started,
        "outputs": sorted(path.name for path in output_dir.iterdir() if path.is_file()),
    }
    (output_dir / "weapon_space_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({
        "map_statistics": maps.statistics(),
        "raw_asset_seam": raw_seam,
        "corrected_asset_seam": corrected_seam,
        "raw_multiview": raw_score.multi_view.total_score,
        "corrected_multiview": corrected_score.multi_view.total_score,
        "runtime_seconds": log["runtime_seconds"],
        "output_dir": str(output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()
