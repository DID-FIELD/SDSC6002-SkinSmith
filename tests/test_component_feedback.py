from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.component_feedback import (  # noqa: E402
    diagnose_component_detail,
    make_detail_reduction_style,
    measure_component_views,
)
from skinsmith.uv_compositor import ComponentStyle  # noqa: E402


class ComponentFeedbackTests(unittest.TestCase):
    def test_measures_detail_and_diagnoses_excess(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = np.zeros((64, 64, 3), dtype=np.uint8)
            for x in range(8, 57, 4):
                cv2.line(candidate, (x, 8), (x, 55), (255, 255, 255), 1)
            visibility = np.zeros((64, 64, 3), dtype=np.uint8)
            visibility[8:56, 8:56] = 255
            candidate_path = root / "candidate_left.png"
            visibility_path = root / "visibility_receiver_left.png"
            Image.fromarray(candidate, mode="RGB").save(candidate_path)
            Image.fromarray(visibility, mode="RGB").save(visibility_path)
            _, aggregates, score = measure_component_views(
                [candidate_path], {"receiver": [visibility_path]}, {"receiver": 0.05}
            )
            self.assertEqual(len(aggregates), 1)
            self.assertGreater(aggregates[0].relative_excess, 0)
            self.assertLess(score, 1.0)
            diagnosis = diagnose_component_detail(aggregates)
            self.assertEqual(diagnosis.target_component, "receiver")

    def test_detail_reduction_changes_only_requested_style_parameters(self) -> None:
        style = ComponentStyle(
            blur_sigma=2,
            rotation_quadrants=3,
            contrast=1.0,
            saturation=0.9,
            motif_strength=0.8,
        )
        corrected = make_detail_reduction_style(style, 2)
        self.assertEqual(corrected.blur_sigma, 10)
        self.assertEqual(corrected.rotation_quadrants, 3)
        self.assertEqual(corrected.saturation, 0.9)
        self.assertLess(corrected.contrast, style.contrast)
        self.assertLess(corrected.motif_strength, style.motif_strength)


if __name__ == "__main__":
    unittest.main()
