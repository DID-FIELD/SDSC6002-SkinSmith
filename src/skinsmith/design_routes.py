from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Any, Mapping

from .style_planner import HEX_COLOR, StylePack


GROUP_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
COMPOSITION_MODES = {"spanning", "grouped", "independent", "background"}
WEAPON_SURFACES = {"left", "right", "top"}


def _strings(data: Mapping[str, Any], key: str) -> tuple[str, ...]:
    values = data.get(key)
    if not isinstance(values, list) or not values:
        raise ValueError(f"{key} must be a non-empty list")
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise ValueError(f"{key} must contain non-empty strings")
    return tuple(value.strip() for value in values)


@dataclass(frozen=True)
class ThemeElement:
    element_id: str
    display_name: str
    semantic_role: str
    generation_description: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ThemeElement":
        for key in ("element_id", "display_name", "semantic_role", "generation_description"):
            if not isinstance(data.get(key), str) or not str(data[key]).strip():
                raise ValueError(f"theme element {key} must be a non-empty string")
        role = str(data["semantic_role"]).strip()
        if role not in {"hero", "secondary", "connector", "background"}:
            raise ValueError(f"unsupported theme element role: {role}")
        return cls(
            element_id=str(data["element_id"]).strip(),
            display_name=str(data["display_name"]).strip(),
            semantic_role=role,
            generation_description=str(data["generation_description"]).strip(),
        )


@dataclass(frozen=True)
class ComponentStory:
    component: str
    narrative_role: str
    element_ids: tuple[str, ...]
    prominence: float
    detail_density: float

    @classmethod
    def from_dict(cls, component: str, data: Mapping[str, Any]) -> "ComponentStory":
        role = data.get("narrative_role")
        if not isinstance(role, str) or not role.strip():
            raise ValueError(f"{component}.narrative_role must be a non-empty string")
        prominence = float(data.get("prominence", 0.5))
        detail_density = float(data.get("detail_density", 0.5))
        if not 0.0 <= prominence <= 1.0 or not 0.0 <= detail_density <= 1.0:
            raise ValueError(f"{component} prominence/detail_density must be in [0, 1]")
        return cls(
            component=component,
            narrative_role=role.strip(),
            element_ids=_strings(data, "element_ids"),
            prominence=prominence,
            detail_density=detail_density,
        )


@dataclass(frozen=True)
class ThemeCompositionGroup:
    group_id: str
    composition_mode: str
    semantic_role: str
    element_ids: tuple[str, ...]
    components: tuple[str, ...]
    narrative_role: str
    surfaces: tuple[str, ...]
    mirror_on_right: bool
    allow_muzzle_focus: bool

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
        *,
        target_components: tuple[str, ...],
        element_roles: Mapping[str, str],
    ) -> "ThemeCompositionGroup":
        group_id = str(data.get("group_id", "")).strip()
        if not GROUP_ID.fullmatch(group_id):
            raise ValueError(
                "composition group_id must use lowercase letters, digits, underscores, or hyphens"
            )
        mode = str(data.get("composition_mode", "")).strip()
        if mode not in COMPOSITION_MODES:
            raise ValueError(f"unsupported composition mode: {mode}")
        element_ids = _strings(data, "element_ids")
        unknown_elements = set(element_ids) - element_roles.keys()
        if unknown_elements:
            raise ValueError(
                f"composition group references unknown elements: {sorted(unknown_elements)}"
            )
        roles = {element_roles[element_id] for element_id in element_ids}
        if len(roles) != 1:
            raise ValueError("one composition group must use elements from one semantic role")
        semantic_role = next(iter(roles))
        if mode == "background" and semantic_role != "background":
            raise ValueError("background composition groups must use background elements")
        if mode != "background" and semantic_role == "background":
            raise ValueError("background elements require background composition mode")
        components = _strings(data, "components")
        unknown_components = set(components) - set(target_components)
        if unknown_components:
            raise ValueError(
                f"composition group references unknown components: {sorted(unknown_components)}"
            )
        if mode == "independent" and len(components) != 1:
            raise ValueError("independent composition groups must target exactly one component")
        if mode == "spanning" and len(components) < 2:
            raise ValueError("spanning composition groups must target at least two components")
        narrative_role = str(data.get("narrative_role", "")).strip()
        if not narrative_role:
            raise ValueError("composition group narrative_role must not be empty")
        surfaces = _strings(data, "surfaces")
        if not set(surfaces) <= WEAPON_SURFACES:
            raise ValueError("composition group surfaces must use left, right, or top")
        allow_muzzle_focus = bool(data.get("allow_muzzle_focus", False))
        if allow_muzzle_focus and "barrel_muzzle" not in components:
            raise ValueError(
                "allow_muzzle_focus requires barrel_muzzle in the composition group"
            )
        return cls(
            group_id=group_id,
            composition_mode=mode,
            semantic_role=semantic_role,
            element_ids=element_ids,
            components=components,
            narrative_role=narrative_role,
            surfaces=surfaces,
            mirror_on_right=bool(data.get("mirror_on_right", True)),
            allow_muzzle_focus=allow_muzzle_focus,
        )


