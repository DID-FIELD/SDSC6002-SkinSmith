from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith import BoundedRefinementAgent, SkinSmithPipeline  # noqa: E402
from skinsmith.generator import DiffusionTextureGenerator, build_texture_prompt  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer  # noqa: E402
from skinsmith.refinement import diagnose_candidate, make_round_1_spec  # noqa: E402
from skinsmith.semantic import ClipSemanticEvaluator  # noqa: E402
from skinsmith.spec import DesignSpec  # noqa: E402


SD_TURBO_REVISION = "b261bac6fd2cf515557d5d0707481eafa0485ec2"


def load_spec() -> DesignSpec:
    themes = json.loads((PROJECT_ROOT / "config" / "themes.json").read_text(encoding="utf-8"))
    theme_name = "neon_tide"
    theme = themes[theme_name]
    return DesignSpec(
        theme_name=theme_name,
        description=theme["description"],
        palette=tuple(theme["palette"]),
        motif=theme["motif"],
        candidate_count=4,
    )


def plan(spec: DesignSpec) -> dict:
    from transformers import CLIPTokenizer

    previous = json.loads(
        (PROJECT_ROOT / "runs" / "diffusion_real_model" / "agent_log.json").read_text(encoding="utf-8")
    )
    semantic_run = json.loads(
        (PROJECT_ROOT / "runs" / "semantic_existing_candidates" / "agent_log.json").read_text(encoding="utf-8")
    )
    previous_best = previous["candidates"][0]
    semantic_best = next(
        candidate for candidate in semantic_run["candidates"] if candidate["candidate_id"] == previous_best["candidate_id"]
    )
    previous_best["scores"]["semantic"] = semantic_best["semantic"]
    diagnosis = diagnose_candidate(previous_best)
    round_1_spec = make_round_1_spec(spec, diagnosis)
    prompt = build_texture_prompt(round_1_spec)
    tokenizer = CLIPTokenizer.from_pretrained(
        "stabilityai/sd-turbo",
        subfolder="tokenizer",
        revision=SD_TURBO_REVISION,
        local_files_only=True,
    )
    prompt_tokens = len(tokenizer(prompt, truncation=False)["input_ids"])
    return {
        "diagnosis": diagnosis.to_dict(),
        "round_1_spec": round_1_spec.to_dict(),
        "round_1_prompt": prompt,
        "prompt_tokens": prompt_tokens,
        "prompt_token_limit": int(tokenizer.model_max_length),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Run the one real two-round acceptance experiment")
    args = parser.parse_args()
    spec = load_spec()
    planned = plan(spec)
    if not args.execute:
        print(json.dumps(planned, indent=2))
        return

    model_path = PROJECT_ROOT / "third_party" / "valve_geometry" / "weapon_rif_ak47.obj"
    if not model_path.exists():
        raise SystemExit(f"Missing local Valve model: {model_path}\nSee ASSET_SETUP.md.")
    pipeline = SkinSmithPipeline(
        generator=DiffusionTextureGenerator(),
        renderer=ObjMultiViewRenderer(model_path),
        semantic_evaluator=ClipSemanticEvaluator(),
    )
    result = BoundedRefinementAgent(pipeline).run(spec, PROJECT_ROOT / "runs" / "diffusion_refinement")
    print(json.dumps({"plan": planned, "decision": result["decision"], "selected": result["selected"]}, indent=2))


if __name__ == "__main__":
    main()
