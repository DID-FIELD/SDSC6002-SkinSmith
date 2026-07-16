from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.generator import DiffusionTextureGenerator, build_texture_prompt  # noqa: E402
from skinsmith.spec import DesignSpec  # noqa: E402


class FakePipeline:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        seed = kwargs["generator"].initial_seed()
        color = (seed % 255, 40, 80)
        return SimpleNamespace(images=[Image.new("RGB", (kwargs["width"], kwargs["height"]), color)])


class OverlengthTokenizer:
    model_max_length = 77

    def __call__(self, prompt: str, truncation: bool):
        return {"input_ids": list(range(78))}


class DiffusionGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = DesignSpec(
            theme_name="test",
            description="original abstract ocean light pattern, no text, no logo",
            palette=("#001122", "#00CCFF"),
            motif="waves",
            size=64,
            candidate_count=1,
            seed=123,
        )

    def test_prompt_contains_constraints(self) -> None:
        prompt = build_texture_prompt(self.spec)
        self.assertIn("Seamless repeating texture tile", prompt)
        self.assertIn("#001122", prompt)
        self.assertIn("no logo", prompt)
        self.assertIn("weapon", prompt)

    def test_fake_backend_receives_reproducible_parameters(self) -> None:
        fake = FakePipeline()
        generator = DiffusionTextureGenerator(device="cpu", inference_steps=2, pipeline=fake)
        first = generator.generate(self.spec, 123)
        second = generator.generate(self.spec, 123)

        self.assertEqual(first.tobytes(), second.tobytes())
        self.assertEqual(fake.calls[0]["num_inference_steps"], 2)
        self.assertEqual(fake.calls[0]["guidance_scale"], 0.0)
        self.assertEqual(fake.calls[0]["width"], 64)
        self.assertEqual(generator.metadata()["last_seed"], 123)

    def test_rejects_unsupported_step_count(self) -> None:
        with self.assertRaises(ValueError):
            DiffusionTextureGenerator(inference_steps=5)

    def test_rejects_prompt_truncation(self) -> None:
        fake = FakePipeline()
        fake.tokenizer = OverlengthTokenizer()
        generator = DiffusionTextureGenerator(device="cpu", pipeline=fake)
        with self.assertRaisesRegex(ValueError, "exceeding the model limit"):
            generator.generate(self.spec, 123)


if __name__ == "__main__":
    unittest.main()