@dataclass(frozen=True)
class ThemePack:
    theme_id: str
    display_name: str
    generation_label: str
    match_terms: tuple[str, ...]
    concept: str
    narrative: str
    default_style_id: str
    target_components: tuple[str, ...]
    palette: tuple[str, ...]
    elements: tuple[ThemeElement, ...]
    pattern_notes: tuple[str, ...]
    component_story: tuple[ComponentStory, ...]
    composition_groups: tuple[ThemeCompositionGroup, ...]
    evaluation_criteria: tuple[str, ...]
    reference_policy: str
    source_path: Path

    @classmethod
    def load(cls, path: Path) -> "ThemePack":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data, path)

    @classmethod
    def from_dict(
        cls, data: Mapping[str, Any], source_path: Path | None = None
    ) -> "ThemePack":
        source_path = Path(source_path) if source_path is not None else Path("<generated-theme>")
        for key in (
            "theme_id",
            "display_name",
            "generation_label",
            "concept",
            "narrative",
            "default_style_id",
            "reference_policy",
        ):
            if not isinstance(data.get(key), str) or not str(data[key]).strip():
                raise ValueError(f"{key} must be a non-empty string")

        palette = _strings(data, "palette")
        if not all(HEX_COLOR.fullmatch(color) for color in palette):
            raise ValueError("theme palette entries must use #RRGGBB")

        element_values = data.get("elements")
        if not isinstance(element_values, list) or not element_values:
            raise ValueError("elements must be a non-empty list")
        elements = tuple(ThemeElement.from_dict(item) for item in element_values)
        element_ids = [element.element_id for element in elements]
        if len(element_ids) != len(set(element_ids)):
            raise ValueError("theme element ids must be unique")
        roles = {element.semantic_role for element in elements}
        if not {"hero", "connector", "background"} <= roles:
            raise ValueError("theme must define hero, connector, and background elements")

        target_components = _strings(data, "target_components")
        if len(target_components) != len(set(target_components)):
            raise ValueError("target_components must be unique")
        story_values = data.get("component_story")
        if not isinstance(story_values, dict):
            raise ValueError("component_story must be an object")
        missing = set(target_components) - story_values.keys()
        if missing:
            raise ValueError(f"component_story is missing: {sorted(missing)}")
        extra = story_values.keys() - set(target_components)
        if extra:
            raise ValueError(f"component_story has undeclared components: {sorted(extra)}")
        component_story = tuple(
            ComponentStory.from_dict(component, story_values[component])
            for component in target_components
        )
        known = set(element_ids)
        referenced = {element_id for item in component_story for element_id in item.element_ids}
        unknown = referenced - known
        if unknown:
            raise ValueError(f"component_story references unknown elements: {sorted(unknown)}")
        group_values = data.get("composition_groups", [])
        if not isinstance(group_values, list):
            raise ValueError("composition_groups must be an array when provided")
        element_roles = {
            element.element_id: element.semantic_role for element in elements
        }
        composition_groups = tuple(
            ThemeCompositionGroup.from_dict(
                item,
                target_components=target_components,
                element_roles=element_roles,
            )
            for item in group_values
        )
        if composition_groups:
            group_ids = [group.group_id for group in composition_groups]
            if len(group_ids) != len(set(group_ids)):
                raise ValueError("composition group ids must be unique")
            assigned = [
                element_id
                for group in composition_groups
                for element_id in group.element_ids
            ]
            if len(assigned) != len(set(assigned)):
                raise ValueError(
                    "each theme element may belong to only one composition group"
                )
            missing_elements = known - set(assigned)
            if missing_elements:
                raise ValueError(
                    f"composition groups are missing elements: {sorted(missing_elements)}"
                )

        return cls(
            theme_id=str(data["theme_id"]).strip(),
            display_name=str(data["display_name"]).strip(),
            generation_label=str(data["generation_label"]).strip(),
            match_terms=_strings(data, "match_terms"),
            concept=str(data["concept"]).strip(),
            narrative=str(data["narrative"]).strip(),
            default_style_id=str(data["default_style_id"]).strip(),
            target_components=target_components,
            palette=palette,
            elements=elements,
            pattern_notes=_strings(data, "pattern_notes"),
            component_story=component_story,
            composition_groups=composition_groups,
            evaluation_criteria=_strings(data, "evaluation_criteria"),
            reference_policy=str(data["reference_policy"]).strip(),
            source_path=source_path,
        )


