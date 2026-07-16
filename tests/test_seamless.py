from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from skinsmith.seamless import make_seamless, seam_error  # noqa: E402


class SeamlessTests(unittest.TestCase):
    def test_repair_reduces_periodic_boundary_error(self) -> None:
        rng = np.random.default_rng(42)
        array = rng.integers(0, 256, size=(128, 128, 3), dtype=np.uint8)
        array[:, 0] = 0
        array[:, -1] = 255
        image = Image.fromarray(array, mode="RGB")

        before = seam_error(image)
        after = seam_error(make_seamless(image))

        self.assertGreater(before, 0.2)
        self.assertLess(after, before * 0.25)

    def test_repair_preserves_most_pixels(self) -> None:
        rng = np.random.default_rng(7)
        array = rng.integers(0, 256, size=(128, 128, 3), dtype=np.uint8)
        image = Image.fromarray(array, mode="RGB")
        repaired = np.asarray(make_seamless(image), dtype=np.int16)

        changed = np.any(np.abs(repaired - array.astype(np.int16)) > 2, axis=2)
        mean_change = float(np.abs(repaired - array.astype(np.int16)).mean())
        self.assertLess(mean_change, 24.0)


if __name__ == "__main__":
    unittest.main()
