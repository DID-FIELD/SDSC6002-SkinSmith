from __future__ import annotations

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
    run_dir = PROJECT_ROOT / "runs" / "diffusion_real_model"
    texture = Image.open(run_dir / "candidates" / "candidate_02_seamless.png")
    previews = sorted((run_dir / "previews").glob("candidate_02_*.png"))
    text = "an original abstract deep-sea bioluminescent pattern, flowing cyan lines, violet shadows"
    evaluator = ClipSemanticEvaluator()
    score = evaluator.evaluate(text, texture, previews)
    result = {"score": score.__dict__, "evaluator": evaluator.metadata()}
    output = PROJECT_ROOT / "runs" / "semantic_smoke"
    output.mkdir(parents=True, exist_ok=True)
    (output / "semantic_log.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
