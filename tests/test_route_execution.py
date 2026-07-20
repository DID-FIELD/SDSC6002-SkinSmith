from __future__ import annotations

import math
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.agent_runtime import (  # noqa: E402
    AgentBudget,
    AgentMemory,
    AgentRunRequest,
    AgentState,
    AgentToolContext,
    SkinSmithAgent,
    ToolRegistry,
)
from skinsmith.agent_tools import CreativePlanningTool  # noqa: E402
from skinsmith.design_routes import (  # noqa: E402
    AssetCreativeProfile,
    ThemeCompiler,
    ThemeLibrary,
)
from skinsmith.route_execution import RouteExecutionTool  # noqa: E402
from skinsmith.route_asset_generation import RouteImageJob  # noqa: E402
from skinsmith.source_validation import SourceAssetValidator  # noqa: E402
from skinsmith.style_planner import StyleCompiler, StyleLibrary  # noqa: E402


class SyntheticImageBackend:
    backend_id = "synthetic:test-images"
    last_trace = None

    def generate_image(self, prompt: str) -> Image.Image:
        size = 256
        if "tileable game weapon-skin" in prompt:
            image = Image.new("RGB", (size, size))
            pixels = image.load()
            for y in range(size):
                for x in range(size):
                    wave = int(42 + 35 * math.sin(x * math.pi / 32))
                    pixels[x, y] = (
                        12 + (x // 24 + y // 24) % 2 * 18,
                        38 + wave,
                        62 + (x + y) % 80,
                    )
            return image

        if "master artwork" in prompt.casefold():
            width, height = 448, 256
        else:
            width, height = size, size
        image = Image.new("RGB", (width, height), (8, 10, 14))
        draw = ImageDraw.Draw(image)
        if "master artwork" in prompt.casefold():
            for offset in range(-height, width + height, 12):
                draw.line(
                    (offset, 0, offset - height, height),
                    fill=(205, 165, 72),
                    width=5,
                )
                draw.line(
                    (offset + 6, 0, offset - height + 6, height),
                    fill=(38, 108, 118),
                    width=3,
                )
        elif "square background asset" in prompt:
            for y in range(size):
                value = 12 + int(18 * math.sin(y * math.pi / 22))
                draw.line((0, y, size, y), fill=(value, value + 5, value + 10))
            for x in range(0, size, 31):
                draw.line((x, 0, x + 80, size), fill=(32, 38, 46), width=3)
        elif "square hero asset" in prompt:
            draw.ellipse((70, 58, 188, 190), outline=(225, 178, 68), width=16)
            draw.arc((88, 72, 170, 178), 30, 315, fill=(238, 220, 156), width=7)
        elif "square secondary asset" in prompt:
            for offset in range(5):
                draw.arc(
                    (58 + offset * 8, 82, 190, 175 + offset * 4),
                    180,
                    350,
                    fill=(90, 140 + offset * 8, 120),
                    width=3,
                )
        else:
            points = [(54, 150), (90, 122), (125, 137), (160, 92), (202, 115)]
            draw.line(points, fill=(204, 168, 72), width=7)
            draw.line([(90, 122), (104, 80)], fill=(150, 126, 58), width=4)
            draw.line([(160, 92), (178, 62)], fill=(150, 126, 58), width=4)
        return image


class RetryConnectorBackend(SyntheticImageBackend):
    def __init__(self) -> None:
        self.calls = 0

    def generate_image(self, prompt: str) -> Image.Image:
        self.calls += 1
        if self.calls == 1:
            image = Image.new("RGB", (256, 256), (180, 140, 55))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 255, 255), outline=(255, 220, 120), width=20)
            return image
        return super().generate_image("square connector asset")


def _planning_tool() -> CreativePlanningTool:
    profile = AssetCreativeProfile.load(
        PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
    )
    return CreativePlanningTool(
        profile,
        ThemeCompiler(
            ThemeLibrary.load_directory(PROJECT_ROOT / "config" / "design_themes")
        ),
        StyleCompiler(
            StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
        ),
        supported_asset_ids=("cs2_ak47_new_geometry",),
    )


