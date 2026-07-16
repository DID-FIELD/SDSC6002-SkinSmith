from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith import SkinSmithPipeline  # noqa: E402
from skinsmith.generator import DiffusionTextureGenerator  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer  # noqa: E402
from skinsmith.spec import DesignSpec  # noqa: E402
from skinsmith.semantic import ClipSemanticEvaluator  # noqa: E402


def main() -> None:
    model_path = PROJECT_ROOT / "third_party" / "valve_geometry" / "weapon_rif_ak47.obj"
    if not model_path.exists():
        raise SystemExit(f"Missing local Valve model: {model_path}\nSee ASSET_SETUP.md.")

    themes = json.loads((PROJECT_ROOT / "config" / "themes.json").read_text(encoding="utf-8"))
    theme_name = "neon_tide"
    theme = themes[theme_name]
    spec = DesignSpec(
        theme_name=theme_name,
        description=theme["description"],
        palette=tuple(theme["palette"]),
        motif=theme["motif"],
        candidate_count=4,
    )
    pipeline = SkinSmithPipeline(
        generator=DiffusionTextureGenerator(),
        renderer=ObjMultiViewRenderer(model_path),
        semantic_evaluator=ClipSemanticEvaluator(),
    )
    result = pipeline.run(spec, PROJECT_ROOT / "runs" / "diffusion_real_model")
    summary = {
        "best_candidate": result["best_candidate"],
        "runtime_seconds": result["pipeline"]["runtime_seconds"],
        "ranking": [
            {
                "rank": candidate["rank"],
                "candidate_id": candidate["candidate_id"],
                "texture_score": candidate["scores"]["texture_score"],
                "multi_view_score": candidate["scores"]["multi_view"]["total_score"],
                "semantic_score": candidate["scores"]["semantic"]["total_score"],
                "semantic_cosine": candidate["scores"]["semantic"]["combined_cosine"],
                "total_score": candidate["scores"]["total_score"],
            }
            for candidate in result["candidates"]
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
