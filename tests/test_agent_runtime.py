from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.agent_runtime import (  # noqa: E402
    AgentBudget,
    AgentMemory,
    AgentPhase,
    ArtworkCandidate,
    ArtDirectionCandidate,
    SkinSmithAgent,
    ToolRegistry,
    directions_from_style_plan,
)
from skinsmith.agent_tools import CreativePlanningTool  # noqa: E402
from skinsmith.design_routes import (  # noqa: E402
    AssetCreativeProfile,
    ThemeCompiler,
    ThemeLibrary,
)
from skinsmith.style_planner import StylePack, StylePlanner  # noqa: E402
from skinsmith.style_planner import StyleCompiler, StyleLibrary  # noqa: E402


def _directions(count: int) -> tuple[ArtDirectionCandidate, ...]:
    return tuple(
        ArtDirectionCandidate(
            direction_id=f"direction_{index}",
            title=f"Direction {index}",
            concept=f"Distinct concept {index}",
            style_family="Material",
            palette=("#111111", "#D4AF37"),
            materials=("stone", "metal inlay"),
            hero_strategy=f"receiver hero {index}",
            secondary_strategy="stock and magazine support",
            connector_strategy="handguard carries the flow",
            background_strategy="quiet dark field",
            route_a_logic=f"crop-tolerant pattern logic {index}",
            route_b_logic=f"whole-weapon composition logic {index}",
            quiet_regions=("barrel_muzzle",),
            risks=("hero may cross a UV edge",),
            recommendation_reason=f"clear hierarchy option {index}",
        )
        for index in range(1, count + 1)
    )


