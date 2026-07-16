from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.selection import (  # noqa: E402
    Constraint,
    Objective,
    constraint_first_pareto_select,
    weighted_rank,
)


class SelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidates = {
            "raw": {"seam": 0.20, "view": 0.75},
            "narrow": {"seam": 0.009, "view": 0.72},
            "wide": {"seam": 0.002, "view": 0.68},
        }

    def test_constraint_gate_rejects_high_view_invalid_candidate(self) -> None:
        decision = constraint_first_pareto_select(
            self.candidates,
            (Constraint("seam", maximum=0.01),),
            (Objective("view", maximize=True), Objective("seam", maximize=False)),
        )
        self.assertEqual(decision.selected_id, "narrow")
        self.assertEqual(set(decision.pareto_ids), {"narrow", "wide"})
        self.assertIn("raw", decision.rejected_ids)

    def test_weighted_ranking_can_select_constraint_violator(self) -> None:
        ranking = weighted_rank(
            self.candidates,
            {Objective("view", maximize=True): 0.9, Objective("seam", maximize=False): 0.1},
        )
        self.assertEqual(ranking[0][0], "raw")


if __name__ == "__main__":
    unittest.main()
