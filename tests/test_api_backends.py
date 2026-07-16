from __future__ import annotations

import base64
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.api_backends import (  # noqa: E402
    ApiBackendError,
    GeminiImageBackend,
    GeminiMappedReadabilityReviewer,
    GeminiSemanticSourceReviewer,
    GeminiStyleBackend,
    GeminiThemeBackend,
    OpenAIImageBackend,
    OpenAIThemeBackend,
)
from skinsmith.design_routes import AssetCreativeProfile  # noqa: E402
from skinsmith.generator import ApiTextureGenerator  # noqa: E402
from skinsmith.mapped_readability import DesignElement  # noqa: E402
from skinsmith.spec import DesignSpec  # noqa: E402


def _profile() -> AssetCreativeProfile:
    return AssetCreativeProfile.load(
        PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
    )


def _api_theme() -> dict:
    record = json.loads(
        (
            PROJECT_ROOT
            / "runs"
            / "theme_compilation_chip_circuit"
            / "recorded_agent_theme.json"
        ).read_text(encoding="utf-8")
    )["theme"]
    # The preserved evidence predates the English-submission cleanup.
    record["display_name"] = "Silicon Vein"
    record["component_story"] = [
        {"component": component, **story}
        for component, story in record["component_story"].items()
    ]
    return record


