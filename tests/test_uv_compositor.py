from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.uv_compositor import ComponentStyle, UVComposer, apply_uv_edge_safety  # noqa: E402


class UVComposerTests(unittest.TestCase):
    def test_composes_soft_regions_and_returns_common_uv_edge_color(self) -> None:
        source = np.zeros((32, 32, 3), dtype=np.uint8)
        source[..., 0] = np.arange(32, dtype=np.uint8)[None, :] * 8
        left = np.zeros((64, 64), dtype=np.uint8)
        right = np.zeros((64, 64), dtype=np.uint8)
        left[8:56, 8:32] = 255
        right[8:56, 32:56] = 255
        base = (7, 26, 47)
        composer = UVComposer(
            {
                "left": ComponentStyle(contrast=1.2),
                "right": ComponentStyle(rotation_quadrants=1, blur_sigma=2),
            },
            base_color=base,
            transition_sigma=2,
            edge_safe_pixels=6,
        )
        result = composer.compose(
            Image.fromarray(source, mode="RGB"),
            {
                "left": Image.fromarray(left, mode="L"),
                "right": Image.fromarray(right, mode="L"),
            },
        )
        before = np.asarray(result.before_asset_seam_correction)
        after = np.asarray(result.after_asset_seam_correction)
        self.assertEqual(before.shape, (64, 64, 3))
        self.assertEqual(tuple(after[8, 20]), base)
        self.assertFalse(np.array_equal(before[32, 16], before[32, 48]))
        self.assertGreater(np.asarray(result.edge_safety_map)[32, 32], 0)

    def test_rejects_mismatched_masks(self) -> None:
        composer = UVComposer({}, base_color=(0, 0, 0))
        with self.assertRaises(ValueError):
            composer.compose(
                Image.new("RGB", (8, 8)),
                {"a": Image.new("L", (64, 64)), "b": Image.new("L", (65, 64))},
            )

    def test_zero_edge_width_preserves_paintable_source(self) -> None:
        source = Image.new("RGB", (64, 64), (40, 80, 120))
        mask = np.zeros((64, 64), dtype=np.uint8)
        mask[8:56, 8:56] = 255
        corrected, edge_map = apply_uv_edge_safety(
            source,
            {"main": Image.fromarray(mask, mode="L")},
            base_color=(1, 2, 3),
            edge_safe_pixels=0,
        )
        corrected_array = np.asarray(corrected)
        self.assertEqual(tuple(corrected_array[32, 32]), (40, 80, 120))
        self.assertEqual(tuple(corrected_array[0, 0]), (1, 2, 3))
        self.assertEqual(np.asarray(edge_map)[32, 32], 255)


if __name__ == "__main__":
    unittest.main()
