from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Any, Mapping

from .spec import DesignSpec


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
REQUIRED_COMPONENTS = (
    "stock",
    "receiver",
    "magazine",
    "pistol_grip",
    "handguard",
    "front_assembly",
    "barrel_muzzle",
)


def _strings(data: Mapping[str, Any], key: str) -> tuple[str, ...]:
    values = data.get(key)
    if not isinstance(values, list) or not values or not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError(f"{key} must be a non-empty list of strings")
    return tuple(value.strip() for value in values)


@dataclass(frozen=True)
class CandidateDirection:
    direction_id: str
    title: str
    concept: str
    motifs: tuple[str, ...]
    route_a_emphasis: str
    route_b_emphasis: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CandidateDirection":
        for key in ("direction_id", "title", "concept", "route_a_emphasis", "route_b_emphasis"):
            if not isinstance(data.get(key), str) or not str(data[key]).strip():
                raise ValueError(f"candidate_directions.{key} must be a non-empty string")
        return cls(
            direction_id=str(data["direction_id"]).strip(),
            title=str(data["title"]).strip(),
            concept=str(data["concept"]).strip(),
            motifs=_strings(data, "motifs"),
            route_a_emphasis=str(data["route_a_emphasis"]).strip(),
            route_b_emphasis=str(data["route_b_emphasis"]).strip(),
        )


@dataclass(frozen=True)
class RoutePolicy:
    objective: str
    composition_rules: tuple[str, ...]
    constraints: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], prefix: str) -> "RoutePolicy":
        objective = data.get("objective")
        if not isinstance(objective, str) or not objective.strip():
            raise ValueError(f"{prefix}.objective must be a non-empty string")
        return cls(
            objective=objective.strip(),
            composition_rules=_strings(data, "composition_rules"),
            constraints=_strings(data, "constraints"),
        )


@dataclass(frozen=True)
class StylePack:
    style_id: str
    display_name: str
    generation_label: str
    match_terms: tuple[str, ...]
    summary: str
    visual_vocabulary: tuple[str, ...]
    motifs: tuple[str, ...]
    palette: tuple[str, ...]
    material_cues: tuple[str, ...]
    composition_principles: tuple[str, ...]
    avoid: tuple[str, ...]
    route_a: RoutePolicy
    route_b: RoutePolicy
    component_roles: Mapping[str, str]
    candidate_directions: tuple[CandidateDirection, ...]
    evaluation_criteria: tuple[str, ...]
    reference_policy: str
    procedural_fallback_motif: str
    source_path: Path

    @classmethod
    def load(cls, path: Path) -> "StylePack":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data, path)

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
        source_path: Path | None = None,
        *,
        required_components: tuple[str, ...] = REQUIRED_COMPONENTS,
    ) -> "StylePack":
        source_path = Path(source_path) if source_path is not None else Path("<generated-style>")
        for key in ("style_id", "display_name", "generation_label", "summary", "reference_policy"):
            if not isinstance(data.get(key), str) or not str(data[key]).strip():
                raise ValueError(f"{key} must be a non-empty string")

        palette = _strings(data, "palette")
        if not all(HEX_COLOR.fullmatch(color) for color in palette):
            raise ValueError("palette entries must use #RRGGBB")

        component_roles = data.get("component_roles")
        if not isinstance(component_roles, dict):
            raise ValueError("component_roles must be an object")
        missing = set(required_components) - component_roles.keys()
        if missing:
            raise ValueError(f"component_roles is missing: {sorted(missing)}")
        extra = component_roles.keys() - set(required_components)
        if extra:
            raise ValueError(f"component_roles has undeclared components: {sorted(extra)}")
        if not all(
            isinstance(component_roles[key], str) and component_roles[key].strip()
            for key in required_components
        ):
            raise ValueError("every component role must be a non-empty string")

        directions_data = data.get("candidate_directions")
        if not isinstance(directions_data, list) or len(directions_data) < 3:
            raise ValueError("candidate_directions must contain at least three alternatives")
        directions = tuple(CandidateDirection.from_dict(item) for item in directions_data)
        direction_ids = [item.direction_id for item in directions]
        if len(direction_ids) != len(set(direction_ids)):
            raise ValueError("candidate direction ids must be unique")

        fallback = str(data.get("procedural_fallback_motif", "waves"))
        if fallback not in {"waves", "diagonal", "circuits"}:
            raise ValueError("procedural_fallback_motif must be waves, diagonal, or circuits")

        return cls(
            style_id=str(data["style_id"]).strip(),
            display_name=str(data["display_name"]).strip(),
            generation_label=str(data["generation_label"]).strip(),
            match_terms=_strings(data, "match_terms"),
            summary=str(data["summary"]).strip(),
            visual_vocabulary=_strings(data, "visual_vocabulary"),
            motifs=_strings(data, "motifs"),
            palette=palette,
            material_cues=_strings(data, "material_cues"),
            composition_principles=_strings(data, "composition_principles"),
            avoid=_strings(data, "avoid"),
            route_a=RoutePolicy.from_dict(data.get("route_a", {}), "route_a"),
            route_b=RoutePolicy.from_dict(data.get("route_b", {}), "route_b"),
            component_roles={key: str(component_roles[key]).strip() for key in required_components},
            candidate_directions=directions,
            evaluation_criteria=_strings(data, "evaluation_criteria"),
            reference_policy=str(data["reference_policy"]).strip(),
            procedural_fallback_motif=fallback,
            source_path=source_path,
        )


