from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping


_SOURCE_ASSET_CONTRACT = (
    "CRITICAL SOURCE-ASSET MODE: all weapon names, component names, and placement "
    "descriptions above are placement metadata only for later composition. No weapon or "
    "weapon part may appear. Do not depict, imply, "
    "crop, silhouette, emboss, or texture any firearm, weapon, receiver, trigger, grip, "
    "magazine, stock, barrel, muzzle, mechanical weapon part, weapon mockup, product "
    "mockup, UV layout, rectangular material sample, framed tile, or presentation board. "
)

_ROLE_CONTRACTS = {
    "master_artwork": (
        "MASTER-ARTWORK CONTRACT: create one dense, opaque, edge-to-edge landscape thematic artwork "
        "with strong local detail at multiple scales. Large crops from any part of the image "
        "must remain visually rich. Use many medium and small subject clusters rather than one "
        "oversized subject: no single element may occupy more than roughly 35% of the canvas "
        "width or height, and no subject may span the complete image width. Weave primary motifs, "
        "supporting symbols, environmental fragments, atmospheric connectors, linework, and "
        "material texture through every region. Do not isolate motifs as separate "
        "stickers and do not leave large plain or near-black negative-space pockets. Do not draw "
        "a weapon, weapon part, mockup, UV layout, text, logo, watermark, border, framed panel, "
        "presentation board, or product render. Subject-part placement is not evaluated."
    ),
    "hero": (
        "Depict only one isolated theme-defining subject with generous empty margin "
        "on a uniform removable near-black background. It must be a free-floating design "
        "element, not applied to any object or slab. Keep the motif open so the background "
        "remains visible through and around it. Small detached theme fragments are allowed, "
        "but there must be no coherent backing slab, full material surface, or rectangular board."
    ),
    "secondary": (
        "ROLE PRIORITY OVERRIDES THE CANDIDATE DIRECTION: depict only three to seven restrained "
        "thin secondary marks using only the secondary content and palette assigned above, clearly "
        "quieter than the hero, isolated on a uniform removable near-black background. Do not import "
        "the hero motif or its dominant accent colour. No central impact, radial burst, complete "
        "scene, material tile, framed square, or finished surface."
    ),
    "connector": (
        "ROLE PRIORITY OVERRIDES THE CANDIDATE DIRECTION: depict only a sparse, branching, "
        "elongated connector network isolated on a perfectly uniform removable near-black "
        "background. The network must float with margin and must not touch the square edges. "
        "No background-material texture, circular centre, radial burst, large focal mass, object, "
        "slab, or scene."
    ),
    "background": (
        "ROLE PRIORITY OVERRIDES THE CANDIDATE DIRECTION: depict only an edge-to-edge, low-contrast, "
        "low-salience background material field using only the background content and quiet palette "
        "assigned above. Do not import any hero/connector motif or their bright accent colours. No "
        "central focal point, hero, object, border, floating slab, mockup, or dominant streak."
    ),
}


@dataclass(frozen=True)
class RouteImageJob:
    job_id: str
    route: str
    semantic_role: str
    prompt: str
    output_name: str
    composition_group_id: str | None = None
    composition_mode: str | None = None
    target_components: tuple[str, ...] = ()


def _direction_prompt(
    candidate_direction: Mapping[str, Any] | None,
    *,
    route: str,
) -> tuple[str, str]:
    if candidate_direction is None:
        return "", ""
    required = ("direction_id", "title", "concept", "motifs")
    if not all(candidate_direction.get(key) for key in required):
        raise ValueError("candidate_direction is incomplete")
    direction_id = str(candidate_direction["direction_id"]).strip()
    motifs = candidate_direction["motifs"]
    if not isinstance(motifs, (list, tuple)) or not motifs:
        raise ValueError("candidate_direction.motifs must contain at least one motif")
    emphasis_key = "route_a_emphasis" if route == "A" else "route_b_emphasis"
    emphasis = str(candidate_direction.get(emphasis_key, "")).strip()
    if not emphasis:
        raise ValueError(f"candidate_direction.{emphasis_key} is required")
    prompt = (
        f"Locked candidate art direction: {candidate_direction['title']} "
        f"({direction_id}). Concept: {candidate_direction['concept']}. "
        f"Motifs: {', '.join(str(item) for item in motifs)}. "
        f"Expanded thematic world: {', '.join(str(item) for item in candidate_direction.get('world_elements', ()))}. "
        f"Route-{route} emphasis: {emphasis}. Do not drift to another art direction. "
    )
    return direction_id, prompt


