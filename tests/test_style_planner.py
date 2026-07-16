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

from skinsmith.style_planner import (  # noqa: E402
    REQUIRED_COMPONENTS,
    StyleCompiler,
    StyleLibrary,
    StylePack,
    StylePlanner,
)


class StylePlannerTests(unittest.TestCase):
    def test_all_style_packs_load_and_offer_alternatives(self) -> None:
        for path in sorted((PROJECT_ROOT / "config" / "styles").glob("*.json")):
            pack = StylePack.load(path)
            self.assertGreaterEqual(len(pack.candidate_directions), 3)
            self.assertEqual(set(pack.component_roles), set(REQUIRED_COMPONENTS))

    def test_porcelain_plan_shares_style_but_changes_route_logic(self) -> None:
        path = PROJECT_ROOT / "config" / "styles" / "blue_white_porcelain.json"
        plan = StylePlanner(StylePack.load(path)).plan(
            "Design an elegant but contemporary blue-and-white porcelain AK-47", 3
        )
        self.assertEqual(len(plan.candidates), 3)
        self.assertEqual(plan.palette[0], "#F3F0E5")
        self.assertIn("seamless", plan.candidates[0].route_a_prompt.lower())
        self.assertIn("receiver", plan.candidates[0].route_b_prompt.lower())
        self.assertNotEqual(plan.candidates[0].concept, plan.candidates[1].concept)
        self.assertEqual(plan.candidates[0].component_roles["receiver"], plan.candidates[1].component_roles["receiver"])

    def test_library_resolves_porcelain_from_brief(self) -> None:
        library = StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
        pack = library.resolve("I want an elegant blue-and-white porcelain weapon skin")
        self.assertEqual(pack.style_id, "blue_white_porcelain_v1")

    def test_library_rejects_unknown_style_instead_of_guessing(self) -> None:
        library = StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
        with self.assertRaisesRegex(ValueError, "no style pack matches"):
            library.resolve("a completely unknown style with no knowledge pack")

    def test_route_a_adapter_preserves_planned_prompt(self) -> None:
        path = PROJECT_ROOT / "config" / "styles" / "blue_white_porcelain.json"
        plan = StylePlanner(StylePack.load(path)).plan("blue-and-white porcelain theme", 1)
        spec = plan.route_a_design_spec()
        self.assertEqual(spec.description, plan.candidates[0].generator_brief)
        self.assertEqual(spec.palette, plan.palette)
        self.assertEqual(spec.motif, "waves")
        self.assertIn("peony", spec.prompt_motif)
        self.assertIn("blue-and-white porcelain", spec.description)

    def test_rejects_pack_without_component_roles(self) -> None:
        path = PROJECT_ROOT / "config" / "styles" / "blue_white_porcelain.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["component_roles"]["receiver"]
        with tempfile.TemporaryDirectory() as directory:
            bad_path = Path(directory) / "bad.json"
            bad_path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "receiver"):
                StylePack.load(bad_path)

    def test_dynamic_style_compiler_generates_theme_specific_style(self) -> None:
        library = StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
        generated = json.loads(
            (
                PROJECT_ROOT / "config" / "styles" / "retro_futurist_neon.json"
            ).read_text(encoding="utf-8")
        )
        generated.update(
            {
                "style_id": "geological_luxury_material_v1",
                "display_name": "Geological Luxury Material",
                "generation_label": "dark marble and warm gold mineral material art",
                "match_terms": ["marble", "gold vein", "geological material"],
                "summary": "A stone-led material system built from tectonic fractures and restrained gold mineral seams.",
                "visual_vocabulary": [
                    "deep charcoal marble fields",
                    "large geological fault planes",
                    "warm gold mineral seams",
                ],
                "motifs": ["tectonic fracture", "marble plane", "gold seam"],
                "material_cues": [
                    "matte polished stone",
                    "metallic mineral inlay without baked highlights",
                ],
            }
        )
        theme_palette = ["#111214", "#2B2C30", "#B88A44", "#E4C786"]
        asset_context = {
            "components": [{"component": name} for name in REQUIRED_COMPONENTS]
        }

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "compiled_style.json"
            result = StyleCompiler(
                library,
                lambda brief, theme, asset: generated,
                backend_id="fake:style",
            ).compile(
                "dark marble with warm gold veins",
                {"palette": theme_palette},
                asset_context,
                force_generate=True,
                output_path=output,
            )

            self.assertEqual(result.source_mode, "generated")
            self.assertEqual(result.style.style_id, "geological_luxury_material_v1")
            self.assertIn("stone", result.style.summary)
            self.assertEqual(list(result.style.palette), theme_palette)
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