@dataclass(frozen=True)
class StyleCompileResult:
    style: StylePack
    source_mode: str
    backend_id: str | None
    compiled_style_path: str


StyleSynthesisBackend = Callable[
    [str, Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]
]


class StyleCompiler:
    """Reuse a cached style or synthesize a validated style for one theme and asset."""

    def __init__(
        self,
        library: "StyleLibrary",
        synthesis_backend: StyleSynthesisBackend | None = None,
        *,
        backend_id: str | None = None,
    ) -> None:
        self.library = library
        self.synthesis_backend = synthesis_backend
        self.backend_id = backend_id

    def compile(
        self,
        brief: str,
        theme_context: Mapping[str, Any],
        asset_context: Mapping[str, Any],
        *,
        requested_style: str = "auto",
        force_generate: bool = False,
        output_path: Path | None = None,
    ) -> StyleCompileResult:
        brief = brief.strip()
        if not brief:
            raise ValueError("brief must not be empty")
        component_values = asset_context.get("components")
        if not isinstance(component_values, list) or not component_values:
            raise ValueError("asset_context.components must be a non-empty list")
        component_names = tuple(
            str(item["component"])
            for item in component_values
            if isinstance(item, dict) and isinstance(item.get("component"), str)
        )
        if len(component_names) != len(component_values) or len(set(component_names)) != len(
            component_names
        ):
            raise ValueError("asset_context components must be unique named objects")

        cached: StylePack | None = None
        if not force_generate:
            request = requested_style
            if request == "auto" and isinstance(theme_context.get("default_style_id"), str):
                request = str(theme_context["default_style_id"])
            try:
                cached = self.library.resolve(brief, request)
            except ValueError:
                cached = None
        if cached is not None and set(cached.component_roles) == set(component_names):
            return StyleCompileResult(
                style=cached,
                source_mode="library",
                backend_id=None,
                compiled_style_path=str(cached.source_path),
            )

        if self.synthesis_backend is None:
            raise ValueError("a creative style synthesis backend is required")
        data = dict(self.synthesis_backend(brief, theme_context, asset_context))
        palette = theme_context.get("palette")
        if isinstance(palette, (list, tuple)) and palette:
            data["palette"] = list(palette)
        path = Path(output_path) if output_path is not None else Path("<generated-style>")
        if output_path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        style = StylePack.from_dict(data, path, required_components=component_names)
        return StyleCompileResult(
            style=style,
            source_mode="generated",
            backend_id=self.backend_id or type(self.synthesis_backend).__name__,
            compiled_style_path=str(path),
        )


@dataclass(frozen=True)
class PlannedCandidate:
    candidate_id: str
    title: str
    concept: str
    motifs: tuple[str, ...]
    generator_brief: str
    route_a_prompt: str
    route_b_prompt: str
    component_roles: Mapping[str, str]


@dataclass(frozen=True)
class ArtDirectionSpec:
    user_brief: str
    style_id: str
    style_name: str
    palette: tuple[str, ...]
    shared_constraints: tuple[str, ...]
    evaluation_criteria: tuple[str, ...]
    reference_policy: str
    procedural_fallback_motif: str
    candidates: tuple[PlannedCandidate, ...]
    style_pack_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def route_a_design_spec(self, index: int = 0, *, size: int = 512, seed: int = 20260714) -> DesignSpec:
        candidate = self.candidates[index]
        return DesignSpec(
            theme_name=f"{self.style_id}:{candidate.candidate_id}",
            description=candidate.generator_brief,
            palette=self.palette,
            motif=self.procedural_fallback_motif,
            size=size,
            candidate_count=1,
            seed=seed,
            prompt_motif=", ".join(candidate.motifs),
        )