def plan_route_image_jobs(
    bundle: Mapping[str, Any],
    *,
    route: str = "all",
    route_a_candidates: int = 1,
    candidate_direction: Mapping[str, Any] | None = None,
) -> tuple[RouteImageJob, ...]:
    route = route.casefold()
    if route not in {"a", "b", "all"}:
        raise ValueError("route must be a, b, or all")
    if route_a_candidates < 1:
        raise ValueError("route_a_candidates must be positive")

    jobs: list[RouteImageJob] = []
    if route in {"a", "all"}:
        direction_id, direction_prompt = _direction_prompt(
            candidate_direction,
            route="A",
        )
        direction_suffix = f"__{direction_id}" if direction_id else ""
        pattern = bundle.get("pattern")
        if not isinstance(pattern, dict) or not isinstance(pattern.get("generation_prompt"), str):
            raise ValueError("route bundle is missing pattern.generation_prompt")
        for index in range(1, route_a_candidates + 1):
            jobs.append(
                RouteImageJob(
                    job_id=f"route_a_candidate_{index:02d}{direction_suffix}",
                    route="A",
                    semantic_role="tileable_template_pattern",
                    prompt=(
                        "Use case: stylized-concept. Asset type: tileable game weapon-skin "
                        f"texture source. {pattern['generation_prompt']} {direction_prompt}Candidate {index} of "
                        f"{route_a_candidates}. Output only the square artwork: no weapon, text, logo, "
                        "watermark, presentation border, UV wireframe, or mockup."
                    ),
                    output_name=f"route_a_candidate_{index:02d}.png",
                )
            )

    if route in {"b", "all"}:
        direction_id, direction_prompt = _direction_prompt(
            candidate_direction,
            route="B",
        )
        direction_suffix = f"__{direction_id}" if direction_id else ""
        weapon = bundle.get("weapon_theme")
        briefs = weapon.get("asset_briefs") if isinstance(weapon, dict) else None
        if not isinstance(briefs, (list, tuple)) or not briefs:
            raise ValueError("route bundle is missing weapon_theme.asset_briefs")
        graph_groups_by_id: dict[str, Mapping[str, Any]] = {}
        composition_graph = (
            weapon.get("composition_graph") if isinstance(weapon, Mapping) else None
        )
        graph_groups = (
            composition_graph.get("groups")
            if isinstance(composition_graph, Mapping)
            else None
        )
        if isinstance(graph_groups, (list, tuple)):
            for group in graph_groups:
                if not isinstance(group, Mapping):
                    continue
                graph_group_id = group.get("group_id")
                if isinstance(graph_group_id, str) and graph_group_id:
                    graph_groups_by_id[graph_group_id] = group
        for brief in briefs:
            if not isinstance(brief, Mapping):
                raise ValueError("Route-B asset brief must be an object")
            asset_id = brief.get("asset_id")
            role = brief.get("semantic_role")
            prompt = brief.get("generation_prompt")
            if not all(isinstance(value, str) and value for value in (asset_id, role, prompt)):
                raise ValueError("Route-B asset brief is incomplete")
            group_id = brief.get("composition_group_id")
            if group_id is not None:
                if not isinstance(group_id, str) or not re.fullmatch(
                    r"[a-z0-9][a-z0-9_-]*", group_id
                ):
                    raise ValueError("Route-B composition_group_id is invalid")
            output_token = group_id or role
            graph_group = graph_groups_by_id.get(group_id, {})
            composition_mode = brief.get(
                "composition_mode",
                graph_group.get("composition_mode"),
            )
            if composition_mode is not None and composition_mode not in {
                "spanning",
                "grouped",
                "independent",
                "background",
            }:
                raise ValueError("Route-B composition_mode is invalid")
            target_components = tuple(
                str(value)
                for value in brief.get(
                    "target_components",
                    graph_group.get("components", ()),
                )
            )
            group_contract = (
                "COMPOSITION-GROUP CONTRACT: preserve the requested spatial structure and "
                "narrative purpose exactly; spanning sources must read as one continuous "
                "elongated subject, grouped sources as coordinated reusable units, and "
                "independent sources as one component-specific mark. "
                if group_id
                else ""
            )
            jobs.append(
                RouteImageJob(
                    job_id=f"{asset_id}{direction_suffix}",
                    route="B",
                    semantic_role=role,
                    prompt=(
                        "Use case: stylized-concept. Asset type: game weapon-skin "
                        f"source for later UV-aware composition. {prompt} {direction_prompt}"
                        f"{_SOURCE_ASSET_CONTRACT}{group_contract}"
                        f"{_ROLE_CONTRACTS.get(role, '')} "
                        + (
                            "Output only the landscape 2D source artwork, approximately 16:9, "
                            if role == "master_artwork"
                            else "Output only the square 2D source artwork "
                        )
                        + "with no text, logo, watermark, "
                        "border, annotation, or explanation."
                    ),
                    output_name=f"route_b_{output_token}.png",
                    composition_group_id=group_id,
                    composition_mode=composition_mode,
                    target_components=target_components,
                )
            )
    return tuple(jobs)
