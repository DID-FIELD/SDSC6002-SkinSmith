from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.design_routes import (  # noqa: E402
    AssetCreativeProfile,
    RecordedAgentThemeBackend,
    RouteDesignPlanner,
    ThemeCompiler,
    ThemeLibrary,
    ThemePack,
)
from skinsmith.style_planner import REQUIRED_COMPONENTS, StylePack  # noqa: E402


def _bundle():
    theme = ThemePack.load(PROJECT_ROOT / "config" / "design_themes" / "wild_lotus.json")
    style = StylePack.load(PROJECT_ROOT / "config" / "styles" / "modern_chinese_botanical.json")
    data = json.loads(
        (PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json").read_text(
            encoding="utf-8"
        )
    )
    anchors = {key: tuple(value) for key, value in data["component_anchors"].items()}
    return RouteDesignPlanner(anchors).plan(
        "Design an AK-47 skin called Wild Lotus", theme, style
    )


def _dragon_bundle():
    theme = ThemePack.load(
        PROJECT_ROOT / "config" / "design_themes" / "celestial_dragon.json"
    )
    style = StylePack.load(
        PROJECT_ROOT / "config" / "styles" / "modern_chinese_botanical.json"
    )
    profile = AssetCreativeProfile.load(
        PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
    )
    return RouteDesignPlanner(
        profile.component_anchors,
        route_b_strategy="composition_graph",
    ).plan(
        "dragon body across stock receiver and handguard, clawed magazine, muzzle head",
        theme,
        style,
    )