class StylePlanner:
    """Expand a natural-language brief into shared Route-A/Route-B art directions."""

    def __init__(self, style_pack: StylePack) -> None:
        self.style_pack = style_pack

    def plan(self, user_brief: str, candidate_count: int = 4) -> ArtDirectionSpec:
        brief = user_brief.strip()
        if not brief:
            raise ValueError("user_brief must not be empty")
        if candidate_count < 1 or candidate_count > len(self.style_pack.candidate_directions):
            raise ValueError("candidate_count must fit the alternatives in the style pack")

        shared = (
            *self.style_pack.composition_principles,
            *(f"avoid {item}" for item in self.style_pack.avoid),
        )
        candidates = tuple(
            self._candidate(index, brief, direction)
            for index, direction in enumerate(self.style_pack.candidate_directions[:candidate_count], start=1)
        )
        return ArtDirectionSpec(
            user_brief=brief,
            style_id=self.style_pack.style_id,
            style_name=self.style_pack.display_name,
            palette=self.style_pack.palette,
            shared_constraints=shared,
            evaluation_criteria=self.style_pack.evaluation_criteria,
            reference_policy=self.style_pack.reference_policy,
            procedural_fallback_motif=self.style_pack.procedural_fallback_motif,
            candidates=candidates,
            style_pack_path=str(self.style_pack.source_path),
        )

    def _candidate(self, index: int, brief: str, direction: CandidateDirection) -> PlannedCandidate:
        vocabulary = ", ".join(self.style_pack.visual_vocabulary)
        motifs = ", ".join(direction.motifs)
        palette = ", ".join(self.style_pack.palette)
        materials = ", ".join(self.style_pack.material_cues)
        avoid = ", ".join(self.style_pack.avoid)
        route_a_rules = "; ".join(self.style_pack.route_a.composition_rules)
        route_b_rules = "; ".join(self.style_pack.route_b.composition_rules)
        route_a_constraints = ", ".join(self.style_pack.route_a.constraints)
        route_b_constraints = ", ".join(self.style_pack.route_b.constraints)
        roles = "; ".join(f"{name}: {role}" for name, role in self.style_pack.component_roles.items())
        route_a_prompt = (
            f"Brief: {brief}. Style: {self.style_pack.summary}. Direction: {direction.concept}. "
            f"Visual language: {vocabulary}. Motifs: {motifs}. Palette: {palette}. Material cues: {materials}. "
            f"Route A objective: {self.style_pack.route_a.objective}. {route_a_rules}. "
            f"Emphasis: {direction.route_a_emphasis}. Required: {route_a_constraints}. Avoid: {avoid}."
        )
        route_b_prompt = (
            f"Brief: {brief}. Style: {self.style_pack.summary}. Direction: {direction.concept}. "
            f"Visual language: {vocabulary}. Motifs: {motifs}. Palette: {palette}. Material cues: {materials}. "
            f"Route B objective: {self.style_pack.route_b.objective}. {route_b_rules}. "
            f"Component narrative: {roles}. Emphasis: {direction.route_b_emphasis}. "
            f"Required: {route_b_constraints}. Avoid: {avoid}."
        )
        generator_brief = (
            f"Original {self.style_pack.generation_label} design, {direction.concept}; "
            f"{motifs}; balanced medium-scale motifs and clear negative space"
        )
        return PlannedCandidate(
            candidate_id=f"candidate_{index:02d}_{direction.direction_id}",
            title=direction.title,
            concept=direction.concept,
            motifs=direction.motifs,
            generator_brief=generator_brief,
            route_a_prompt=route_a_prompt,
            route_b_prompt=route_b_prompt,
            component_roles=dict(self.style_pack.component_roles),
        )


class StyleLibrary:
    """Resolve a brief to one validated local style pack without a fixed theme."""

    def __init__(self, packs: tuple[StylePack, ...]) -> None:
        if not packs:
            raise ValueError("style library must contain at least one pack")
        ids = [pack.style_id for pack in packs]
        if len(ids) != len(set(ids)):
            raise ValueError("style ids must be unique")
        self.packs = packs

    @classmethod
    def load_directory(cls, directory: Path) -> "StyleLibrary":
        paths = sorted(Path(directory).glob("*.json"))
        return cls(tuple(StylePack.load(path) for path in paths))

    def resolve(self, brief: str, requested: str = "auto") -> StylePack:
        brief_normalized = brief.casefold()
        requested_normalized = requested.casefold().removesuffix(".json")
        if requested_normalized != "auto":
            for pack in self.packs:
                names = {
                    pack.source_path.stem.casefold(),
                    pack.style_id.casefold(),
                    pack.display_name.casefold(),
                    pack.generation_label.casefold(),
                    *(term.casefold() for term in pack.match_terms),
                }
                if requested_normalized in names:
                    return pack
            raise ValueError(f"unknown style pack: {requested}")

        scored = [
            (sum(1 for term in pack.match_terms if term.casefold() in brief_normalized), pack)
            for pack in self.packs
        ]
        best_score = max(score for score, _ in scored)
        if best_score == 0:
            available = ", ".join(pack.display_name for pack in self.packs)
            raise ValueError(
                f"no style pack matches the brief; add a knowledge pack or choose one of: {available}"
            )
        return sorted(
            (pack for score, pack in scored if score == best_score), key=lambda pack: pack.style_id
        )[0]
