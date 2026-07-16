from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.agent_runtime import SkinSmithAgent, ToolRegistry  # noqa: E402
from skinsmith.agent_tools import CreativePlanningTool  # noqa: E402
from skinsmith.api_backends import (  # noqa: E402
    GeminiImageBackend,
    GeminiSemanticSourceReviewer,
    GeminiStyleBackend,
    GeminiThemeBackend,
    OpenAIImageBackend,
    OpenAIStyleBackend,
    OpenAIThemeBackend,
)
from skinsmith.design_routes import (  # noqa: E402
    AssetCreativeProfile,
    ThemeCompiler,
    ThemeLibrary,
)
from skinsmith.style_planner import StyleCompiler, StyleLibrary  # noqa: E402
from skinsmith.route_execution import RouteExecutionTool  # noqa: E402
from skinsmith.source_validation import SourceAssetValidator  # noqa: E402


def _provider_backends(provider: str | None, model: str | None):
    if provider is None:
        return None, None
    defaults = json.loads(
        (PROJECT_ROOT / "config" / "creative_api.json").read_text(encoding="utf-8")
    )
    styles = StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
    style_ids = tuple(pack.style_id for pack in styles.packs)
    if provider == "openai":
        selected = model or "gpt-5.4-mini"
        return (
            OpenAIThemeBackend(selected, style_ids=style_ids),
            OpenAIStyleBackend(selected),
        )
    selected = model or defaults["theme_model"]
    api_key_env = defaults["theme_api_key_env"]
    return (
        GeminiThemeBackend(
            selected,
            api_key_env=api_key_env,
            style_ids=style_ids,
        ),
        GeminiStyleBackend(selected, api_key_env=api_key_env),
    )


def _image_backend(provider: str, model: str | None):
    defaults = json.loads(
        (PROJECT_ROOT / "config" / "creative_api.json").read_text(encoding="utf-8")
    )
    if provider == "openai":
        return OpenAIImageBackend(
            model or "gpt-image-2",
            api_key_env="OPENAI_API_KEY",
            size="1536x1024",
            quality="medium",
        )
    return GeminiImageBackend(
        model or defaults["image_model"],
        api_key_env=defaults["image_api_key_env"],
        image_size=defaults["image_size"],
        aspect_ratio=defaults["image_aspect_ratio"],
    )