class ThemeLibrary:
    def __init__(self, themes: tuple[ThemePack, ...]) -> None:
        if not themes:
            raise ValueError("theme library must contain at least one theme")
        ids = [theme.theme_id for theme in themes]
        if len(ids) != len(set(ids)):
            raise ValueError("theme ids must be unique")
        self.themes = themes

    @classmethod
    def load_directory(cls, directory: Path) -> "ThemeLibrary":
        return cls(tuple(ThemePack.load(path) for path in sorted(Path(directory).glob("*.json"))))

    def resolve(self, brief: str, requested: str = "auto") -> ThemePack:
        request = requested.casefold().removesuffix(".json")
        if request != "auto":
            for theme in self.themes:
                aliases = {
                    theme.source_path.stem.casefold(),
                    theme.theme_id.casefold(),
                    theme.display_name.casefold(),
                    *(term.casefold() for term in theme.match_terms),
                }
                if request in aliases:
                    return theme
            raise ValueError(f"unknown theme pack: {requested}")
        normalized = brief.casefold()
        scored = [
            (sum(1 for term in theme.match_terms if term.casefold() in normalized), theme)
            for theme in self.themes
        ]
        score = max(value for value, _ in scored)
        if score == 0:
            raise ValueError("no theme pack matches the brief")
        return sorted(
            (theme for value, theme in scored if value == score), key=lambda item: item.theme_id
        )[0]


@dataclass(frozen=True)
class AssetCreativeProfile:
    asset_id: str
    weapon_type: str
    silhouette_notes: tuple[str, ...]
    component_anchors: Mapping[str, tuple[float, float]]
    component_functions: Mapping[str, str]
    source_path: Path

    @classmethod
    def load(cls, path: Path) -> "AssetCreativeProfile":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("asset_id", "weapon_type"):
            if not isinstance(data.get(key), str) or not str(data[key]).strip():
                raise ValueError(f"{key} must be a non-empty string")
        anchors = data.get("component_anchors")
        functions = data.get("component_functions")
        if not isinstance(anchors, dict) or not anchors:
            raise ValueError("component_anchors must be a non-empty object")
        if not isinstance(functions, dict) or set(functions) != set(anchors):
            raise ValueError("component_functions must exactly match component_anchors")
        normalized_anchors: dict[str, tuple[float, float]] = {}
        for component, values in anchors.items():
            if not isinstance(values, list) or len(values) != 2:
                raise ValueError(f"{component} anchor must contain two values")
            anchor = tuple(float(value) for value in values)
            if not all(0.0 <= value <= 1.0 for value in anchor):
                raise ValueError(f"{component} anchor must be normalized")
            normalized_anchors[str(component)] = anchor
        if not all(isinstance(value, str) and value.strip() for value in functions.values()):
            raise ValueError("component_functions values must be non-empty strings")
        return cls(
            asset_id=str(data["asset_id"]).strip(),
            weapon_type=str(data["weapon_type"]).strip(),
            silhouette_notes=_strings(data, "silhouette_notes"),
            component_anchors=normalized_anchors,
            component_functions={str(key): str(value).strip() for key, value in functions.items()},
            source_path=path,
        )

    def compiler_context(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "weapon_type": self.weapon_type,
            "silhouette_notes": list(self.silhouette_notes),
            "components": [
                {
                    "component": component,
                    "function": self.component_functions[component],
                    "weapon_space_anchor": list(anchor),
                }
                for component, anchor in self.component_anchors.items()
            ],
        }


