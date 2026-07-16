from __future__ import annotations

import sys
import unittest
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.ablation import (  # noqa: E402
    _apply_component_detail_correction,
    paired_route_summary,
)


def _record(candidate_id: str, seam: float, view: float, balance: float, agent: float) -> dict:
    return {
        "candidate_id": candidate_id,
        "asset_seam": {"total_error": seam},
        "standard_score": {"multi_view": {"total_score": view}},
        "component_detail_balance": balance,
        "agent_score": agent,
    }


class AblationTests(unittest.TestCase):
    def test_component_correction_is_zero_outside_target_halo(self) -> None:
        texture = Image.new("RGB", (64, 64), (20, 20, 20))
        pixels = np.asarray(texture).copy()
        pixels[20:44, 20:44] = np.indices((24, 24)).sum(axis=0)[..., None] % 2 * 220
        texture = Image.fromarray(pixels.astype(np.uint8), mode="RGB")
        mask = Image.new("L", (64, 64), 0)
        mask_array = np.asarray(mask).copy()
        mask_array[26:38, 26:38] = 255
        mask = Image.fromarray(mask_array, mode="L")
        corrected = _apply_component_detail_correction(
            texture, mask, intensity=1, transition_sigma=2.0
        )
        changed = np.max(
            np.abs(
                np.asarray(texture, dtype=np.int16)
                - np.asarray(corrected, dtype=np.int16)
            ),
            axis=2,
        ) > 1
        allowed = cv2.dilate(
            (mask_array > 127).astype(np.uint8),
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)),
        ) > 0
        self.assertEqual(int(np.count_nonzero(changed & ~allowed)), 0)

    def test_paired_summary_uses_positive_values_for_b_improvement(self) -> None:
        route_a = [
            _record("candidate_01", 0.20, 0.60, 0.3, 0.4),
            _record("candidate_02", 0.18, 0.62, 0.4, 0.5),
        ]
        route_b = [
            _record("candidate_01", 0.01, 0.65, 0.5, 0.6),
            _record("candidate_02", 0.02, 0.64, 0.5, 0.55),
        ]
        summary = paired_route_summary(
            route_a, route_b, bootstrap_seed=7, bootstrap_samples=100
        )
        self.assertGreater(summary["asset_seam_improvement"]["mean"], 0)
        self.assertEqual(summary["multi_view_improvement"]["win_rate"], 1.0)
        self.assertAlmostEqual(summary["agent_score_improvement"]["paired_values"][0], 0.2)
        self.assertAlmostEqual(summary["agent_score_improvement"]["paired_values"][1], 0.05)

    def test_paired_summary_rejects_mismatched_candidate_pool(self) -> None:
        with self.assertRaises(ValueError):
            paired_route_summary(
                [_record("candidate_01", 0.2, 0.6, 0.3, 0.4)],
                [_record("candidate_02", 0.1, 0.7, 0.4, 0.5)],
                bootstrap_seed=7,
            )


if __name__ == "__main__":
    unittest.main()