def _png_base64() -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (20, 40, 60)).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class ApiBackendTests(unittest.TestCase):
    def test_mapped_readability_reviewer_compares_source_and_three_named_views(self) -> None:
        captured = {}

        def transport(method, url, headers, payload, timeout):
            captured["payload"] = payload
            captured["headers"] = headers
            captured["url"] = url
            return {
                "outputs": [
                    {
                        "type": "model_output",
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "elements": [
                                            {
                                                "element_id": "dragon",
                                                "source_score": 1.0,
                                                "left_score": 0.9,
                                                "right_score": 0.7,
                                                "top_score": 0.3,
                                                "best_view": "left",
                                                "source_evidence": "dragon visible",
                                                "mapped_evidence": "receiver dragon",
                                                "confidence": 0.9,
                                            }
                                        ]
                                    }
                                ),
                            }
                        ],
                    }
                ]
            }

        reviewer = GeminiMappedReadabilityReviewer(transport=transport)
        image = Image.new("RGB", (16, 16), (10, 12, 14))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-gemini"}, clear=False):
            matches = reviewer(
                (DesignElement("dragon", "Dragon", "celestial dragon"),),
                image,
                {"left": image, "right": image, "top": image},
            )
        self.assertEqual(matches[0].best_view, "left")
        self.assertEqual(len(captured["payload"]["input"]), 5)
        self.assertIn("recommendation-only", captured["payload"]["input"][0]["text"])
        trace = json.dumps(reviewer.last_trace.to_dict())
        self.assertNotIn("secret-gemini", trace)
        self.assertNotIn(captured["payload"]["input"][1]["data"], trace)

    def test_openai_theme_backend_uses_schema_and_redacts_key(self) -> None:
        captured = {}

        def transport(method, url, headers, payload, timeout):
            captured.update(
                method=method, url=url, headers=headers, payload=payload, timeout=timeout
            )
            return {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": json.dumps(_api_theme())}
                        ],
                    }
                ]
            }

        backend = OpenAIThemeBackend(
            style_ids=("retro_futurist_neon_v1",), transport=transport
        )
        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret-openai"}, clear=False):
            theme = backend("chip circuit", _profile())
        self.assertEqual(theme["theme_id"], "silicon_pulse_v1")
        self.assertEqual(set(theme["component_story"]), set(_profile().component_anchors))
        self.assertEqual(
            captured["payload"]["text"]["format"]["type"], "json_schema"
        )
        trace = backend.last_trace.to_dict()
        self.assertNotIn("secret-openai", json.dumps(trace))
        self.assertFalse(trace["api_key_recorded"])

    def test_gemini_theme_backend_uses_interactions_response_schema(self) -> None:
        captured = {}

        def transport(method, url, headers, payload, timeout):
            captured["payload"] = payload
            captured["headers"] = headers
            captured["url"] = url
            return {
                "steps": [
                    {
                        "type": "model_output",
                        "content": [{"type": "text", "text": json.dumps(_api_theme())}],
                    }
                ]
            }

        backend = GeminiThemeBackend(
            style_ids=("retro_futurist_neon_v1",), transport=transport
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-gemini"}, clear=False):
            theme = backend("chip circuit", _profile())
        self.assertEqual(theme["display_name"], "Silicon Vein")
        self.assertTrue(captured["url"].endswith("/v1beta/interactions"))
        self.assertEqual(captured["headers"]["Api-Revision"], "2026-05-20")
        response_format = captured["payload"]["response_format"]
        self.assertEqual(response_format["mime_type"], "application/json")
        self.assertEqual(response_format["schema"]["type"], "object")
        self.assertNotIn("composition_groups", response_format["schema"]["required"])
        self.assertNotIn("composition_groups", response_format["schema"]["properties"])

    def test_gemini_style_backend_requests_dynamic_component_roles(self) -> None:
        captured = {}
        style = json.loads(
            (
                PROJECT_ROOT / "config" / "styles" / "retro_futurist_neon.json"
            ).read_text(encoding="utf-8")
        )

        def transport(method, url, headers, payload, timeout):
            captured["payload"] = payload
            return {
                "steps": [
                    {
                        "type": "model_output",
                        "content": [{"type": "text", "text": json.dumps(style)}],
                    }
                ]
            }

        profile = _profile()
        backend = GeminiStyleBackend(transport=transport)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-gemini"}, clear=False):
            result = backend(
                "dark marble with warm gold veins",
                {"palette": ["#111214", "#B88A44"]},
                profile.compiler_context(),
            )

        self.assertEqual(result["style_id"], "retro_futurist_neon_v1")
        schema = captured["payload"]["response_format"]["schema"]
        component_schema = schema["properties"]["component_roles"]
        self.assertEqual(
            set(component_schema["required"]), set(profile.component_anchors)
        )
        self.assertNotIn("secret-gemini", json.dumps(backend.last_trace.to_dict()))

    def test_missing_key_fails_before_transport(self) -> None:
        backend = OpenAIThemeBackend(
            style_ids=("retro_futurist_neon_v1",),
            transport=lambda *args: self.fail("transport must not be called"),
        )
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ApiBackendError, "OPENAI_API_KEY"):
                backend("any theme", _profile())

    def test_image_backends_decode_provider_responses(self) -> None:
        encoded = _png_base64()
        openai = OpenAIImageBackend(
            transport=lambda *args: {"data": [{"b64_json": encoded}]}
        )
        gemini = GeminiImageBackend(
            transport=lambda *args: {
                "steps": [
                    {
                        "type": "model_output",
                        "content": [
                            {"type": "image", "mime_type": "image/png", "data": encoded}
                        ],
                    }
                ]
            }
        )
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "one", "GEMINI_API_KEY": "two"},
            clear=False,
        ):
            self.assertEqual(openai.generate_image("test").size, (8, 8))
            self.assertEqual(gemini.generate_image("test").size, (8, 8))
        self.assertEqual(
            gemini.last_trace.request["response_format"]["mime_type"],
            "image/jpeg",
        )

    def test_gemini_image_backend_accepts_scope_reference_image(self) -> None:
        captured = {}

        def transport(method, url, headers, payload, timeout):
            captured["payload"] = payload
            return {
                "steps": [
                    {
                        "type": "model_output",
                        "content": [
                            {
                                "type": "image",
                                "mime_type": "image/png",
                                "data": _png_base64(),
                            }
                        ],
                    }
                ]
            }

        backend = GeminiImageBackend(transport=transport)
        guide = Image.new("RGB", (16, 16), (255, 255, 255))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-gemini"}, clear=False):
            result = backend.generate_image_with_references("fit this scope", (guide,))
        self.assertEqual(result.size, (8, 8))
        inputs = captured["payload"]["input"]
        self.assertEqual(inputs[0]["type"], "text")
        self.assertEqual(inputs[1]["type"], "image")
        self.assertEqual(inputs[1]["mime_type"], "image/png")
        self.assertNotIn("secret-gemini", json.dumps(backend.last_trace.to_dict()))

    def test_gemini_semantic_source_reviewer_uses_image_and_structured_result(self) -> None:
        captured = {}

        def transport(method, url, headers, payload, timeout):
            captured["payload"] = payload
            return {
                "steps": [
                    {
                        "type": "model_output",
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "passed": False,
                                        "summary": "wrong subject",
                                        "depicted_subjects": ["claw marks"],
                                        "violations": ["dragon head is absent"],
                                    }
                                ),
                            }
                        ],
                    }
                ]
            }

        reviewer = GeminiSemanticSourceReviewer(transport=transport)
        image = Image.new("RGB", (16, 16), (10, 12, 14))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-gemini"}, clear=False):
            passed, status = reviewer("hero", "dragon head plus short neck", image)

        self.assertFalse(passed)
        self.assertIn("dragon head is absent", status)
        self.assertEqual(captured["payload"]["input"][1]["type"], "image")
        self.assertEqual(
            captured["payload"]["response_format"]["mime_type"],
            "application/json",
        )
        self.assertNotIn("secret-gemini", json.dumps(reviewer.last_trace.to_dict()))
        self.assertNotIn(
            captured["payload"]["input"][1]["data"],
            json.dumps(reviewer.last_trace.to_dict()),
        )

    def test_master_artwork_review_checks_forbidden_content_not_subject_parts(self) -> None:
        captured = {}

        def transport(method, endpoint, headers, payload, timeout):
            captured["payload"] = payload
            return {
                "outputs": [
                    {
                        "type": "model_output",
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "passed": True,
                                        "summary": "no forbidden presentation content",
                                        "depicted_subjects": ["dragon", "clouds"],
                                        "violations": [],
                                    }
                                ),
                            }
                        ],
                    }
                ]
            }

        reviewer = GeminiSemanticSourceReviewer(transport=transport)
        image = Image.new("RGB", (16, 16), (10, 12, 14))
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-gemini"}, clear=False):
            passed, _ = reviewer("master_artwork", "dense dragon artwork", image)

        self.assertTrue(passed)
        review_prompt = captured["payload"]["input"][0]["text"]
        self.assertIn("Do not judge whether a named anatomical part", review_prompt)
        self.assertIn("multiple distinct medium/small", review_prompt)
        self.assertIn("Reject any visible or implied firearm", review_prompt)

    def test_api_texture_generator_adapts_image_backend_to_existing_pipeline(self) -> None:
        class FakeImageBackend:
            backend_id = "fake:image"

            @staticmethod
            def generate_image(prompt):
                return Image.new("RGB", (64, 64), (10, 20, 30))

        generator = ApiTextureGenerator(FakeImageBackend())
        spec = DesignSpec(
            theme_name="test",
            description="dense original cats and dogs",
            palette=("#000000", "#FFFFFF"),
            motif="diagonal",
            size=32,
        )
        result = generator.generate(spec, 7)
        self.assertEqual(result.size, (32, 32))
        self.assertEqual(generator.metadata()["provider_backend"], "fake:image")


if __name__ == "__main__":
    unittest.main()