class RouteExecutionTests(unittest.TestCase):
    def test_artwork_candidates_preserve_source_and_mapped_views_before_selection(self) -> None:
        planning_tools = ToolRegistry()
        planning_tools.register("plan_directions", _planning_tool())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            planned = SkinSmithAgent(PROJECT_ROOT, planning_tools).run(
                "Design an element-rich dragon-themed AK-47 skin",
                "cs2_ak47_new_geometry",
                candidate_budget=3,
                output_dir=output,
            )
            executor = RouteExecutionTool(
                PROJECT_ROOT,
                SyntheticImageBackend(),
                asset_spec_path=Path("config/assets/ak47_cs2.json"),
                bake_size=64,
                edge_widths=(0, 1),
                asset_seam_maximum=1.0,
                minimum_multiview_retention=0.0,
                export_tga=False,
                enable_refinement=False,
                candidate_preview_size=64,
            )
            execution_tools = ToolRegistry()
            execution_tools.register(
                "generate_artwork_candidates",
                executor.generate_artwork_candidates,
            )
            execution_tools.register("execute_design", executor)
            result = SkinSmithAgent(PROJECT_ROOT, execution_tools).resume(
                output,
                planned.directions[0].direction_id,
            )

            self.assertEqual(result.status, "awaiting_artwork")
            self.assertEqual(len(result.artwork_candidates), 3)
            for candidate in result.artwork_candidates:
                self.assertTrue(Path(candidate.source_path).is_file())
                self.assertGreaterEqual(len(candidate.preview_paths), 3)
                self.assertTrue(
                    all(Path(path).is_file() for path in candidate.preview_paths)
                )
                self.assertEqual(
                    candidate.metrics["preview_bake_size"],
                    64,
                )
            selected = result.artwork_candidates[1]
            completed_agent = SkinSmithAgent(PROJECT_ROOT, execution_tools)
            completed = completed_agent.resume(
                output,
                artwork_choice=selected.candidate_id,
            )
            self.assertEqual(completed.status, "completed")
            self.assertEqual(completed.selected_artwork_id, selected.candidate_id)
            self.assertEqual(completed_agent.state.image_calls_used, 4)
            manifest = json.loads(
                Path(completed.artifacts["execution_manifest"]).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                manifest["selected_artwork"]["candidate_id"],
                selected.candidate_id,
            )
            self.assertEqual(
                manifest["selected_artwork"]["source"],
                selected.source_path,
            )

    def test_executor_rejects_contract_asset_mismatch_before_generation(self) -> None:
        planning_tools = ToolRegistry()
        planning_tools.register("plan_directions", _planning_tool())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            planned = SkinSmithAgent(PROJECT_ROOT, planning_tools).run(
                "Design an AK-47 skin called Wild Lotus",
                "cs2_ak47_new_geometry",
                candidate_budget=3,
                output_dir=output,
            )
            execution_tools = ToolRegistry()
            execution_tools.register(
                "execute_design",
                RouteExecutionTool(
                    PROJECT_ROOT,
                    SyntheticImageBackend(),
                    asset_spec_path=Path(
                        "config/assets/ak47_workbench_official.json"
                    ),
                    bake_size=64,
                    export_tga=False,
                ),
            )
            with self.assertRaisesRegex(
                ValueError,
                "design contract asset does not match execution AssetSpec",
            ):
                SkinSmithAgent(PROJECT_ROOT, execution_tools).resume(
                    output,
                    planned.directions[0].direction_id,
                )

    def test_source_validator_accepts_isolated_role_and_rejects_full_field_hero(self) -> None:
        validator = SourceAssetValidator()
        good = SyntheticImageBackend().generate_image("square hero asset")
        good_result = validator.validate("hero", "hero prompt", good)
        self.assertTrue(good_result.passed, good_result.reasons)

        bad = Image.new("RGB", (256, 256), (190, 150, 70))
        bad_result = validator.validate("hero", "hero prompt", bad)
        self.assertFalse(bad_result.passed)

        subtle_background = Image.new("RGB", (256, 256), (24, 26, 25))
        draw = ImageDraw.Draw(subtle_background)
        for y in range(0, 256, 12):
            draw.line((0, y, 255, y + 8), fill=(42, 45, 43), width=3)
        background_result = validator.validate(
            "background",
            "quiet brushed metal",
            subtle_background,
        )
        self.assertTrue(background_result.passed, background_result.reasons)

    def test_master_artwork_checks_density_and_forbidden_content_only(self) -> None:
        semantic_calls = []

        def reviewer(role, prompt, image):
            semantic_calls.append(role)
            return True, "forbidden-content gate passed"

        validator = SourceAssetValidator(reviewer)
        dense = Image.new("RGB", (448, 256), (15, 20, 25))
        draw = ImageDraw.Draw(dense)
        for offset in range(-256, 704, 12):
            draw.line((offset, 0, offset - 256, 255), fill=(190, 145, 70), width=5)
            draw.line((offset + 6, 0, offset - 250, 255), fill=(35, 100, 110), width=3)
        result = validator.validate("master_artwork", "dense artwork", dense)
        self.assertTrue(result.passed, result.reasons)
        self.assertEqual(
            result.semantic_status,
            "forbidden-content gate passed",
        )
        self.assertEqual(semantic_calls, ["master_artwork"])

        flat = Image.new("RGB", (448, 256), (40, 42, 43))
        flat_result = validator.validate("master_artwork", "dense artwork", flat)
        self.assertFalse(flat_result.passed)

        sparse = Image.new("RGB", (448, 256), (8, 10, 12))
        draw = ImageDraw.Draw(sparse)
        for offset in range(-128, 448, 6):
            draw.line((offset, 0, offset - 128, 127), fill=(210, 160, 75), width=3)
            draw.line(
                (offset + 3, 0, offset - 125, 127),
                fill=(35, 115, 125),
                width=2,
            )
        sparse_result = validator.validate("master_artwork", "dense artwork", sparse)
        self.assertFalse(sparse_result.passed)
        self.assertTrue(
            any("low-detail" in reason for reason in sparse_result.reasons)
        )
        self.assertEqual(semantic_calls, ["master_artwork"])

        forbidden_validator = SourceAssetValidator(
            lambda role, prompt, image: (False, "weapon silhouette detected")
        )
        forbidden_result = forbidden_validator.validate(
            "master_artwork",
            "dense artwork",
            dense,
        )
        self.assertFalse(forbidden_result.passed)
        self.assertIn("weapon silhouette detected", forbidden_result.reasons[0])

    def test_source_validator_runs_semantic_gate_only_after_technical_gate(self) -> None:
        calls = []

        def reviewer(role, prompt, image):
            calls.append((role, prompt, image.size))
            return False, "wrong depicted subject"

        validator = SourceAssetValidator(reviewer)
        good = SyntheticImageBackend().generate_image("square hero asset")
        semantic_result = validator.validate("hero", "dragon head", good)
        self.assertFalse(semantic_result.passed)
        self.assertTrue(semantic_result.technical_passed)
        self.assertIn("wrong depicted subject", semantic_result.reasons[0])
        self.assertEqual(len(calls), 1)

        bad = Image.new("RGB", (256, 256), (190, 150, 70))
        technical_result = validator.validate("hero", "dragon head", bad)
        self.assertFalse(technical_result.passed)
        self.assertEqual(
            technical_result.semantic_status,
            "not_run_technical_gate_failed",
        )
        self.assertEqual(len(calls), 1)

    def test_agent_executes_real_a_b_geometry_chain_with_synthetic_images(self) -> None:
        planning_tools = ToolRegistry()
        planning_tools.register("plan_directions", _planning_tool())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            planned = SkinSmithAgent(PROJECT_ROOT, planning_tools).run(
                "Design an AK-47 skin called Wild Lotus",
                "cs2_ak47_new_geometry",
                candidate_budget=3,
                output_dir=output,
            )
            selected_id = planned.directions[0].direction_id

            execution_tools = ToolRegistry()
            execution_tools.register(
                "execute_design",
                RouteExecutionTool(
                    PROJECT_ROOT,
                    SyntheticImageBackend(),
                    asset_spec_path=Path("config/assets/ak47_cs2.json"),
                    bake_size=64,
                    edge_widths=(0, 1),
                    asset_seam_maximum=1.0,
                    minimum_multiview_retention=0.0,
                    minimum_refinement_improvement=1.0,
                    export_tga=False,
                ),
            )
            resumed_agent = SkinSmithAgent(PROJECT_ROOT, execution_tools)
            result = resumed_agent.resume(output, selected_id)

            self.assertEqual(result.status, "completed")
            self.assertEqual(resumed_agent.state.image_calls_used, 2)
            self.assertEqual(resumed_agent.state.refinement_rounds_used, 1)
            self.assertTrue(Path(result.artifacts["execution_manifest"]).is_file())
            self.assertTrue(Path(result.artifacts["selected_texture_png"]).is_file())
            self.assertEqual(len(result.artifacts["selected_previews"]), 4)
            self.assertIn(result.decision["selected_route"], {"A", "B"})
            self.assertIn("route_a", result.metrics)
            self.assertIn("route_b", result.metrics)
            self.assertIn("route_c", result.metrics)
            self.assertEqual(result.decision["route_c"]["accepted"], False)
            manifest = json.loads(
                Path(result.artifacts["execution_manifest"]).read_text(encoding="utf-8")
            )
            for candidate in manifest["route_c"]["candidates"].values():
                for locality in candidate["locality"].values():
                    self.assertEqual(
                        locality["changed_outside_target_halo_count"],
                        0,
                    )

    def test_failed_role_is_retried_locally_and_preserves_both_attempts(self) -> None:
        backend = RetryConnectorBackend()
        tool = RouteExecutionTool(
            PROJECT_ROOT,
            backend,
            asset_spec_path=Path("config/assets/ak47_cs2.json"),
            bake_size=64,
            edge_widths=(0,),
        )
        request = AgentRunRequest(
            brief="retry test",
            asset_id="cs2_ak47_new_geometry",
            candidate_budget=3,
            budget=AgentBudget(max_image_calls=2, max_role_retries=1),
        )
        state = AgentState(run_id="retry_test", request=request)
        events = []
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            context = AgentToolContext(
                state=state,
                memory=AgentMemory(),
                output_dir=output,
                emit=lambda *args, **kwargs: events.append((args, kwargs)),
            )
            records, validations = tool._generate_and_validate_sources(
                context,
                (
                    RouteImageJob(
                        job_id="connector_job",
                        route="B",
                        semantic_role="connector",
                        prompt="square connector asset",
                        output_name="route_b_connector.png",
                    ),
                ),
                output,
            )
            self.assertEqual(backend.calls, 2)
            self.assertEqual(state.image_calls_used, 2)
            self.assertEqual(state.role_retries_used, 1)
            self.assertEqual(len(records), 2)
            self.assertTrue(Path(records[0]["output"]).is_file())
            self.assertTrue(Path(records[1]["output"]).is_file())
            self.assertNotEqual(records[0]["sha256"], records[1]["sha256"])
            self.assertTrue((output / "route_b_connector.png").is_file())
            self.assertTrue(validations["connector"].passed)

            resumed_state = AgentState(run_id="retry_resume", request=request)
            resumed_context = AgentToolContext(
                state=resumed_state,
                memory=AgentMemory(),
                output_dir=output,
                emit=lambda *args, **kwargs: events.append((args, kwargs)),
            )
            resumed_records, resumed_validations = tool._generate_and_validate_sources(
                resumed_context,
                (
                    RouteImageJob(
                        job_id="connector_job",
                        route="B",
                        semantic_role="connector",
                        prompt="square connector asset",
                        output_name="route_b_connector.png",
                    ),
                ),
                output,
            )
            self.assertEqual(backend.calls, 2)
            self.assertEqual(resumed_state.image_calls_used, 0)
            self.assertEqual(resumed_state.role_retries_used, 0)
            self.assertEqual(resumed_records, [])
            self.assertTrue(resumed_validations["connector"].passed)


if __name__ == "__main__":
    unittest.main()
