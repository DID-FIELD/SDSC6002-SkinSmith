from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.obj_renderer import ObjMesh  # noqa: E402
from skinsmith.asset_spec import AssetSpec, SemanticRegionSpec  # noqa: E402
from skinsmith.route_b_composition import (  # noqa: E402
    compile_weapon_design_plan,
    extract_removable_background,
    load_generated_role_images,
)
from skinsmith.weapon_space import (  # noqa: E402
    CanonicalWeaponFrame,
    UVGeometryMaps,
    WeaponSpaceLayerSpec,
    bake_uv_geometry_maps,
    bake_weapon_space_texture,
    compose_weapon_space_layers,
)
from skinsmith.uv_region_composition import compose_groups_in_uv_regions  # noqa: E402


class WeaponSpaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mesh = ObjMesh(
            vertices=np.asarray([(0, 0, 0), (0, 0, 1), (0, 1, 0)], dtype=np.float32),
            texcoords=np.asarray([(0.1, 0.1), (0.9, 0.1), (0.1, 0.9)], dtype=np.float32),
            vertex_faces=np.asarray([(0, 1, 2)], dtype=np.int32),
            texture_faces=np.asarray([(0, 1, 2)], dtype=np.int32),
        )

    def test_generated_role_background_extraction_removes_rectangular_field(self) -> None:
        image = Image.new("RGB", (128, 128), (14, 15, 16))
        draw = ImageDraw.Draw(image)
        draw.ellipse((38, 34, 92, 96), fill=(190, 145, 55))
        extracted = extract_removable_background(image)
        alpha = np.asarray(extracted.getchannel("A"), dtype=np.uint8)
        self.assertLess(int(alpha[:8, :8].max()), 16)
        self.assertGreater(int(alpha[64, 64]), 200)

    def test_canonical_frame_maps_longitudinal_and_up_axes(self) -> None:
        frame = CanonicalWeaponFrame.from_mesh(self.mesh, (0, 0, 1), (0, 1, 0))
        coordinates = frame.normalized_coordinates(self.mesh.vertices)
        self.assertEqual(coordinates[1, 0], 1.0)
        self.assertEqual(coordinates[2, 1], 1.0)

    def test_explicit_group_is_hard_clipped_to_mesh_derived_uv_region(self) -> None:
        frame = CanonicalWeaponFrame.from_mesh(self.mesh, (0, 0, 1), (0, 1, 0))
        maps = bake_uv_geometry_maps(self.mesh, frame, 64)
        spec = AssetSpec(
            asset_id="test",
            display_name="test",
            game="test",
            mesh_path=Path("test.obj"),
            mesh_sha256="0" * 64,
            mesh_version="test",
            uv_source="mesh",
            uv_address_mode="clamp",
            uv_sheet_path=None,
            uv_sheet_sha256=None,
            texture_size=64,
            export_format="png",
            camera_views=("left",),
            semantic_regions=(
                SemanticRegionSpec("part", (255, 0, 0)),
            ),
            default_region=SemanticRegionSpec("other", (0, 0, 0)),
            source_path=Path("test.json"),
        )
        bundle = {
            "weapon_theme": {
                "composition_graph": {
                    "strategy": "background",
                    "groups": [
                        {
                            "group_id": "field",
                            "composition_mode": "background",
                            "semantic_role": "background",
                            "components": ["part"],
                            "surfaces": ["left", "right", "top"],
                            "mirror_on_right": True,
                        }
                    ],
                }
            }
        }
        source = Image.new("RGBA", (16, 16), (220, 80, 20, 255))
        with tempfile.TemporaryDirectory() as directory:
            result = compose_groups_in_uv_regions(
                bundle,
                self.mesh,
                maps,
                spec,
                {"field": source},
                base_color=(5, 6, 7),
                diagnostic_dir=Path(directory),
            )
            self.assertTrue((Path(directory) / "uv_group_mask_field.png").is_file())
        array = np.asarray(result)
        self.assertTrue(np.all(array[~maps.valid_mask] == (5, 6, 7)))
        self.assertGreater(int(array[maps.valid_mask, 0].mean()), 100)

    def test_uv_baker_interpolates_position_and_canvases(self) -> None:
        frame = CanonicalWeaponFrame.from_mesh(self.mesh, (0, 0, 1), (0, 1, 0))
        maps = bake_uv_geometry_maps(self.mesh, frame, size=64)
        self.assertGreater(np.count_nonzero(maps.valid_mask), 0)
        self.assertEqual(maps.statistics()["maximum_coverage_count"], 1)
        left = Image.new("RGB", (64, 32), (10, 20, 30))
        right = Image.new("RGB", (64, 32), (40, 50, 60))
        top = Image.new("RGB", (64, 32), (70, 80, 90))
        texture = bake_weapon_space_texture(
            maps, {"left": left, "right": right, "top": top}, (1, 2, 3)
        )
        pixels = np.asarray(texture)
        self.assertTrue(np.any(np.all(pixels == (10, 20, 30), axis=2)))
        self.assertEqual(tuple(pixels[0, 0]), (1, 2, 3))

    def test_uv_baker_wraps_official_repeat_coordinates(self) -> None:
        shifted_mesh = ObjMesh(
            vertices=self.mesh.vertices,
            texcoords=self.mesh.texcoords + np.asarray((1.0, -2.0), dtype=np.float32),
            vertex_faces=self.mesh.vertex_faces,
            texture_faces=self.mesh.texture_faces,
        )
        frame = CanonicalWeaponFrame.from_mesh(
            shifted_mesh, (0, 0, 1), (0, 1, 0)
        )
        baseline = bake_uv_geometry_maps(self.mesh, frame, size=64)
        repeated = bake_uv_geometry_maps(
            shifted_mesh, frame, size=64, uv_address_mode="repeat"
        )

        np.testing.assert_array_equal(repeated.valid_mask, baseline.valid_mask)
        np.testing.assert_allclose(
            repeated.canonical_position,
            baseline.canonical_position,
            atol=1e-6,
        )

    def test_projection_blends_side_and_top_by_surface_normal(self) -> None:
        shape = (8, 8)
        position = np.zeros((*shape, 3), dtype=np.float32)
        position[..., 2] = 0.25
        normal = np.zeros((*shape, 3), dtype=np.float32)
        normal[..., 1] = np.sqrt(0.5)
        normal[..., 2] = -np.sqrt(0.5)
        maps = UVGeometryMaps(
            canonical_position=position,
            canonical_normal=normal,
            valid_mask=np.ones(shape, dtype=bool),
            face_index=np.zeros(shape, dtype=np.int32),
            coverage_count=np.ones(shape, dtype=np.uint16),
        )
        texture = bake_weapon_space_texture(
            maps,
            {
                "left": Image.new("RGB", (8, 8), (255, 0, 0)),
                "right": Image.new("RGB", (8, 8), (0, 255, 0)),
                "top": Image.new("RGB", (8, 8), (0, 0, 255)),
            },
            (0, 0, 0),
            projection_blend_power=2.0,
        )
        self.assertEqual(tuple(np.asarray(texture)[4, 4]), (128, 0, 128))

    def test_generated_content_is_placed_on_weapon_space_canvas(self) -> None:
        canvases = {
            surface: Image.new("RGB", (40, 20), (0, 0, 0))
            for surface in ("left", "right", "top")
        }
        layer = WeaponSpaceLayerSpec.from_dict(
            {
                "layer_id": "hero",
                "surfaces": ["left"],
                "center": [0.5, 0.5],
                "size": [0.5, 0.5],
                "opacity": 1.0,
                "blend_mode": "normal",
                "fit_mode": "stretch",
            }
        )
        result = compose_weapon_space_layers(
            canvases,
            (layer,),
            {"hero": Image.new("RGBA", (8, 8), (255, 0, 0, 255))},
        )
        left = np.asarray(result["left"])
        self.assertEqual(tuple(left[10, 20]), (255, 0, 0))
        self.assertEqual(tuple(left[0, 0]), (0, 0, 0))
        self.assertEqual(tuple(np.asarray(result["right"])[10, 20]), (0, 0, 0))

    def test_content_layer_can_select_normalized_source_crop(self) -> None:
        source = np.zeros((8, 8, 4), dtype=np.uint8)
        source[:, :4] = (255, 0, 0, 255)
        source[:, 4:] = (0, 255, 0, 255)
        layer = WeaponSpaceLayerSpec.from_dict(
            {
                "layer_id": "cropped",
                "surfaces": ["left"],
                "size": [1.0, 1.0],
                "fit_mode": "stretch",
                "source_crop": [0.5, 0.0, 1.0, 1.0],
            }
        )
        canvases = {
            surface: Image.new("RGB", (16, 8), (0, 0, 0))
            for surface in ("left", "right", "top")
        }
        result = compose_weapon_space_layers(
            canvases, (layer,), {"cropped": Image.fromarray(source, mode="RGBA")}
        )
        self.assertEqual(tuple(np.asarray(result["left"])[4, 8]), (0, 255, 0))

    def test_route_bundle_compiles_semantic_generated_asset_layers(self) -> None:
        centers = {
            "stock": [0.14, 0.31],
            "receiver": [0.45, 0.20],
            "magazine": [0.50, 0.56],
            "pistol_grip": [0.43, 0.47],
            "handguard": [0.72, 0.11],
            "front_assembly": [0.82, 0.16],
            "barrel_muzzle": [0.94, 0.20],
        }
        bundle = {
            "weapon_theme": {
                "theme_id": "test_theme",
                "palette": ["#0A0A0A", "#D4AF37", "#4A4A4A", "#FDF4DC"],
                "component_layout": [
                    {"component": name, "canvas_center": center}
                    for name, center in centers.items()
                ],
            }
        }
        plan = compile_weapon_design_plan(bundle)
        layers = {layer.layer_id: layer for layer in plan.content_layers}
        self.assertEqual(plan.focal_center, (0.45, 0.8))
        self.assertAlmostEqual(plan.flow_center, (0.31 + 0.20 + 0.11) / 3.0)
        self.assertEqual(layers["background_all"].blend_mode, "normal")
        self.assertEqual(layers["background_all"].opacity, 1.0)
        self.assertEqual(layers["hero_receiver"].surfaces, ("left", "right"))
        self.assertEqual(layers["hero_receiver"].center, (0.45, 0.20))
        self.assertAlmostEqual(layers["secondary_magazine"].center[0], 0.5)
        self.assertAlmostEqual(layers["secondary_magazine"].center[1], 0.56)
        self.assertIn("connector_top", layers)

    def test_generated_role_images_expand_to_all_consuming_layers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, role in enumerate(
                ("hero", "secondary", "connector", "background"), start=1
            ):
                Image.new("RGB", (8, 8), (index, 0, 0)).save(
                    root / f"route_b_{role}.png"
                )
            images, provenance = load_generated_role_images(root)
        self.assertEqual(len(images), 7)
        self.assertEqual(provenance["hero_receiver"]["semantic_role"], "hero")
        self.assertEqual(
            provenance["secondary_stock"]["sha256"],
            provenance["secondary_magazine"]["sha256"],
        )

    def test_master_artwork_binds_one_image_to_complete_weapon_canvases(self) -> None:
        centers = {
            "stock": [0.14, 0.31],
            "receiver": [0.45, 0.20],
            "magazine": [0.50, 0.56],
            "pistol_grip": [0.43, 0.47],
            "handguard": [0.72, 0.11],
            "front_assembly": [0.82, 0.16],
            "barrel_muzzle": [0.94, 0.20],
        }
        bundle = {
            "weapon_theme": {
                "theme_id": "master",
                "palette": ["#101519", "#B98A42", "#315B61", "#D9C9A2"],
                "focal_component": "receiver",
                "component_layout": [
                    {"component": name, "canvas_center": center}
                    for name, center in centers.items()
                ],
                "composition_graph": {
                    "strategy": "master_artwork",
                    "groups": [],
                },
            }
        }
        plan = compile_weapon_design_plan(bundle)
        layers = {layer.layer_id: layer for layer in plan.content_layers}
        self.assertEqual(set(layers), {"master_artwork__side", "master_artwork__top"})
        self.assertEqual(layers["master_artwork__side"].surfaces, ("left", "right"))
        self.assertEqual(layers["master_artwork__side"].fit_mode, "cover")
        self.assertEqual(plan.quiet_strength, 0.0)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (32, 32), (50, 80, 110)).save(
                root / "route_b_master_artwork.png"
            )
            images, provenance = load_generated_role_images(root, bundle)
        self.assertEqual(set(images), set(layers))
        self.assertEqual(
            provenance["master_artwork__side"]["semantic_role"],
            "master_artwork",
        )

    def test_composition_graph_compiles_spanning_and_independent_layers(self) -> None:
        centers = {
            "stock": [0.14, 0.31],
            "receiver": [0.45, 0.20],
            "magazine": [0.50, 0.56],
            "pistol_grip": [0.43, 0.47],
            "handguard": [0.72, 0.11],
            "front_assembly": [0.82, 0.16],
            "barrel_muzzle": [0.94, 0.20],
        }
        layout = [
            {
                "component": name,
                "canvas_center": center,
                "prominence": 0.8 if name != "receiver" else 1.0,
                "detail_density": 0.6,
            }
            for name, center in centers.items()
        ]
        groups = [
            {
                "group_id": "field",
                "composition_mode": "background",
                "semantic_role": "background",
                "components": list(centers),
                "surfaces": ["left", "right", "top"],
                "mirror_on_right": True,
                "allow_muzzle_focus": False,
            },
            {
                "group_id": "dragon_body",
                "composition_mode": "spanning",
                "semantic_role": "hero",
                "components": ["stock", "receiver", "handguard"],
                "surfaces": ["left", "right", "top"],
                "mirror_on_right": True,
                "allow_muzzle_focus": False,
            },
            {
                "group_id": "dragon_head",
                "composition_mode": "spanning",
                "semantic_role": "hero",
                "components": ["front_assembly", "barrel_muzzle"],
                "surfaces": ["left", "right"],
                "mirror_on_right": True,
                "allow_muzzle_focus": True,
            },
            {
                "group_id": "claw",
                "composition_mode": "independent",
                "semantic_role": "secondary",
                "components": ["magazine"],
                "surfaces": ["left", "right"],
                "mirror_on_right": True,
                "allow_muzzle_focus": False,
            },
        ]
        bundle = {
            "weapon_theme": {
                "theme_id": "dragon",
                "palette": ["#101519", "#B98A42", "#315B61", "#D9C9A2"],
                "focal_component": "receiver",
                "component_layout": layout,
                "composition_graph": {"strategy": "hybrid", "groups": groups},
            }
        }
        plan = compile_weapon_design_plan(bundle)
        layers = {layer.layer_id: layer for layer in plan.content_layers}
        self.assertGreater(layers["dragon_body__side"].size[0], 0.8)
        self.assertIn("dragon_body__top", layers)
        self.assertEqual(
            layers["claw__magazine__side"].center,
            tuple(centers["magazine"]),
        )
        self.assertEqual(plan.quiet_strength, 0.0)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, group in enumerate(groups, start=1):
                Image.new("RGB", (16, 16), (index * 20, 0, 0)).save(
                    root / f"route_b_{group['group_id']}.png"
                )
            images, provenance = load_generated_role_images(root, bundle)
        self.assertEqual(set(images), set(layers))
        self.assertEqual(
            provenance["dragon_body__side"]["composition_group_id"],
            "dragon_body",
        )


if __name__ == "__main__":
    unittest.main()