def _source_validator(provider: str) -> SourceAssetValidator:
    if provider != "gemini":
        return SourceAssetValidator()
    defaults = json.loads(
        (PROJECT_ROOT / "config" / "creative_api.json").read_text(encoding="utf-8")
    )
    return SourceAssetValidator(
        GeminiSemanticSourceReviewer(
            defaults["theme_model"],
            api_key_env=defaults["theme_api_key_env"],
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run SkinSmithAgent creative planning. Until execute_design is registered, "
            "the honest terminal state is awaiting_direction or ready_to_execute."
        )
    )
    parser.add_argument("brief", nargs="?", help="Free-form game-skin design brief")
    parser.add_argument(
        "--asset-id",
        default="cs2_ak47_new_geometry",
        help="Target deployment asset id",
    )
    parser.add_argument(
        "--style-family",
        help="Optional broad preference such as Material, Sci-Fi, or Traditional Art",
    )
    parser.add_argument("--count", type=int, choices=(3, 4), default=4)
    parser.add_argument(
        "--confirm-theme",
        action="store_true",
        help="Confirm the expanded theme checkpoint and continue to direction planning",
    )
    parser.add_argument("--direction", help="Direction id to lock after planning")
    parser.add_argument(
        "--artwork",
        help="Mapped artwork candidate id to lock after comparing source and three views",
    )
    parser.add_argument(
        "--resume",
        type=Path,
        help="Resume an existing Agent run directory at direction or artwork selection",
    )
    parser.add_argument(
        "--retry-role",
        action="append",
        choices=("hero", "secondary", "connector", "background", "master_artwork"),
        help="Reopen a completed run and regenerate only this rejected role; may be repeated",
    )
    parser.add_argument(
        "--review-file",
        type=Path,
        help="Mapped visual-review JSON containing role_decisions and retry_roles",
    )
    parser.add_argument(
        "--additional-image-calls",
        type=int,
        default=0,
        help="Explicit logged budget extension for a failed/completed role-local revision",
    )
    parser.add_argument(
        "--reuse-latest-role",
        action="append",
        choices=("hero", "secondary", "connector", "background", "master_artwork"),
        help="Promote the latest preserved passing attempt without a new image call",
    )
    parser.add_argument(
        "--provider",
        choices=("openai", "gemini"),
        default="gemini",
        help="Structured creative backend required for uncached briefs/styles",
    )
    parser.add_argument("--model", help="Optional provider model override")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run the real Route A/B image, official-UV, render, and evaluation chain",
    )
    parser.add_argument(
        "--image-provider",
        choices=("openai", "gemini"),
        default="gemini",
        help="Image backend used by --execute",
    )
    parser.add_argument("--image-model", help="Optional image model override")
    parser.add_argument(
        "--bake-size",
        type=int,
        choices=(512, 1024, 2048),
        default=512,
        help="Route-B UV bake resolution",
    )
    parser.add_argument(
        "--export-tga",
        action="store_true",
        help="Write formal Workbench TGA files; Route B requires --bake-size 2048",
    )
    parser.add_argument("--output", type=Path, help="Explicit Agent run directory")
    args = parser.parse_args()
    if (
        args.resume is not None
        and not args.retry_role
        and not args.confirm_theme
        and not args.direction
        and not args.artwork
    ):
        parser.error(
            "--resume requires --confirm-theme, --direction, or --artwork"
        )
    if args.resume is not None and (args.direction or args.artwork) and not args.execute:
        parser.error("--direction/--artwork resume requires --execute")
    if args.resume is None and not args.brief:
        parser.error("brief is required unless --resume is used")
    if (
        args.resume is None
        and args.execute
        and not args.direction
        and not args.retry_role
    ):
        parser.error("--execute requires --direction")
    if args.export_tga and args.bake_size != 2048:
        parser.error("--export-tga requires --bake-size 2048")
    if args.retry_role and args.resume is None:
        parser.error("--retry-role requires --resume")
    if args.retry_role and not args.execute:
        parser.error("--retry-role requires --execute")

    tools = ToolRegistry()
    if args.resume is None or args.confirm_theme:
        theme_backend, style_backend = _provider_backends(args.provider, args.model)
        theme_library = ThemeLibrary.load_directory(
            PROJECT_ROOT / "config" / "design_themes"
        )
        style_library = StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
        profile = AssetCreativeProfile.load(
            PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
        )
        planner = CreativePlanningTool(
            profile,
            ThemeCompiler(
                theme_library,
                theme_backend,
                backend_id=theme_backend.backend_id if theme_backend else None,
            ),
            StyleCompiler(
                style_library,
                style_backend,
                backend_id=style_backend.backend_id if style_backend else None,
            ),
            supported_asset_ids=("cs2_ak47_new_geometry",),
        )
        tools.register("expand_theme", planner.expand_theme)
        tools.register("plan_directions", planner.plan_directions)
    if args.execute:
        creative_defaults = json.loads(
            (PROJECT_ROOT / "config" / "creative_api.json").read_text(
                encoding="utf-8"
            )
        )
        executor = RouteExecutionTool(
            PROJECT_ROOT,
            _image_backend(args.image_provider, args.image_model),
            asset_spec_path=Path("config/assets/ak47_cs2.json"),
            source_validator=_source_validator(args.image_provider),
            bake_size=args.bake_size,
            export_tga=args.export_tga,
            candidate_preview_size=creative_defaults.get(
                "candidate_preview_bake_size",
                256,
            ),
        )
        tools.register(
            "generate_artwork_candidates",
            executor.generate_artwork_candidates,
        )
        tools.register(
            "execute_design",
            executor,
        )
        tools.register("retry_roles", executor.retry_roles)
    agent = SkinSmithAgent(PROJECT_ROOT, tools)
    if args.retry_role:
        review_reasons = {}
        if args.review_file is not None:
            review = json.loads(args.review_file.read_text(encoding="utf-8"))
            review_reasons = {
                role: str(record.get("reason", ""))
                for role, record in review.get("role_decisions", {}).items()
                if isinstance(record, dict)
            }
        result = agent.revise(
            args.resume,
            args.retry_role,
            review_reasons=review_reasons,
            additional_image_calls=args.additional_image_calls,
            reuse_latest_roles=args.reuse_latest_role or (),
        )
    elif args.resume is not None:
        result = agent.resume(
            args.resume,
            args.direction,
            args.artwork,
            theme_confirmed=args.confirm_theme,
        )
    else:
        result = agent.run(
            args.brief,
            args.asset_id,
            args.style_family,
            args.count,
            args.direction,
            args.artwork,
            theme_confirmed=args.confirm_theme,
            output_dir=args.output,
        )
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "status": result.status,
                "phase": result.phase.value,
                "theme_expansion": result.theme_expansion,
                "directions": [
                    {
                        "direction_id": item.direction_id,
                        "title": item.title,
                        "concept": item.concept,
                    }
                    for item in result.directions
                ],
                "selected_direction": (
                    result.design_contract.selected_direction.direction_id
                    if result.design_contract
                    else None
                ),
                "artwork_candidates": [
                    {
                        "candidate_id": item.candidate_id,
                        "title": item.title,
                        "variation": item.variation,
                        "source": item.source_path,
                        "previews": list(item.preview_paths),
                        "metrics": item.metrics,
                    }
                    for item in result.artwork_candidates
                ],
                "selected_artwork": result.selected_artwork_id,
                "checkpoint": result.checkpoint_path,
                "stop_reason": result.stop_reason,
                "artifacts": result.artifacts,
                "metrics": result.metrics,
                "decision": result.decision,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
