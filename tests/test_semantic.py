from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.semantic import scale_clip_similarity  # noqa: E402


class SemanticTests(unittest.TestCase):
    def test_clipscore_scaling(self) -> None:
        self.assertEqual(scale_clip_similarity(-0.1), 0.0)
        self.assertAlmostEqual(scale_clip_similarity(0.2), 0.5)
        self.assertEqual(scale_clip_similarity(0.6), 1.0)


if __name__ == "__main__":
    unittest.main()
