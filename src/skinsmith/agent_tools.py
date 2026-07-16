from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .agent_runtime import (
    AgentEventType,
    AgentRunRequest,
    AgentToolContext,
    directions_from_style_plan,
)
from .design_routes import (
    AssetCreativeProfile,
    RouteDesignPlanner,
    ThemeCompiler,
    ThemePack,
)
from .style_planner import StyleCompiler, StylePlanner


def _associated_world_elements(brief: str, theme: ThemePack) -> tuple[str, ...]:
    """Expand cached or generated themes into crop-robust visual-world ingredients."""

    values = [
        element.display_name for element in theme.elements
    ] + [
        element.generation_description for element in theme.elements
    ]
    haystack = " ".join(
        (brief, theme.display_name, theme.generation_label, theme.concept, theme.narrative)
    ).casefold()
    associations: list[str] = []
    if "dragon" in haystack:
        associations.extend(
            (
                "layered cloud banks",
                "ocean waves and foam",
                "scattered treasure and ancient coins",
                "flaming pearls",
                "mountain silhouettes",
                "lightning forks",
                "mist ribbons",
                "jade ornaments",
                "palace-roof and bronze-vessel pattern fragments",
            )
        )
    if "landscape" in haystack:
        associations.extend(
            (
                "mountains and rocky ridges",
                "rivers, waterfalls, and reflective water",
                "pavilions, bridges, and distant towers",
                "bamboo and pine",
                "small scholar and traveller figures",
                "boats and birds",
                "sun or moon",
                "layered atmospheric mist",
            )
        )
    associations.extend(
        (
            "small symbolic objects related to the main theme",
            "environmental fragments that imply a complete world",
            "atmospheric connectors and motion rhythms",
            "fine material grain and ornamental micro-detail",
        )
    )
    return tuple(dict.fromkeys((*values, *associations)))


def theme_compiler_context(theme: ThemePack) -> dict[str, Any]:
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
        "default_style_id": theme.default_style_id,
    }


