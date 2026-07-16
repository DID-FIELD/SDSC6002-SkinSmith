from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from skinsmith.replay import discover_replay_runs, load_replay_run, resolve_project_path


class ReplayRunTests(unittest.TestCase):
    def test_loads_result_readability_and_checkpoint_usage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "runs" / "demo"
            (run_dir / "execution").mkdir(parents=True)
            (run_dir / "agent_run_result.json").write_text(
                json.dumps(
                    {
                        "phase": "completed",
                        "selected_artwork_id": "artwork_04",
                        "request": {"budget": {"max_image_calls": 8}},
                        "design_contract": {
                            "selected_direction": {"direction_id": "direction_04"}
                        },
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "checkpoint.json").write_text(
                json.dumps(
                    {
                        "state": {
                            "image_calls_used": 6,
                            "role_retries_used": 1,
                            "refinement_rounds_used": 1,
                        }
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "execution" / "mapped_element_readability.json").write_text(
                json.dumps({"status": "recommendation_only"}),
                encoding="utf-8",
            )

            replay = load_replay_run(root, Path("runs/demo"))

            self.assertEqual(replay.phase, "completed")
            self.assertEqual(replay.selected_direction_id, "direction_04")
            self.assertEqual(replay.selected_artwork_id, "artwork_04")
            self.assertEqual(replay.usage["image_calls_used"], 6)
            self.assertEqual(replay.readability["status"], "recommendation_only")
            self.assertEqual(discover_replay_runs(root), (run_dir,))

    def test_rejects_paths_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                resolve_project_path(root, "../outside.png")

    def test_loads_awaiting_direction_directly_from_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "runs" / "awaiting"
            run_dir.mkdir(parents=True)
            (run_dir / "checkpoint.json").write_text(
                json.dumps(
                    {
                        "state": {
                            "run_id": "run-1",
                            "phase": "awaiting_direction",
                            "request": {"brief": "deep sea ruins"},
                            "candidates": [
                                {
                                    "direction_id": "direction_01",
                                    "title": "Hydrothermal Leak",
                                }
                            ],
                            "artwork_candidates": [],
                        },
                        "events": [{"sequence": 1, "summary": "planned"}],
                    }
                ),
                encoding="utf-8",
            )

            replay = load_replay_run(root, Path("runs/awaiting"))

            self.assertEqual(replay.phase, "awaiting_direction")
            self.assertEqual(
                replay.result["directions"][0]["direction_id"],
                "direction_01",
            )
            self.assertIn(run_dir, discover_replay_runs(root))


if __name__ == "__main__":
    unittest.main()