class AgentRuntimeTests(unittest.TestCase):
    def test_theme_direction_and_artwork_are_three_separate_checkpoints(self) -> None:
        tools = ToolRegistry()
        tools.register(
            "expand_theme",
            lambda context, request: {
                "keyword": request.brief,
                "theme_id": "dragon_world",
                "display_name": "Dragon World",
                "concept": "Dragons expanded into a complete visual world.",
                "palette": ["#101519", "#B98A42", "#315B61"],
                "elements": [
                    {"label": "dragon", "semantic_role": "hero"},
                    {"label": "clouds", "semantic_role": "connector"},
                    {"label": "jade", "semantic_role": "secondary"},
                ],
                "theme_path": "theme.json",
            },
        )

        def plan(context, payload):
            self.assertEqual(payload["theme_expansion"]["theme_id"], "dragon_world")
            return _directions(payload["request"].candidate_budget)

        tools.register("plan_directions", plan)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            theme = SkinSmithAgent(PROJECT_ROOT, tools).run(
                "dragon",
                "ak47",
                candidate_budget=3,
                output_dir=output,
            )
            self.assertEqual(theme.status, "awaiting_theme")
            self.assertEqual(theme.phase, AgentPhase.AWAITING_THEME)
            self.assertEqual(theme.theme_expansion["theme_id"], "dragon_world")
            self.assertEqual(theme.directions, ())

            directions = SkinSmithAgent(PROJECT_ROOT, tools).resume(
                output,
                theme_confirmed=True,
            )
            self.assertEqual(directions.status, "awaiting_direction")
            self.assertEqual(len(directions.directions), 3)

    def test_direction_then_mapped_artwork_selection_are_separate_checkpoints(self) -> None:
        planning_tools = ToolRegistry()
        planning_tools.register(
            "plan_directions",
            lambda context, request: _directions(request.candidate_budget),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            first = SkinSmithAgent(PROJECT_ROOT, planning_tools).run(
                "rich dragon world",
                "ak47",
                candidate_budget=3,
                output_dir=output,
            )
            self.assertEqual(first.status, "awaiting_direction")

            execution_tools = ToolRegistry()

            def generate(context, contract):
                return tuple(
                    ArtworkCandidate(
                        candidate_id=f"artwork_{index:02d}",
                        title=f"Artwork {index}",
                        variation=f"variation {index}",
                        source_path=f"source_{index}.png",
                        prompt=f"prompt {index}",
                        preview_paths=(
                            f"left_{index}.png",
                            f"right_{index}.png",
                            f"top_{index}.png",
                        ),
                        validation={"passed": True},
                        metrics={"multi_view_score": 0.5 + index / 10},
                    )
                    for index in range(1, 4)
                )

            execution_tools.register("generate_artwork_candidates", generate)
            execution_tools.register(
                "execute_design",
                lambda context, payload: {
                    "artifacts": {
                        "selected": payload["artwork_candidate"].candidate_id
                    }
                },
            )
            awaiting_artwork = SkinSmithAgent(
                PROJECT_ROOT,
                execution_tools,
            ).resume(output, "direction_2")
            self.assertEqual(awaiting_artwork.status, "awaiting_artwork")
            self.assertEqual(
                awaiting_artwork.phase,
                AgentPhase.AWAITING_ARTWORK,
            )
            self.assertEqual(len(awaiting_artwork.artwork_candidates), 3)

            completed = SkinSmithAgent(PROJECT_ROOT, execution_tools).resume(
                output,
                artwork_choice="artwork_03",
            )
            self.assertEqual(completed.status, "completed")
            self.assertEqual(completed.selected_artwork_id, "artwork_03")
            self.assertEqual(completed.artifacts["selected"], "artwork_03")

    def test_run_plans_directions_and_waits_without_faking_execution(self) -> None:
        tools = ToolRegistry()
        tools.register(
            "plan_directions",
            lambda context, request: _directions(request.candidate_budget),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            result = SkinSmithAgent(PROJECT_ROOT, tools).run(
                "dark geological skin with warm mineral seams",
                "ak47_workbench_official",
                "Material",
                4,
                output_dir=output,
            )
            self.assertEqual(result.status, "awaiting_direction")
            self.assertEqual(result.phase, AgentPhase.AWAITING_DIRECTION)
            self.assertEqual(len(result.directions), 4)
            self.assertIsNone(result.design_contract)
            self.assertTrue((output / "directions.json").is_file())
            self.assertTrue((output / "checkpoint.json").is_file())
            self.assertTrue((output / "events.jsonl").is_file())

    def test_selected_direction_locks_contract_and_stops_if_executor_is_missing(self) -> None:
        tools = ToolRegistry()
        tools.register("plan_directions", lambda context, request: _directions(3))
        with tempfile.TemporaryDirectory() as directory:
            result = SkinSmithAgent(PROJECT_ROOT, tools).run(
                "original storm glass weapon skin",
                "ak47_workbench_official",
                "Organic",
                3,
                "direction_2",
                output_dir=Path(directory) / "run",
            )
            self.assertEqual(result.status, "ready_to_execute")
            self.assertEqual(result.phase, AgentPhase.READY_TO_EXECUTE)
            self.assertEqual(
                result.design_contract.selected_direction.direction_id,
                "direction_2",
            )

    def test_awaiting_run_resumes_from_checkpoint_with_selected_direction(self) -> None:
        planning_tools = ToolRegistry()
        planning_tools.register(
            "plan_directions",
            lambda context, request: _directions(3),
        )
        execution_tools = ToolRegistry()
        execution_tools.register(
            "execute_design",
            lambda context, contract: {
                "artifacts": {"selected": contract.selected_direction.direction_id}
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            first = SkinSmithAgent(PROJECT_ROOT, planning_tools).run(
                "original storm glass weapon skin",
                "ak47_workbench_official",
                candidate_budget=3,
                output_dir=output,
            )
            self.assertEqual(first.status, "awaiting_direction")

            resumed = SkinSmithAgent(PROJECT_ROOT, execution_tools).resume(
                output,
                "direction_3",
            )
            self.assertEqual(resumed.status, "completed")
            self.assertEqual(resumed.artifacts["selected"], "direction_3")
            self.assertGreater(len(resumed.events), len(first.events))

    def test_registered_executor_receives_budgeted_context(self) -> None:
        tools = ToolRegistry()
        tools.register("plan_directions", lambda context, request: _directions(3))

        def execute(context, contract):
            context.consume_image_call(2)
            context.consume_role_retry()
            context.consume_refinement_round()
            return {
                "artifacts": {"texture_png": "final.png"},
                "metrics": {"score": 0.8},
                "decision": {"selected_route": "B"},
            }

        tools.register("execute_design", execute)
        with tempfile.TemporaryDirectory() as directory:
            agent = SkinSmithAgent(PROJECT_ROOT, tools)
            result = agent.run(
                "original storm glass weapon skin",
                "ak47_workbench_official",
                candidate_budget=3,
                direction_choice="direction_1",
                budget=AgentBudget(
                    max_image_calls=2,
                    max_role_retries=1,
                    max_refinement_rounds=1,
                ),
                output_dir=Path(directory) / "run",
            )
            self.assertEqual(result.status, "completed")
            self.assertEqual(result.artifacts["texture_png"], "final.png")
            self.assertEqual(agent.state.image_calls_used, 2)
            self.assertEqual(agent.state.role_retries_used, 1)
            self.assertEqual(agent.state.refinement_rounds_used, 1)

    def test_completed_run_can_reopen_for_evidence_backed_role_revision(self) -> None:
        planning_tools = ToolRegistry()
        planning_tools.register("plan_directions", lambda context, request: _directions(3))
        planning_tools.register(
            "execute_design",
            lambda context, contract: {
                "artifacts": {"texture_png": "round_0.png"},
                "metrics": {"score": 0.7},
                "decision": {"selected_route": "B"},
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            completed = SkinSmithAgent(PROJECT_ROOT, planning_tools).run(
                "revision test",
                "ak47",
                candidate_budget=3,
                direction_choice="direction_1",
                output_dir=output,
            )
            self.assertEqual(completed.status, "completed")

            revision_tools = ToolRegistry()

            def retry_roles(context, payload):
                self.assertEqual(payload["roles"], ("connector", "background"))
                self.assertIn("connector", payload["review_reasons"])
                return {
                    "artifacts": {"texture_png": "revised.png"},
                    "metrics": {"score": 0.8},
                    "decision": {"selected_route": "B"},
                }

            revision_tools.register("retry_roles", retry_roles)
            revised = SkinSmithAgent(PROJECT_ROOT, revision_tools).revise(
                output,
                ("connector", "background"),
                review_reasons={"connector": "complete object drift"},
                additional_image_calls=1,
                reuse_latest_roles=("background",),
            )
            self.assertEqual(revised.status, "completed")
            self.assertEqual(revised.artifacts["texture_png"], "revised.png")
            self.assertGreater(len(revised.events), len(completed.events))
            self.assertEqual(
                revised.request.budget.max_image_calls,
                completed.request.budget.max_image_calls + 1,
            )

    def test_budget_prevents_unbounded_image_calls(self) -> None:
        tools = ToolRegistry()
        tools.register("plan_directions", lambda context, request: _directions(3))

        def execute(context, contract):
            context.consume_image_call(3)
            return {}

        tools.register("execute_design", execute)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "image-call budget exceeded"):
                SkinSmithAgent(PROJECT_ROOT, tools).run(
                    "brief",
                    "ak47",
                    candidate_budget=3,
                    direction_choice="direction_1",
                    budget=AgentBudget(max_image_calls=2),
                    output_dir=Path(directory) / "run",
                )

    def test_memory_requires_evidence_and_round_trips(self) -> None:
        memory = AgentMemory()
        memory.remember(
            "ak47.uv_orientation",
            "known-good official Workbench orientation",
            ["CODEX_CONTEXT.md#known-correct-uv-calibration"],
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            memory.save(path)
            loaded = AgentMemory.load(path)
            self.assertEqual(
                loaded.facts["ak47.uv_orientation"].value,
                "known-good official Workbench orientation",
            )

    def test_existing_style_plan_adapts_to_rich_agent_directions(self) -> None:
        style = StylePack.load(
            PROJECT_ROOT / "config" / "styles" / "blue_white_porcelain.json"
        )
        plan = StylePlanner(style).plan("original porcelain weapon skin", 3)
        candidates = directions_from_style_plan(
            style,
            plan,
            style_family="Traditional Art",
        )
        self.assertEqual(len(candidates), 3)
        self.assertEqual(candidates[0].style_family, "Traditional Art")
        self.assertIn("master artwork", candidates[0].route_b_logic.lower())
        self.assertIn("subject-part placement", candidates[0].route_b_logic.lower())
        self.assertEqual(candidates[0].quiet_regions, ())

    def test_style_adapter_can_preserve_optional_composition_graph_logic(self) -> None:
        style = StylePack.load(
            PROJECT_ROOT / "config" / "styles" / "blue_white_porcelain.json"
        )
        plan = StylePlanner(style).plan("original porcelain weapon skin", 1)
        candidates = directions_from_style_plan(
            style,
            plan,
            route_b_strategy="composition_graph",
        )
        self.assertIn("receiver", candidates[0].route_b_logic.lower())
        self.assertEqual(candidates[0].quiet_regions, ("barrel_muzzle",))
        self.assertEqual(candidates[0].route_b_logic, plan.candidates[0].route_b_prompt)

    def test_real_planning_tool_uses_validated_theme_style_chain(self) -> None:
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        tool = CreativePlanningTool(
            profile,
            ThemeCompiler(
                ThemeLibrary.load_directory(
                    PROJECT_ROOT / "config" / "design_themes"
                )
            ),
            StyleCompiler(
                StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
            ),
            supported_asset_ids=("cs2_ak47_new_geometry",),
        )
        tools = ToolRegistry()
        tools.register("plan_directions", tool)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            result = SkinSmithAgent(PROJECT_ROOT, tools).run(
                "Design an AK-47 skin called Wild Lotus",
                "cs2_ak47_new_geometry",
                candidate_budget=3,
                output_dir=output,
            )
            self.assertEqual(result.status, "awaiting_direction")
            self.assertEqual(len(result.directions), 3)
            self.assertTrue(
                (output / "planning" / "planning_manifest.json").is_file()
            )
            self.assertTrue((output / "memory_snapshot.json").is_file())


if __name__ == "__main__":
    unittest.main()
