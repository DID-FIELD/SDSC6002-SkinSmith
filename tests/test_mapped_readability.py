from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.mapped_readability import (  # noqa: E402
    DesignElement,
    ElementReadability,
    build_readability_report,
    design_elements_from_records,
)


class MappedReadabilityTests(unittest.TestCase):
    def test_left_view_is_primary_and_report_is_recommendation_only(self) -> None:
        elements = (
            DesignElement("dragon", "dragon", "readable dragon", 2.0),
            DesignElement("cloud", "cloud", "cloud ribbon", 1.0),
        )
        matches = (
            ElementReadability(
                "dragon", 1.0, 0.9, 0.5, 0.2, "left", "source dragon", "left receiver", 0.9
            ),
            ElementReadability(
                "cloud", 0.8, 0.6, 0.7, 0.4, "right", "source cloud", "both sides", 0.8
            ),
        )
        report = build_readability_report(elements, matches)
        self.assertEqual(report["status"], "recommendation_only")
        self.assertTrue(report["human_selection_is_authoritative"])
        self.assertGreater(report["left_readability"], report["top_readability"])
        self.assertEqual(report["visible_element_count"], 2)

    def test_element_builder_prefers_theme_and_direction_before_world_details(self) -> None:
        elements = design_elements_from_records(
            (
                {
                    "element_id": "dragon",
                    "display_name": "Dragon",
                    "generation_description": "several dragons",
                    "semantic_role": "hero",
                },
            ),
            ("flaming pearl",),
            ("Dragon", "waves", "a" * 80),
            maximum=4,
        )
        self.assertEqual([item.element_id for item in elements], ["dragon", "motif_01", "world_02"])
        self.assertGreater(elements[0].weight, elements[-1].weight)


if __name__ == "__main__":
    unittest.main()