@dataclass(frozen=True)
class ThemeCompileResult:
    theme: ThemePack
    source_mode: str
    backend_id: str | None
    compiled_theme_path: str


ThemeSynthesisBackend = Callable[[str, AssetCreativeProfile], Mapping[str, Any]]


class RecordedAgentThemeBackend:
    """Replay one preserved creative-agent response with strict input binding."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.record = json.loads(self.path.read_text(encoding="utf-8"))
        for key in ("recorded_brief", "asset_id", "backend_id", "theme"):
            if key not in self.record:
                raise ValueError(f"recorded theme backend is missing {key}")
        if not isinstance(self.record["theme"], dict):
            raise ValueError("recorded theme must be an object")

    @property
    def backend_id(self) -> str:
        return str(self.record["backend_id"])

    def __call__(self, brief: str, asset: AssetCreativeProfile) -> Mapping[str, Any]:
        if brief.strip() != str(self.record["recorded_brief"]).strip():
            raise ValueError("recorded theme brief does not match the requested brief")
        if asset.asset_id != str(self.record["asset_id"]):
            raise ValueError("recorded theme asset does not match the target asset")
        return dict(self.record["theme"])


class ThemeCompiler:
    """Reuse cached themes or synthesize and validate a new one for the target weapon."""

    def __init__(
        self,
        library: ThemeLibrary,
        synthesis_backend: ThemeSynthesisBackend | None = None,
        *,
        backend_id: str | None = None,
    ) -> None:
        self.library = library
        self.synthesis_backend = synthesis_backend
        self.backend_id = backend_id

    def compile(
        self,
        brief: str,
        asset: AssetCreativeProfile,
        *,
        requested_theme: str = "auto",
        output_path: Path | None = None,
    ) -> ThemeCompileResult:
        brief = brief.strip()
        if not brief:
            raise ValueError("brief must not be empty")
        cached: ThemePack | None = None
        try:
            cached = self.library.resolve(brief, requested_theme)
        except ValueError:
            cached = None
        if cached is not None and set(cached.target_components) == set(asset.component_anchors):
            return ThemeCompileResult(
                theme=cached,
                source_mode="library",
                backend_id=None,
                compiled_theme_path=str(cached.source_path),
            )

        if self.synthesis_backend is None:
            reason = "unknown theme" if cached is None else "cached theme does not match target weapon"
            raise ValueError(f"{reason}; a creative synthesis backend is required")

        data = dict(self.synthesis_backend(brief, asset))
        data["target_components"] = list(asset.component_anchors)
        path = Path(output_path) if output_path is not None else Path("<generated-theme>")
        if output_path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        theme = ThemePack.from_dict(data, path)
        if set(theme.target_components) != set(asset.component_anchors):
            raise ValueError("generated theme components do not match target weapon")
        return ThemeCompileResult(
            theme=theme,
            source_mode="generated",
            backend_id=self.backend_id or type(self.synthesis_backend).__name__,
            compiled_theme_path=str(path),
        )


@dataclass(frozen=True)
class PatternDesignPlan:
    route: str
    design_object: str
    brief: str
    theme_id: str
    style_id: str
    palette: tuple[str, ...]
    element_ids: tuple[str, ...]
    density_strategy: str
    source_canvas: tuple[int, int]
    generation_prompt: str
    constraints: tuple[str, ...]
    required_outputs: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedAssetBrief:
    asset_id: str
    semantic_role: str
    element_ids: tuple[str, ...]
    source_canvas: tuple[int, int]
    background_policy: str
    generation_prompt: str
    composition_group_id: str | None = None
    composition_mode: str | None = None
    target_components: tuple[str, ...] = ()


@dataclass(frozen=True)
class WeaponComponentPlacement:
    component: str
    canvas_center: tuple[float, float]
    narrative_role: str
    element_ids: tuple[str, ...]
    prominence: float
    detail_density: float


@dataclass(frozen=True)
class CompositionGroupPlan:
    group_id: str
    composition_mode: str
    semantic_role: str
    asset_id: str
    element_ids: tuple[str, ...]
    components: tuple[str, ...]
    narrative_role: str
    surfaces: tuple[str, ...]
    mirror_on_right: bool
    allow_muzzle_focus: bool


@dataclass(frozen=True)
class CompositionRelationPlan:
    source_group_id: str
    target_group_id: str
    relation: str
    shared_components: tuple[str, ...]


@dataclass(frozen=True)
class CompositionGraphPlan:
    strategy: str
    groups: tuple[CompositionGroupPlan, ...]
    relations: tuple[CompositionRelationPlan, ...]


@dataclass(frozen=True)
class WeaponThemeDesignPlan:
    route: str
    design_object: str
    brief: str
    theme_id: str
    style_id: str
    palette: tuple[str, ...]
    focal_component: str
    source_square_semantics: str
    final_square_semantics: str
    asset_briefs: tuple[GeneratedAssetBrief, ...]
    component_layout: tuple[WeaponComponentPlacement, ...]
    composition_graph: CompositionGraphPlan
    composition_prompt: str
    pipeline: tuple[str, ...]
    constraints: tuple[str, ...]
    required_outputs: tuple[str, ...]


@dataclass(frozen=True)
class RefinementDesignPlan:
    route: str
    base_route: str
    inputs: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    acceptance_rule: str
    required_outputs: tuple[str, ...]


@dataclass(frozen=True)
class RouteDesignBundle:
    brief: str
    theme_name: str
    style_name: str
    pattern: PatternDesignPlan
    weapon_theme: WeaponThemeDesignPlan
    refinement: RefinementDesignPlan
    invariants: tuple[str, ...]
    theme_pack_path: str
    style_pack_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PatternDesigner:
    """Plan Route A as a crop-tolerant, dense, tileable template skin."""

    def design(self, brief: str, theme: ThemePack, style: StylePack) -> PatternDesignPlan:
        elements = ", ".join(element.generation_description for element in theme.elements)
        vocabulary = ", ".join(style.visual_vocabulary)
        notes = "; ".join(theme.pattern_notes)
        avoid = ", ".join(style.avoid)
        prompt = (
            f"Create an original dense all-over seamless template pattern for: {brief}. "
            f"Theme elements: {elements}. Style language: {vocabulary}. Palette: {', '.join(theme.palette)}. "
            f"Pattern logic: {notes}. Every crop must remain visually complete; repeat partial elements across "
            f"opposite edges; use many overlapping elements at varied scales; no unique hero or weapon-aware placement. "
            f"Avoid: {avoid}."
        )
        return PatternDesignPlan(
            route="A",
            design_object="tileable_template_pattern",
            brief=brief,
            theme_id=theme.theme_id,
            style_id=style.style_id,
            palette=theme.palette,
            element_ids=tuple(element.element_id for element in theme.elements),
            density_strategy="dense_all_over_with_varied_scale_and_crop_tolerance",
            source_canvas=(1024, 1024),
            generation_prompt=prompt,
            constraints=(
                "square source is the actual design object",
                "seamless on all four edges",
                "arbitrary crops remain complete",
                "no single irreplaceable focal subject",
                "must be reviewed on AK-47 left/right/top previews",
            ),
            required_outputs=(
                "source_pattern_square",
                "three_by_three_tile_preview",
                "mapped_uv_texture",
                "ak47_left_preview",
                "ak47_right_preview",
                "ak47_top_preview",
            ),
        )


class WeaponThemeDesigner:
    """Plan Route B as one master artwork or an optional component graph."""

    def __init__(
        self,
        component_anchors: Mapping[str, tuple[float, float]],
        *,
        route_b_strategy: str = "master_artwork",
    ) -> None:
        if not component_anchors:
            raise ValueError("component anchors must not be empty")
        if route_b_strategy not in {
            "master_artwork",
            "composition_graph",
            "legacy_semantic_roles",
        }:
            raise ValueError("unsupported Route-B strategy")
        self.route_b_strategy = route_b_strategy
        self.components = tuple(component_anchors)
        self.component_anchors = {
            component: tuple(float(value) for value in component_anchors[component])
            for component in self.components
        }
        if not all(
            len(anchor) == 2 and all(0.0 <= value <= 1.0 for value in anchor)
            for anchor in self.component_anchors.values()
        ):
            raise ValueError("component anchors must be normalized 2D coordinates")

    def design(self, brief: str, theme: ThemePack, style: StylePack) -> WeaponThemeDesignPlan:
        story_components = {story.component for story in theme.component_story}
        if story_components != set(self.components):
            raise ValueError("theme component story must match the target asset anchors")
        placements = tuple(
            WeaponComponentPlacement(
                component=story.component,
                canvas_center=self.component_anchors[story.component],
                narrative_role=story.narrative_role,
                element_ids=story.element_ids,
                prominence=story.prominence,
                detail_density=story.detail_density,
            )
            for story in theme.component_story
        )
        if self.route_b_strategy == "master_artwork":
            graph = CompositionGraphPlan(
                strategy="master_artwork",
                groups=(),
                relations=(),
            )
            assets = (self._master_artwork_brief(theme, style),)
        elif self.route_b_strategy == "composition_graph" and theme.composition_groups:
            graph = self._composition_graph(theme)
            assets = tuple(
                self._group_asset_brief(theme, style, group)
                for group in theme.composition_groups
            )
        else:
            graph = CompositionGraphPlan(
                strategy="legacy_semantic_roles",
                groups=(),
                relations=(),
            )
            assets = tuple(
                self._asset_brief(theme, style, role)
                for role in ("hero", "secondary", "connector", "background")
            )
        story_text = "; ".join(
            f"{item.component} at {item.canvas_center}: {item.narrative_role} "
            f"using {', '.join(item.element_ids)}, prominence {item.prominence:.2f}, "
            f"detail {item.detail_density:.2f}"
            for item in placements
        )
        group_text = (
            "one dense master artwork fitted across the complete continuous weapon canvas"
            if graph.strategy == "master_artwork"
            else
            "; ".join(
                f"{group.group_id} [{group.composition_mode}] spans "
                f"{', '.join(group.components)}: {group.narrative_role}"
                for group in graph.groups
            )
            if graph.groups
            else "legacy hero/secondary/connector/background hierarchy"
        )
        muzzle_focus = (
            graph.strategy == "master_artwork"
            or any(group.allow_muzzle_focus for group in graph.groups)
        )
        muzzle_instruction = (
            "The brief explicitly assigns a focal object to the muzzle, so do not apply the "
            "default quiet-muzzle fade. "
            if muzzle_focus
            else "Keep barrel/muzzle intentionally quiet unless a composition group explicitly "
            "overrides it. "
        )
        if graph.strategy == "master_artwork":
            prompt = (
                f"Create one dense whole-canvas master artwork for {brief}. Theme narrative: "
                f"{theme.narrative}. Style: {style.summary}. Use the complete palette and visual "
                "language across the image. The artwork must remain attractive under arbitrary "
                "cropping and must provide useful detail throughout the canvas. It will be fitted "
                "to continuous left/right/top weapon canvases and automatically cut into the "
                "fragmented OBJ-derived UV atlas. Do not design separate component stickers and "
                "do not require a named motif part to land on a named weapon component."
            )
        else:
            prompt = (
                f"Design a coherent whole-weapon composition for {brief}. Theme narrative: {theme.narrative}. "
                f"Style: {style.summary}. Component story: {story_text}. Composition graph: {group_text}. "
                "Treat every spanning group as one continuous subject crossing its assigned components; "
                "treat grouped and independent groups as separate but thematically related design units. "
                f"{muzzle_instruction}"
                "The composition lives in continuous weapon space and will later be baked into a "
                "fragmented square UV atlas."
            )
        focal_component = max(placements, key=lambda item: item.prominence).component
        return WeaponThemeDesignPlan(
            route="B",
            design_object="weapon_space_theme_composition",
            brief=brief,
            theme_id=theme.theme_id,
            style_id=style.style_id,
            palette=theme.palette,
            focal_component=focal_component,
            source_square_semantics=(
                "one dense master artwork used as the continuous weapon-surface design"
                if graph.strategy == "master_artwork"
                else "generated theme elements with semantic roles, not a reusable pattern"
            ),
            final_square_semantics="fragmented UV-atlas storage of the weapon design, not a standalone picture",
            asset_briefs=assets,
            component_layout=placements,
            composition_graph=graph,
            composition_prompt=prompt,
            pipeline=(
                "generate one dense master artwork by default; preserve graph/legacy fallbacks for old bundles",
                "fit the artwork to continuous left/right/top weapon-space canvases",
                "bake weapon-space canvases through position/normal maps into one square UV atlas",
                "apply UV-edge safety correction",
                "render AK-47 left/right/top previews before accepting the candidate",
            ),
            constraints=(
                "do not tile one square pattern across all components",
                "default Route B uses one dense edge-to-edge master artwork, not isolated component stickers",
                "master artwork must remain visually useful under crop and across the full canvas",
                "do not require semantic subparts to land on predetermined components",
                "accept visual quality only from mapped multi-view previews",
            ),
            required_outputs=(
                "generated_square_source_assets",
                "weapon_space_left_canvas",
                "weapon_space_right_canvas",
                "weapon_space_top_canvas",
                "final_square_uv_atlas",
                "ak47_left_preview",
                "ak47_right_preview",
                "ak47_top_preview",
            ),
        )

    @staticmethod
    def _master_artwork_brief(
        theme: ThemePack,
        style: StylePack,
    ) -> GeneratedAssetBrief:
        descriptions = "; ".join(
            element.generation_description for element in theme.elements
        )
        notes = "; ".join(theme.pattern_notes)
        prompt = (
            f"Generate one original dense landscape master artwork, approximately 16:9, for the {theme.display_name} "
            f"weapon-skin theme. Theme content: {descriptions}. Narrative: {theme.narrative}. "
            f"Theme enrichment notes: {notes}. "
            f"Style: {style.summary}. Visual language: {', '.join(style.visual_vocabulary)}. "
            f"Palette: {', '.join(theme.palette)}. Fill the complete canvas with layered, "
            "high-quality, high-density visual information at several scales. Every large crop "
            "must remain attractive and richly detailed. Build a complete thematic world with "
            "many medium and small clusters: primary forms, related symbolic objects, environment, "
            "architecture or nature, atmospheric connectors, linework, and material texture. "
            "No single subject may dominate more than roughly 35% of the canvas width or height, "
            "and no subject may stretch across the full image width. Weave these elements through "
            "every region rather than arranging isolated stickers on empty space. Do not split "
            "it into component assets and do not reserve large plain or near-black areas. This "
            "image will be fitted to continuous weapon space and automatically cut into the "
            "OBJ-derived UV atlas. Do not draw a weapon, weapon mockup, UV layout, text, logo, "
            "watermark, frame, presentation board, or product render."
        )
        return GeneratedAssetBrief(
            asset_id=f"{theme.theme_id}_master_artwork",
            semantic_role="master_artwork",
            element_ids=tuple(element.element_id for element in theme.elements),
            source_canvas=(1536, 864),
            background_policy="dense opaque edge-to-edge master artwork",
            generation_prompt=prompt,
            composition_group_id="master_artwork",
            composition_mode="background",
            target_components=theme.target_components,
        )

    @staticmethod
    def _asset_brief(theme: ThemePack, style: StylePack, role: str) -> GeneratedAssetBrief:
        elements = tuple(element for element in theme.elements if element.semantic_role == role)
        descriptions = "; ".join(element.generation_description for element in elements)
        background = (
            "opaque square background layer"
            if role == "background"
            else "isolatable subject on a flat removable background"
        )
        prompt = (
            f"Generate an original square {role} asset for the {theme.display_name} weapon theme. "
            f"Content: {descriptions}. Style: {style.summary}. Visual language: "
            f"{', '.join(style.visual_vocabulary)}. Palette: {', '.join(theme.palette)}. "
            f"This is a semantic source asset for later weapon-space composition, not a seamless pattern, "
            f"not a weapon mockup, and not the final UV texture. Background policy: {background}."
        )
        return GeneratedAssetBrief(
            asset_id=f"{theme.theme_id}_{role}",
            semantic_role=role,
            element_ids=tuple(element.element_id for element in elements),
            source_canvas=(1024, 1024),
            background_policy=background,
            generation_prompt=prompt,
        )

    @staticmethod
    def _group_asset_brief(
        theme: ThemePack,
        style: StylePack,
        group: ThemeCompositionGroup,
    ) -> GeneratedAssetBrief:
        element_map = {element.element_id: element for element in theme.elements}
        descriptions = "; ".join(
            element_map[element_id].generation_description
            for element_id in group.element_ids
        )
        background = (
            "opaque square background layer"
            if group.semantic_role == "background"
            else "isolatable subject on a flat removable background"
        )
        mode_instruction = {
            "spanning": (
                "Create one continuous elongated subject whose anatomy or structure can cross "
                f"the following components without breaking: {', '.join(group.components)}."
            ),
            "grouped": (
                "Create one reusable thematic unit intended to appear as coordinated echoes on "
                f"these components: {', '.join(group.components)}."
            ),
            "independent": (
                f"Create one self-contained mark specifically for {group.components[0]}."
            ),
            "background": (
                "Create a quiet edge-to-edge material field shared across the complete weapon."
            ),
        }[group.composition_mode]
        prompt = (
            f"Generate an original square source for composition group {group.group_id} in the "
            f"{theme.display_name} weapon theme. Content: {descriptions}. Narrative purpose: "
            f"{group.narrative_role}. {mode_instruction} Style: {style.summary}. Visual language: "
            f"{', '.join(style.visual_vocabulary)}. Palette: {', '.join(theme.palette)}. "
            "This source will be placed in continuous weapon space before UV baking; do not draw "
            "a weapon, UV layout, component outline, mockup, text, or logo. "
            f"Background policy: {background}."
        )
        return GeneratedAssetBrief(
            asset_id=f"{theme.theme_id}_{group.group_id}",
            semantic_role=group.semantic_role,
            element_ids=group.element_ids,
            source_canvas=(1024, 1024),
            background_policy=background,
            generation_prompt=prompt,
            composition_group_id=group.group_id,
            composition_mode=group.composition_mode,
            target_components=group.components,
        )

    @staticmethod
    def _composition_graph(theme: ThemePack) -> CompositionGraphPlan:
        groups = tuple(
            CompositionGroupPlan(
                group_id=group.group_id,
                composition_mode=group.composition_mode,
                semantic_role=group.semantic_role,
                asset_id=f"{theme.theme_id}_{group.group_id}",
                element_ids=group.element_ids,
                components=group.components,
                narrative_role=group.narrative_role,
                surfaces=group.surfaces,
                mirror_on_right=group.mirror_on_right,
                allow_muzzle_focus=group.allow_muzzle_focus,
            )
            for group in theme.composition_groups
        )
        relations: list[CompositionRelationPlan] = []
        for index, source in enumerate(groups):
            for target in groups[index + 1 :]:
                shared = tuple(
                    component
                    for component in source.components
                    if component in target.components
                )
                if shared:
                    relations.append(
                        CompositionRelationPlan(
                            source_group_id=source.group_id,
                            target_group_id=target.group_id,
                            relation="overlap_and_coordinate",
                            shared_components=shared,
                        )
                    )
        modes = {group.composition_mode for group in groups}
        strategy = (
            "hybrid"
            if len(modes - {"background"}) > 1
            else next(iter(modes - {"background"}), "background")
        )
        return CompositionGraphPlan(
            strategy=strategy,
            groups=groups,
            relations=tuple(relations),
        )


class RouteDesignPlanner:
    def __init__(
        self,
        component_anchors: Mapping[str, tuple[float, float]],
        *,
        route_b_strategy: str = "master_artwork",
    ) -> None:
        self.pattern_designer = PatternDesigner()
        self.weapon_designer = WeaponThemeDesigner(
            component_anchors,
            route_b_strategy=route_b_strategy,
        )

    def plan(self, brief: str, theme: ThemePack, style: StylePack) -> RouteDesignBundle:
        brief = brief.strip()
        if not brief:
            raise ValueError("brief must not be empty")
        pattern = self.pattern_designer.design(brief, theme, style)
        weapon = self.weapon_designer.design(brief, theme, style)
        refinement = RefinementDesignPlan(
            route="C",
            base_route="B",
            inputs=("Route-B UV atlas", "left/right/top renders", "semantic and technical scores"),
            allowed_actions=(
                "move or resize the receiver hero in weapon space",
                "reduce detail on one semantic component",
                "replace one theme asset while preserving the composition plan",
                "adjust connector flow or quiet-zone strength",
                "re-bake and re-render without changing unrelated components",
            ),
            acceptance_rule="accept only if hard constraints pass and agent score improves by at least 0.01; otherwise roll back",
            required_outputs=("diagnosis", "localized change record", "new previews", "accept_or_rollback decision"),
        )
        return RouteDesignBundle(
            brief=brief,
            theme_name=theme.display_name,
            style_name=style.display_name,
            pattern=pattern,
            weapon_theme=weapon,
            refinement=refinement,
            invariants=(
                "A and B share theme, style, palette, generation backend, resolution, and evaluation cameras",
                "A designs the square pattern; B designs the weapon and stores the result in a square UV atlas",
                "C is B plus bounded render-conditioned correction, not a third art style",
                "no candidate is shown as accepted without mapped weapon previews",
            ),
            theme_pack_path=str(theme.source_path),
            style_pack_path=str(style.source_path),
        )
