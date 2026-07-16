from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.design_routes import (  # noqa: E402
    AssetCreativeProfile,
    RecordedAgentThemeBackend,
    RouteDesignPlanner,
    ThemeCompiler,
    ThemeLibrary,
)
from skinsmith.api_backends import (  # noqa: E402
    GeminiStyleBackend,
    GeminiThemeBackend,
    OpenAIStyleBackend,
    OpenAIThemeBackend,
)
from skinsmith.style_planner import StyleCompiler, StyleLibrary  # noqa: E402


def _theme_context(theme) -> dict:
    return {
        "theme_id": theme.theme_id,
        "display_name": theme.display_name,
        "generation_label": theme.generation_label,
        "concept": theme.concept,
        "narrative": theme.narrative,
        "palette": list(theme.palette),
        "elements": [
            {
                "element_id": element.element_id,
                "display_name": element.display_name,
                "semantic_role": element.semantic_role,
                "generation_description": element.generation_description,
            }
            for element in theme.elements
        ],
        "component_story": {
            story.component: {
                "narrative_role": story.narrative_role,
                "element_ids": list(story.element_ids),
                "prominence": story.prominence,
                "detail_density": story.detail_density,
            }
            for story in theme.component_story
        },
        "composition_groups": [
            {
                "group_id": group.group_id,
                "composition_mode": group.composition_mode,
                "semantic_role": group.semantic_role,
                "element_ids": list(group.element_ids),
                "components": list(group.components),
                "narrative_role": group.narrative_role,
                "surfaces": list(group.surfaces),
                "mirror_on_right": group.mirror_on_right,
                "allow_muzzle_focus": group.allow_muzzle_focus,
            }
            for group in theme.composition_groups
        ],
        "evaluation_criteria": list(theme.evaluation_criteria),
        "reference_policy": theme.reference_policy,
        "default_style_id": theme.default_style_id,
    }


def main() -> None:
    api_defaults = json.loads(
        (PROJECT_ROOT / "config" / "creative_api.json").read_text(encoding="utf-8")
    )
    parser = argparse.ArgumentParser(description="Plan truly distinct Route-A and Route-B designs.")
    parser.add_argument("brief", help="Natural-language design brief")
    parser.add_argument("--theme", default="auto", help="Theme pack or auto")
    parser.add_argument("--style", default="auto", help="Style pack or auto/default from theme")
    parser.add_argument(
        "--recorded-theme",
        type=Path,
        help="Preserved creative-agent response for an uncached theme",
    )
    parser.add_argument(
        "--theme-provider",
        choices=("openai", "gemini"),
        help="Live structured-output provider for an uncached theme",
    )
    parser.add_argument("--theme-model", help="Override the provider's default text model")
    parser.add_argument("--style-model", help="Override the provider's style-compiler model")
    parser.add_argument(
        "--api-key-env",
        help="Override OPENAI_API_KEY or GEMINI_API_KEY; the key itself is never recorded",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "runs" / "design_route_plan" / "route_design_bundle.json",
    )
    args = parser.parse_args()
    if args.recorded_theme and args.theme_provider:
        parser.error("--recorded-theme and --theme-provider are mutually exclusive")

    themes = ThemeLibrary.load_directory(PROJECT_ROOT / "config" / "design_themes")
    styles = StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
    asset_profile = AssetCreativeProfile.load(
        PROJECT_ROOT / "config" / "assets" / "ak47_weapon_space_anchors.json"
    )
    recorded_backend = (
        RecordedAgentThemeBackend(args.recorded_theme) if args.recorded_theme else None
    )
    api_backend = None
    style_api_backend = None
    style_ids = tuple(style.style_id for style in styles.packs)
    if args.theme_provider == "openai":
        api_backend = OpenAIThemeBackend(
            args.theme_model or "gpt-5.4-mini",
            api_key_env=args.api_key_env or "OPENAI_API_KEY",
            style_ids=style_ids,
        )
        style_api_backend = OpenAIStyleBackend(
            args.style_model or args.theme_model or "gpt-5.4-mini",
            api_key_env=args.api_key_env or "OPENAI_API_KEY",
        )
    elif args.theme_provider == "gemini":
        api_backend = GeminiThemeBackend(
            args.theme_model or api_defaults["theme_model"],
            api_key_env=args.api_key_env or api_defaults["theme_api_key_env"],
            style_ids=style_ids,
        )
        style_api_backend = GeminiStyleBackend(
            args.style_model or args.theme_model or api_defaults["theme_model"],
            api_key_env=args.api_key_env or api_defaults["theme_api_key_env"],
        )
    synthesis_backend = recorded_backend or api_backend
    compiled_theme_path = args.output.parent / "compiled_theme.json"
    theme_result = ThemeCompiler(
        themes,
        synthesis_backend,
        backend_id=synthesis_backend.backend_id if synthesis_backend else None,
    ).compile(
        args.brief,
        asset_profile,
        requested_theme=args.theme,
        output_path=compiled_theme_path if synthesis_backend else None,
    )
    theme = theme_result.theme
    if api_backend is not None and api_backend.last_trace is not None:
        trace_path = args.output.parent / "theme_api_trace.json"
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(
            json.dumps(api_backend.last_trace.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    if args.style != "auto":
        style = styles.resolve(args.brief, args.style)
    elif theme_result.source_mode == "generated" and style_api_backend is not None:
        compiled_style_path = args.output.parent / "compiled_style.json"
        style = StyleCompiler(
            styles,
            style_api_backend,
            backend_id=style_api_backend.backend_id,
        ).compile(
            args.brief,
            _theme_context(theme),
            asset_profile.compiler_context(),
            force_generate=True,
            output_path=compiled_style_path,
        ).style
        if style_api_backend.last_trace is not None:
            style_trace_path = args.output.parent / "style_api_trace.json"
            style_trace_path.write_text(
                json.dumps(
                    style_api_backend.last_trace.to_dict(), indent=2, ensure_ascii=False
                ),
                encoding="utf-8",
            )
    else:
        style = styles.resolve(args.brief, theme.default_style_id)
    bundle = RouteDesignPlanner(asset_profile.component_anchors).plan(args.brief, theme, style)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(bundle.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"Wrote Route A={bundle.pattern.design_object}, "
        f"Route B={bundle.weapon_theme.design_object}, Route C={bundle.refinement.base_route}+feedback "
        f"to {args.output}"
    )


if __name__ == "__main__":
    main()
