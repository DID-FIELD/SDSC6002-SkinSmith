from __future__ import annotations

import csv
import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

from .pipeline import SkinSmithPipeline
from .refinement import decide_refinement, diagnose_candidate, make_round_1_spec
from .spec import DesignSpec


class BoundedRefinementAgent:
    """Run exactly one evaluator-driven refinement round and preserve both rounds."""

    def __init__(self, pipeline: SkinSmithPipeline, minimum_improvement: float = 0.01) -> None:
        if minimum_improvement <= 0:
            raise ValueError("minimum_improvement must be positive")
        self.pipeline = pipeline
        self.minimum_improvement = float(minimum_improvement)

    def run(self, spec: DesignSpec, output_dir: Path) -> dict[str, Any]:
        started = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)

        round_0_spec = replace(spec, candidate_count=4, refinement_directives=())
        round_0 = self.pipeline.run(round_0_spec, output_dir / "round_0")
        round_0_best = round_0["candidates"][0]
        diagnosis = diagnose_candidate(round_0_best)

        round_1_spec = make_round_1_spec(round_0_spec, diagnosis)
        round_1 = self.pipeline.run(round_1_spec, output_dir / "round_1")
        round_1_best = round_1["candidates"][0]
        decision = decide_refinement(
            float(round_0_best["scores"]["total_score"]),
            float(round_1_best["scores"]["total_score"]),
            self.minimum_improvement,
        )
        selected = round_1_best if decision.accepted else round_0_best
        selected_round = decision.selected_round

        result: dict[str, Any] = {
            "agent": {
                "type": type(self).__name__,
                "maximum_refinement_rounds": 1,
                "round_0_candidate_count": 4,
                "round_1_candidate_count": 2,
                "minimum_improvement": self.minimum_improvement,
                "runtime_seconds": time.perf_counter() - started,
            },
            "design_spec": round_0_spec.to_dict(),
            "diagnosis": diagnosis.to_dict(),
            "decision": decision.to_dict(),
            "selected": {
                "round": selected_round,
                "candidate_id": selected["candidate_id"],
                "seed": selected["seed"],
                "total_score": selected["scores"]["total_score"],
                "texture": selected["texture"],
                "previews": selected["previews"],
            },
            "rounds": {"round_0": round_0, "round_1": round_1},
        }
        (output_dir / "agent_log.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        self._write_summary(output_dir / "run_summary.csv", round_0, round_1, selected_round, selected)
        return result

    @staticmethod
    def _write_summary(
        path: Path,
        round_0: dict[str, Any],
        round_1: dict[str, Any],
        selected_round: int,
        selected: dict[str, Any],
    ) -> None:
        fields = (
            "round",
            "rank",
            "candidate_id",
            "seed",
            "texture_score",
            "multi_view_score",
            "semantic_score",
            "total_score",
            "selected",
        )
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for round_number, round_result in ((0, round_0), (1, round_1)):
                for candidate in round_result["candidates"]:
                    scores = candidate["scores"]
                    writer.writerow(
                        {
                            "round": round_number,
                            "rank": candidate["rank"],
                            "candidate_id": candidate["candidate_id"],
                            "seed": candidate["seed"],
                            "texture_score": scores["texture_score"],
                            "multi_view_score": scores["multi_view"]["total_score"]
                            if scores["multi_view"]
                            else "",
                            "semantic_score": scores["semantic"]["total_score"] if scores["semantic"] else "",
                            "total_score": scores["total_score"],
                            "selected": round_number == selected_round
                            and candidate["candidate_id"] == selected["candidate_id"],
                        }
                    )