class CreativePlanningTool:
    """Compile a brief into validated Theme/Style packs and Agent directions."""

    def __init__(
        self,
        asset_profile: AssetCreativeProfile,
        theme_compiler: ThemeCompiler,
        style_compiler: StyleCompiler,
        *,
        supported_asset_ids: tuple[str, ...] = (),
    ) -> None:
        self.asset_profile = asset_profile
        self.theme_compiler = theme_compiler
        self.style_compiler = style_compiler
        self.supported_asset_ids = {
            asset_profile.asset_id,
            *(item.strip() for item in supported_asset_ids if item.strip()),
        }

    def __call__(
        self,
        context: AgentToolContext,
        payload: AgentRunRequest | dict[str, Any],
    ):
        confirmed_theme_checkpoint = isinstance(payload, dict)
        if isinstance(payload, dict):
            request = payload["request"]
            expansion = payload["theme_expansion"]
            if not isinstance(request, AgentRunRequest):
                raise TypeError("planning payload request must be AgentRunRequest")
            theme = ThemePack.load(Path(str(expansion["theme_path"])))
            theme_source_mode = str(expansion.get("source_mode", "confirmed"))
            theme_backend_id = expansion.get("backend_id")
            compiled_theme_path = str(expansion["theme_path"])
        else:
            request = payload
            expansion = self.expand_theme(context, request)
            theme = ThemePack.load(Path(str(expansion["theme_path"])))
            theme_source_mode = str(expansion.get("source_mode", "confirmed"))
            theme_backend_id = expansion.get("backend_id")
            compiled_theme_path = str(expansion["theme_path"])

        if request.asset_id not in self.supported_asset_ids:
            available = ", ".join(sorted(self.supported_asset_ids))
            raise ValueError(
                f"creative profile does not support asset {request.asset_id!r}; "
                f"supported: {available}"
            )

        planning_dir = context.output_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)

        force_dynamic_style = (
            theme_source_mode == "generated"
            or request.style_family is not None
            or confirmed_theme_checkpoint
        )
        style_brief = request.brief
        if request.style_family is not None:
            style_brief = (
                f"{request.brief}\nBroad style-family preference: "
                f"{request.style_family}. Treat this as guidance, not a fixed style name."
            )
        style_result = self.style_compiler.compile(
            style_brief,
            theme_compiler_context(theme),
            self.asset_profile.compiler_context(),
            force_generate=force_dynamic_style,
            output_path=planning_dir / "compiled_style.json",
        )
        context.emit(
            AgentEventType.OBSERVATION,
            f"Style {style_result.style.style_id} validated from {style_result.source_mode}.",
            tool="style_compiler",
            data={
                "style_id": style_result.style.style_id,
                "source_mode": style_result.source_mode,
                "backend_id": style_result.backend_id,
                "forced_dynamic_style": force_dynamic_style,
            },
        )

        actual_candidate_count = min(
            request.candidate_budget,
            len(style_result.style.candidate_directions),
        )
        if actual_candidate_count < 3:
            raise ValueError("validated style must provide at least three directions")
        plan = StylePlanner(style_result.style).plan(
            request.brief,
            actual_candidate_count,
        )
        route_bundle = RouteDesignPlanner(
            self.asset_profile.component_anchors
        ).plan(
            request.brief,
            theme,
            style_result.style,
        )
        route_bundle_path = planning_dir / "route_design_bundle.json"
        route_bundle_path.write_text(
            json.dumps(route_bundle.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        directions = directions_from_style_plan(
            style_result.style,
            plan,
            style_family=request.style_family,
            world_elements=_associated_world_elements(
                request.brief,
                theme,
            ),
        )
        manifest = {
            "request": asdict(request),
            "asset_profile": str(self.asset_profile.source_path),
            "theme": {
                "id": theme.theme_id,
                "source_mode": theme_source_mode,
                "backend_id": theme_backend_id,
                "path": compiled_theme_path,
            },
            "style": {
                "id": style_result.style.style_id,
                "source_mode": style_result.source_mode,
                "backend_id": style_result.backend_id,
                "path": style_result.compiled_style_path,
            },
            "direction_ids": [item.direction_id for item in directions],
            "route_design_bundle": str(route_bundle_path),
        }
        manifest_path = planning_dir / "planning_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        context.memory.remember(
            f"{context.state.run_id}.creative_plan",
            {
                "theme_id": theme.theme_id,
                "style_id": style_result.style.style_id,
                "direction_ids": manifest["direction_ids"],
                "route_design_bundle": str(route_bundle_path),
            },
            [str(manifest_path), str(route_bundle_path)],
        )
        context.memory.save(context.output_dir / "memory_snapshot.json")
        context.emit(
            AgentEventType.ARTIFACT,
            "Creative planning manifest and memory snapshot saved.",
            tool="plan_directions",
            data={
                "planning_manifest": str(manifest_path),
                "memory_snapshot": str(context.output_dir / "memory_snapshot.json"),
            },
        )
        return directions

    def expand_theme(
        self,
        context: AgentToolContext,
        request: AgentRunRequest,
    ) -> dict[str, Any]:
        if request.asset_id not in self.supported_asset_ids:
            available = ", ".join(sorted(self.supported_asset_ids))
            raise ValueError(
                f"creative profile does not support asset {request.asset_id!r}; "
                f"supported: {available}"
            )
        planning_dir = context.output_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)
        theme_result = self.theme_compiler.compile(
            request.brief,
            self.asset_profile,
            output_path=planning_dir / "compiled_theme.json",
        )
        theme = theme_result.theme
        context.emit(
            AgentEventType.OBSERVATION,
            f"Theme {theme.theme_id} validated from {theme_result.source_mode}.",
            tool="theme_compiler",
            data={
                "theme_id": theme.theme_id,
                "source_mode": theme_result.source_mode,
                "backend_id": theme_result.backend_id,
            },
        )
        return {
            "keyword": request.brief,
            "theme_id": theme.theme_id,
            "display_name": theme.display_name,
            "generation_label": theme.generation_label,
            "concept": theme.concept,
            "narrative": theme.narrative,
            "palette": list(theme.palette),
            "elements": [
                {
                    "element_id": item.element_id,
                    "label": item.display_name,
                    "semantic_role": item.semantic_role,
                    "description": item.generation_description,
                }
                for item in theme.elements
            ],
            "world_elements": list(_associated_world_elements(request.brief, theme)),
            "evaluation_criteria": list(theme.evaluation_criteria),
            "reference_policy": theme.reference_policy,
            "source_mode": theme_result.source_mode,
            "backend_id": theme_result.backend_id,
            "theme_path": theme_result.compiled_theme_path,
        }

    def plan_directions(
        self,
        context: AgentToolContext,
        payload: AgentRunRequest | dict[str, Any],
    ):
        return self(context, payload)
