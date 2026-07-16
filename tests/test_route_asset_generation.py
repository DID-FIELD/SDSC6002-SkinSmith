from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.design_routes import (  # noqa: E402
    AssetCreativeProfile,
    RouteDesignPlanner,
    ThemePack,
)
from skinsmith.route_asset_generation import plan_route_image_jobs  # noqa: E402
from skinsmith.style_planner import StylePack  # noqa: E402


class RouteAssetGenerationTests(unittest.TestCase):
    def test_nano_banana_smoke_plan_has_one_a_and_four_semantic_b_jobs(self) -> None:
        bundle = json.loads(
            (
                PROJECT_ROOT
                / "runs"
                / "theme_compilation_chip_circuit"
                / "route_design_bundle.json"
            ).read_text(encoding="utf-8")
        )
        jobs = plan_route_image_jobs(bundle, route="all", route_a_candidates=1)
        self.assertEqual(len(jobs), 5)
        self.assertEqual(jobs[0].route, "A")
        self.assertEqual(
            {job.semantic_role for job in jobs if job.route == "B"},
            {"hero", "secondary", "connector", "background"},
        )
        self.assertTrue(all("no weapon" in job.prompt.casefold() for job in jobs))

    def test_b_source_contract_forbids_mockups_and_separates_roles(self) -> None:
        bundle = json.loads(
            (
                PROJECT_ROOT
                / "runs"
                / "theme_compilation_chip_circuit"
                / "route_design_bundle.json"
            ).read_text(encoding="utf-8")
        )
        jobs = {
            job.semantic_role: job
            for job in plan_route_image_jobs(bundle, route="b")
        }
        for job in jobs.values():
            lowered = job.prompt.casefold()
            self.assertIn("placement metadata only", lowered)
            self.assertIn("do not depict", lowered)
            self.assertIn("weapon mockup", lowered)
            self.assertIn("rectangular material sample", lowered)
        self.assertIn("one isolated", jobs["hero"].prompt)
        self.assertIn("no coherent backing slab", jobs["hero"].prompt)
        self.assertIn("ROLE PRIORITY OVERRIDES", jobs["secondary"].prompt)
        self.assertIn("bright accent colours", jobs["background"].prompt)
        self.assertIn("branching, elongated connector", jobs["connector"].prompt)
        self.assertIn("edge-to-edge, low-contrast", jobs["background"].prompt)

    def test_candidate_direction_is_locked_into_distinct_a_and_b_jobs(self) -> None:
        bundle = json.loads(
            (
                PROJECT_ROOT
                / "runs"
                / "theme_compilation_chip_circuit"
                / "route_design_bundle.json"
            ).read_text(encoding="utf-8")
        )
        direction = {
            "direction_id": "ordered_signal",
            "title": "Ordered Signal",
            "concept": "Layered parallel signal paths with one controlled focal node.",
            "motifs": ["parallel traces", "single node"],
            "route_a_emphasis": "Rhythmic repeated paths.",
            "route_b_emphasis": "Paths follow the weapon length toward the receiver node.",
        }
        jobs = plan_route_image_jobs(
            bundle,
            route="all",
            route_a_candidates=1,
            candidate_direction=direction,
        )
        self.assertEqual(len(jobs), 5)
        self.assertTrue(all(job.job_id.endswith("__ordered_signal") for job in jobs))
        self.assertTrue(all("Locked candidate art direction" in job.prompt for job in jobs))
        self.assertIn("Rhythmic repeated paths", jobs[0].prompt)
        self.assertTrue(
            all(
                "Paths follow the weapon length" in job.prompt
                for job in jobs
                if job.route == "B"
            )
        )
        self.assertEqual(
            {job.output_name for job in jobs if job.route == "B"},
            {
                "route_b_hero.png",
                "route_b_secondary.png",
                "route_b_connector.png",
                "route_b_background.png",
            },
        )

    def test_composition_graph_creates_one_named_job_per_art_group(self) -> None:
        theme = ThemePack.load(
            PROJECT_ROOT / "config" / "design_themes" / "celestial_dragon.json"
        )
        style = StylePack.load(
            PROJECT_ROOT / "config" / "styles" / "modern_chinese_botanical.json"
        )
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        bundle = RouteDesignPlanner(
            profile.component_anchors,
            route_b_strategy="composition_graph",
        ).plan(
            "dragon body across the weapon with a clawed magazine and muzzle head",
            theme,
            style,
        ).to_dict()
        jobs = plan_route_image_jobs(bundle, route="b")
        self.assertEqual(len(jobs), 5)
        self.assertEqual(
            {job.output_name for job in jobs},
            {
                "route_b_lacquer_field.png",
                "route_b_dragon_body_run.png",
                "route_b_dragon_head_coil.png",
                "route_b_magazine_claw.png",
                "route_b_cloud_flow.png",
            },
        )
        body = next(job for job in jobs if job.composition_group_id == "dragon_body_run")
        self.assertIn("continuous elongated subject", body.prompt)
        self.assertEqual(body.semantic_role, "hero")
        self.assertEqual(body.composition_mode, "spanning")
        self.assertEqual(
            body.target_components,
            ("stock", "receiver", "handguard"),
        )

    def test_old_graph_bundle_recovers_scope_metadata_from_composition_graph(self) -> None:
        theme = ThemePack.load(
            PROJECT_ROOT / "config" / "design_themes" / "celestial_dragon.json"
        )
        style = StylePack.load(
            PROJECT_ROOT / "config" / "styles" / "modern_chinese_botanical.json"
        )
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        bundle = RouteDesignPlanner(
            profile.component_anchors,
            route_b_strategy="composition_graph",
        ).plan(
            "dragon body across the weapon with a clawed magazine and muzzle head",
            theme,
            style,
        ).to_dict()
        for brief in bundle["weapon_theme"]["asset_briefs"]:
            brief.pop("composition_mode", None)
            brief.pop("target_components", None)

        jobs = plan_route_image_jobs(bundle, route="b")

        body = next(job for job in jobs if job.composition_group_id == "dragon_body_run")
        self.assertEqual(body.composition_mode, "spanning")
        self.assertEqual(
            body.target_components,
            ("stock", "receiver", "handguard"),
        )

    def test_default_route_b_creates_one_master_artwork_job(self) -> None:
        theme = ThemePack.load(
            PROJECT_ROOT / "config" / "design_themes" / "celestial_dragon.json"
        )
        style = StylePack.load(
            PROJECT_ROOT / "config" / "styles" / "modern_chinese_botanical.json"
        )
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        bundle = RouteDesignPlanner(profile.component_anchors).plan(
            "dense original dragon and cloud artwork",
            theme,
            style,
        ).to_dict()
        jobs = plan_route_image_jobs(bundle, route="b")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].semantic_role, "master_artwork")
        self.assertEqual(jobs[0].output_name, "route_b_master_artwork.png")
        self.assertIn("high-density", jobs[0].prompt)
        self.assertIn("Subject-part placement is not evaluated", jobs[0].prompt)


if __name__ == "__main__":
    unittest.main()
