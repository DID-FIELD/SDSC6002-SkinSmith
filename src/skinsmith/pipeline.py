from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from pathlib import Path

from .evaluation import evaluate_candidate
from .generator import ProceduralTextureGenerator, TextureGenerator
from .preview import PreviewRenderer, TiledPreviewRenderer
from .seamless import make_seamless, seam_error
from .semantic import SemanticEvaluator
from .spec import DesignSpec


class SkinSmithPipeline:
    def __init__(
        self,
        generator: TextureGenerator | None = None,
        renderer: PreviewRenderer | None = None,
        semantic_evaluator: SemanticEvaluator | None = None,
    ) -> None:
        self.generator = generator or ProceduralTextureGenerator()
        self.renderer = renderer or TiledPreviewRenderer()
        self.semantic_evaluator = semantic_evaluator

    def run(self, spec: DesignSpec, output_dir: Path) -> dict:
        run_started = time.perf_counter()
        output_dir.mkdir(parents=True, exist_ok=True)
        candidates_dir = output_dir / "candidates"
        previews_dir = output_dir / "previews"
        candidates_dir.mkdir(exist_ok=True)

        records: list[dict] = []
        for index in range(spec.candidate_count):
            candidate_started = time.perf_counter()
            candidate_id = f"candidate_{index + 1:02d}"
            raw = self.generator.generate(spec, spec.seed + index)
            generation_metadata = self.generator.metadata()
            raw_path = candidates_dir / f"{candidate_id}_raw.png"
            raw.save(raw_path)

            before = seam_error(raw)
            repaired = make_seamless(raw)
            after = seam_error(repaired)
            texture_path = candidates_dir / f"{candidate_id}_seamless.png"
            repaired.save(texture_path)

            preview_paths = self.renderer.render(repaired, previews_dir, candidate_id)
            scored_previews = preview_paths if self.renderer.supports_multiview_scoring else None
            semantic = (
                self.semantic_evaluator.evaluate(spec.description, repaired, preview_paths)
                if self.semantic_evaluator is not None
                else None
            )
            score = evaluate_candidate(candidate_id, repaired, scored_previews, semantic)
            records.append(
                {
                    "candidate_id": candidate_id,
                    "seed": spec.seed + index,
                    "generation": generation_metadata,
                    "raw_texture": str(raw_path),
                    "texture": str(texture_path),
                    "previews": [str(path) for path in preview_paths],
                    "seam_error_before": before,
                    "seam_error_after": after,
                    "scores": asdict(score),
                    "runtime_seconds": time.perf_counter() - candidate_started,
                }
            )

        records.sort(key=lambda record: record["scores"]["total_score"], reverse=True)
        for rank, record in enumerate(records, start=1):
            record["rank"] = rank
        result = {
            "design_spec": spec.to_dict(),
            "pipeline": {
                "generator": self.generator.metadata(),
                "renderer": type(self.renderer).__name__,
                "semantic_evaluator": self.semantic_evaluator.metadata() if self.semantic_evaluator else None,
                "runtime_seconds": time.perf_counter() - run_started,
            },
            "scoring": self._scoring_weights(),
            "best_candidate": records[0]["candidate_id"],
            "candidates": records,
        }
        with (output_dir / "agent_log.json").open("w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=True)
        with (output_dir / "run_summary.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=(
                    "rank",
                    "candidate_id",
                    "texture_score",
                    "multi_view_score",
                    "semantic_score",
                    "semantic_cosine",
                    "total_score",
                    "runtime_seconds",
                ),
            )
            writer.writeheader()
            for record in records:
                multi_view = record["scores"]["multi_view"]
                semantic = record["scores"]["semantic"]
                writer.writerow(
                    {
                        "rank": record["rank"],
                        "candidate_id": record["candidate_id"],
                        "texture_score": record["scores"]["texture_score"],
                        "multi_view_score": multi_view["total_score"] if multi_view else "",
                        "semantic_score": semantic["total_score"] if semantic else "",
                        "semantic_cosine": semantic["combined_cosine"] if semantic else "",
                        "total_score": record["scores"]["total_score"],
                        "runtime_seconds": record["runtime_seconds"],
                    }
                )
        return result

    def _scoring_weights(self) -> dict[str, float]:
        has_multiview = self.renderer.supports_multiview_scoring
        has_semantic = self.semantic_evaluator is not None
        if has_multiview and has_semantic:
            return {"texture_weight": 0.45, "multi_view_weight": 0.30, "semantic_weight": 0.25}
        if has_multiview:
            return {"texture_weight": 0.65, "multi_view_weight": 0.35, "semantic_weight": 0.0}
        if has_semantic:
            return {"texture_weight": 0.75, "multi_view_weight": 0.0, "semantic_weight": 0.25}
        return {"texture_weight": 1.0, "multi_view_weight": 0.0, "semantic_weight": 0.0}
