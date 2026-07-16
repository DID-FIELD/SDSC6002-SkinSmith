from __future__ import annotations

import unittest

from skinsmith.refinement import RefinementDiagnosis, decide_refinement, make_round_1_spec
from skinsmith.spec import DesignSpec


class RefinementTests(unittest.TestCase):
    def test_round_1_is_bounded_to_two_candidates_and_offset_seeds(self) -> None:
        spec = DesignSpec("theme", "description", ("#000000", "#ffffff"), "waves", seed=100)
        diagnosis = RefinementDiagnosis(0.6, 0.8, 0.95, 0.02, ("larger clean shapes",), ())
        refined = make_round_1_spec(spec, diagnosis)
        self.assertEqual(refined.candidate_count, 2)
        self.assertEqual(refined.seed, 1100)
        self.assertEqual(refined.refinement_directives, ("larger clean shapes",))

    def test_refinement_requires_full_minimum_improvement(self) -> None:
        rejected = decide_refinement(0.80, 0.8099)
        accepted = decide_refinement(0.80, 0.81)
        self.assertFalse(rejected.accepted)
        self.assertEqual(rejected.selected_round, 0)
        self.assertTrue(accepted.accepted)
        self.assertEqual(accepted.selected_round, 1)


if __name__ == "__main__":
    unittest.main()