class DesignRouteTests(unittest.TestCase):
    def test_asset_creative_profile_exposes_weapon_structure(self) -> None:
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        self.assertIn("assault rifle", profile.weapon_type)
        self.assertEqual(profile.component_functions["receiver"], "largest primary focal canvas")
        self.assertEqual(len(profile.compiler_context()["components"]), 7)

    def test_theme_library_resolves_wild_lotus(self) -> None:
        library = ThemeLibrary.load_directory(PROJECT_ROOT / "config" / "design_themes")
        self.assertEqual(
            library.resolve("Design a Wild Lotus skin").theme_id,
            "wild_lotus_v1",
        )

    def test_route_a_designs_the_square_pattern(self) -> None:
        plan = _bundle().pattern
        self.assertEqual(plan.design_object, "tileable_template_pattern")
        self.assertIn("dense", plan.density_strategy)
        self.assertIn("no single irreplaceable focal subject", plan.constraints)
        self.assertIn("three_by_three_tile_preview", plan.required_outputs)

    def test_route_b_defaults_to_one_dense_master_artwork(self) -> None:
        plan = _bundle().weapon_theme
        self.assertEqual(plan.design_object, "weapon_space_theme_composition")
        self.assertEqual(plan.focal_component, "receiver")
        self.assertEqual(plan.composition_graph.strategy, "master_artwork")
        self.assertEqual(len(plan.asset_briefs), 1)
        self.assertEqual(plan.asset_briefs[0].semantic_role, "master_artwork")
        self.assertIn("dense master artwork", plan.source_square_semantics)
        self.assertIn("UV-atlas storage", plan.final_square_semantics)
        self.assertEqual({item.component for item in plan.component_layout}, set(REQUIRED_COMPONENTS))
        self.assertTrue(all(item.source_canvas == (1536, 864) for item in plan.asset_briefs))
        self.assertIn("final_square_uv_atlas", plan.required_outputs)
        self.assertIn("ak47_left_preview", plan.required_outputs)

    def test_a_b_share_theme_but_not_generation_logic(self) -> None:
        bundle = _bundle()
        self.assertEqual(bundle.pattern.theme_id, bundle.weapon_theme.theme_id)
        self.assertEqual(bundle.pattern.palette, bundle.weapon_theme.palette)
        self.assertIn("seamless template pattern", bundle.pattern.generation_prompt)
        self.assertNotIn("seamless pattern", bundle.weapon_theme.composition_prompt)
        self.assertIn("arbitrary cropping", bundle.weapon_theme.composition_prompt)
        self.assertEqual(bundle.refinement.base_route, "B")

    def test_receiver_is_most_prominent_and_muzzle_is_quiet(self) -> None:
        placements = {item.component: item for item in _bundle().weapon_theme.component_layout}
        self.assertEqual(placements["receiver"].prominence, 1.0)
        self.assertLess(placements["barrel_muzzle"].detail_density, 0.1)

    def test_dragon_theme_compiles_explicit_component_relationship_graph(self) -> None:
        plan = _dragon_bundle().weapon_theme
        groups = {
            group.group_id: group for group in plan.composition_graph.groups
        }
        self.assertEqual(plan.composition_graph.strategy, "hybrid")
        self.assertEqual(
            groups["dragon_body_run"].components,
            ("stock", "receiver", "handguard"),
        )
        self.assertEqual(groups["dragon_body_run"].composition_mode, "spanning")
        self.assertEqual(groups["magazine_claw"].components, ("magazine",))
        self.assertEqual(groups["magazine_claw"].composition_mode, "independent")
        self.assertTrue(groups["dragon_head_coil"].allow_muzzle_focus)
        self.assertEqual(
            {brief.composition_group_id for brief in plan.asset_briefs},
            set(groups),
        )
        self.assertIn("one continuous subject", plan.composition_prompt)

    def test_unknown_theme_is_generated_and_validated_for_target_weapon(self) -> None:
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        library = ThemeLibrary.load_directory(PROJECT_ROOT / "config" / "design_themes")

        def backend(brief: str, asset: AssetCreativeProfile) -> dict:
            stories = {}
            for component, function in asset.component_functions.items():
                if component == "receiver":
                    element_ids, prominence, density = ["mountain_hero"], 1.0, 0.8
                elif component in {"stock", "handguard"}:
                    element_ids, prominence, density = ["river_connector", "mist_background"], 0.5, 0.4
                else:
                    element_ids, prominence, density = ["mist_background"], 0.2, 0.2
                stories[component] = {
                    "narrative_role": f"adapt landscape composition to {function}",
                    "element_ids": element_ids,
                    "prominence": prominence,
                    "detail_density": density,
                }
            return {
                "theme_id": "generated_landscape_v1",
                "display_name": "Landscape Painting",
                "generation_label": "original mountain-and-water landscape",
                "match_terms": ["landscape painting", "landscape"],
                "concept": "An original mountain-and-water theme compiled from the user brief.",
                "narrative": "A mountain focal scene flows into river and mist across the weapon silhouette.",
                "default_style_id": "modern_chinese_botanical_v1",
                "palette": ["#10211F", "#49665D", "#D8D2BE"],
                "elements": [
                    {"element_id": "mountain_hero", "display_name": "Main Mountain", "semantic_role": "hero", "generation_description": "one readable mountain silhouette"},
                    {"element_id": "river_connector", "display_name": "River Flow", "semantic_role": "connector", "generation_description": "a river path connecting weapon regions"},
                    {"element_id": "mist_background", "display_name": "Cloud Mist", "semantic_role": "background", "generation_description": "broad mist and negative space"}
                ],
                "pattern_notes": ["repeat multiple mountain, river, and mist elements without one unique focal scene"],
                "component_story": stories,
                "evaluation_criteria": ["landscape readability", "weapon-level flow", "quiet muzzle"],
                "reference_policy": "Create original scenery and do not copy one painting or living artist."
            }

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "compiled_theme.json"
            result = ThemeCompiler(library, backend, backend_id="fake-creative-backend").compile(
                "Create an original landscape-painting theme from scratch",
                profile,
                output_path=output,
            )
            self.assertEqual(result.source_mode, "generated")
            self.assertEqual(result.backend_id, "fake-creative-backend")
            self.assertEqual(set(result.theme.target_components), set(profile.component_anchors))
            self.assertTrue(output.exists())

    def test_unknown_theme_requires_a_real_creative_backend(self) -> None:
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        library = ThemeLibrary.load_directory(PROJECT_ROOT / "config" / "design_themes")
        with self.assertRaisesRegex(ValueError, "creative synthesis backend"):
            ThemeCompiler(library).compile("a completely new theme", profile)

    def test_recorded_agent_backend_is_bound_to_brief_and_asset(self) -> None:
        path = (
            PROJECT_ROOT
            / "runs"
            / "theme_compilation_chip_circuit"
            / "recorded_agent_theme.json"
        )
        backend = RecordedAgentThemeBackend(path)
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        recorded_brief = str(backend.record["recorded_brief"])
        theme = backend(recorded_brief, profile)
        self.assertEqual(theme["theme_id"], "silicon_pulse_v1")
        with self.assertRaisesRegex(ValueError, "brief does not match"):
            backend("use a different prompt", profile)


if __name__ == "__main__":
    unittest.main()
