from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.semantic import ClipSemanticEvaluator  # noqa: E402


def main() -> None:
    source_dir = PROJECT_ROOT / "runs" / "diffusion_real_model"
    output_dir = PROJECT_ROOT / "runs" / "semantic_existing_candidates"
    source_log = json.loads((source_dir / "agent_log.json").read_text(encoding="utf-8"))
    description = source_log["design_spec"]["description"]
    evaluator = ClipSemanticEvaluator()
    rows: list[dict[str, object]] = []

    for candidate in source_log["candidates"]:
        candidate_id = candidate["candidate_id"]
        texture_path = source_dir / "candidates" / f"{candidate_id}_seamless.png"
        preview_paths = [
            source_dir / "previews" / f"{candidate_id}_{view}.png"
            for view in ("left", "right", "top")
        ]
        with Image.open(texture_path) as texture:
            semantic = evaluator.evaluate(description, texture.convert("RGB"), preview_paths)
        texture_score = float(candidate["scores"]["texture_score"])
        multi_view_score = float(candidate["scores"]["multi_view"]["total_score"])
        total_score = 0.45 * texture_score + 0.30 * multi_view_score + 0.25 * semantic.total_score
        rows.append(
            {
                "candidate_id": candidate_id,
                "texture_score": texture_score,
                "multi_view_score": multi_view_score,
                "semantic_cosine": semantic.combined_cosine,
                "semantic_score": semantic.total_score,
                "total_score": total_score,
                "semantic": semantic.__dict__,
            }
        )

    rows.sort(key=lambda row: float(row["total_score"]), reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank

    result = {
        "source_run": str(source_dir),
        "description": description,
        "weights": {"texture": 0.45, "multi_view": 0.30, "semantic": 0.25},
        "evaluator": evaluator.metadata(),
        "best_candidate": rows[0]["candidate_id"],
        "candidates": rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "agent_log.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    fieldnames = [
        "rank",
        "candidate_id",
        "texture_score",
        "multi_view_score",
        "semantic_cosine",
        "semantic_score",
        "total_score",
    ]
    with (output_dir / "run_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"best_candidate": rows[0]["candidate_id"], "candidates": rows}, indent=2))


if __name__ == "__main__":
    main()
