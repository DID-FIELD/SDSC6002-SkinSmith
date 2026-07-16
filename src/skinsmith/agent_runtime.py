from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .style_planner import ArtDirectionSpec, StylePack


class AgentPhase(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    AWAITING_THEME = "awaiting_theme"
    AWAITING_DIRECTION = "awaiting_direction"
    AWAITING_ARTWORK = "awaiting_artwork"
    READY_TO_EXECUTE = "ready_to_execute"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentEventType(str, Enum):
    PLAN = "plan"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
    DECISION = "decision"
    ARTIFACT = "artifact"
    ERROR = "error"
    CHECKPOINT = "checkpoint"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    return value


@dataclass(frozen=True)
class AgentBudget:
    max_image_calls: int = 8
    max_role_retries: int = 4
    max_refinement_rounds: int = 1

    def __post_init__(self) -> None:
        if self.max_image_calls < 1:
            raise ValueError("max_image_calls must be positive")
        if self.max_role_retries < 0:
            raise ValueError("max_role_retries must not be negative")
        if self.max_refinement_rounds < 0:
            raise ValueError("max_refinement_rounds must not be negative")


@dataclass(frozen=True)
class AgentRunRequest:
    brief: str
    asset_id: str
    style_family: str | None = None
    candidate_budget: int = 4
    direction_choice: str | None = None
    budget: AgentBudget = field(default_factory=AgentBudget)

    def __post_init__(self) -> None:
        if not self.brief.strip():
            raise ValueError("brief must not be empty")
        if not self.asset_id.strip():
            raise ValueError("asset_id must not be empty")
        if self.candidate_budget not in (3, 4):
            raise ValueError("candidate_budget must be 3 or 4")


@dataclass(frozen=True)
class ArtDirectionCandidate:
    direction_id: str
    title: str
    concept: str
    style_family: str
    palette: tuple[str, ...]
    materials: tuple[str, ...]
    hero_strategy: str
    secondary_strategy: str
    connector_strategy: str
    background_strategy: str
    route_a_logic: str
    route_b_logic: str
    quiet_regions: tuple[str, ...]
    risks: tuple[str, ...]
    recommendation_reason: str
    motifs: tuple[str, ...] = ()
    world_elements: tuple[str, ...] = ()
    generator_brief: str = ""

    def __post_init__(self) -> None:
        required = {
            "direction_id": self.direction_id,
            "title": self.title,
            "concept": self.concept,
            "style_family": self.style_family,
            "hero_strategy": self.hero_strategy,
            "secondary_strategy": self.secondary_strategy,
            "connector_strategy": self.connector_strategy,
            "background_strategy": self.background_strategy,
            "route_a_logic": self.route_a_logic,
            "route_b_logic": self.route_b_logic,
            "recommendation_reason": self.recommendation_reason,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"art direction fields must not be empty: {missing}")
        if not self.palette:
            raise ValueError("art direction palette must not be empty")
        if not self.materials:
            raise ValueError("art direction materials must not be empty")


@dataclass(frozen=True)
class DesignContract:
    brief: str
    asset_id: str
    selected_direction: ArtDirectionCandidate
    locked_at: str
    constraints: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArtworkCandidate:
    candidate_id: str
    title: str
    variation: str
    source_path: str
    prompt: str
    preview_paths: tuple[str, ...]
    validation: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "variation": self.variation,
            "source_path": self.source_path,
            "prompt": self.prompt,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"artwork candidate fields must not be empty: {missing}")
        if len(self.preview_paths) < 3:
            raise ValueError("artwork candidate requires left/right/top mapped previews")


@dataclass(frozen=True)
class MemoryFact:
    key: str
    value: Any
    evidence: tuple[str, ...]
    recorded_at: str


@dataclass
class AgentMemory:
    facts: dict[str, MemoryFact] = field(default_factory=dict)

    def remember(self, key: str, value: Any, evidence: Sequence[str]) -> MemoryFact:
        if not key.strip():
            raise ValueError("memory key must not be empty")
        evidence_tuple = tuple(str(item) for item in evidence if str(item).strip())
        if not evidence_tuple:
            raise ValueError("memory facts require at least one evidence reference")
        fact = MemoryFact(key, value, evidence_tuple, _utc_now())
        self.facts[key] = fact
        return fact

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self.facts)

    @classmethod
    def load(cls, path: Path) -> "AgentMemory":
        path = Path(path)
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        facts = {
            key: MemoryFact(
                key=key,
                value=item["value"],
                evidence=tuple(item["evidence"]),
                recorded_at=item["recorded_at"],
            )
            for key, item in data.get("facts", {}).items()
        }
        return cls(facts)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"facts": self.to_dict()}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


@dataclass(frozen=True)
class AgentEvent:
    sequence: int
    timestamp: str
    phase: AgentPhase
    event_type: AgentEventType
    summary: str
    tool: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    run_id: str
    request: AgentRunRequest
    phase: AgentPhase = AgentPhase.CREATED
    theme_expansion: Mapping[str, Any] | None = None
    candidates: tuple[ArtDirectionCandidate, ...] = ()
    design_contract: DesignContract | None = None
    artwork_candidates: tuple[ArtworkCandidate, ...] = ()
    selected_artwork_id: str | None = None
    image_calls_used: int = 0
    role_retries_used: int = 0
    refinement_rounds_used: int = 0
    stop_reason: str | None = None


AgentTool = Callable[["AgentToolContext", Any], Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register(self, name: str, tool: AgentTool) -> None:
        if not name.strip():
            raise ValueError("tool name must not be empty")
        if name in self._tools:
            raise ValueError(f"tool is already registered: {name}")
        self._tools[name] = tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def call(self, name: str, context: "AgentToolContext", payload: Any) -> Any:
        try:
            tool = self._tools[name]
        except KeyError as error:
            raise KeyError(f"required Agent tool is not registered: {name}") from error
        return tool(context, payload)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))


@dataclass
class AgentToolContext:
    state: AgentState
    memory: AgentMemory
    output_dir: Path
    emit: Callable[..., AgentEvent]

    def consume_image_call(self, count: int = 1) -> None:
        if count < 1:
            raise ValueError("image call count must be positive")
        maximum = self.state.request.budget.max_image_calls
        if self.state.image_calls_used + count > maximum:
            raise RuntimeError(f"image-call budget exceeded ({maximum})")
        self.state.image_calls_used += count

    def consume_role_retry(self, count: int = 1) -> None:
        if count < 1:
            raise ValueError("role retry count must be positive")
        maximum = self.state.request.budget.max_role_retries
        if self.state.role_retries_used + count > maximum:
            raise RuntimeError(f"role-retry budget exceeded ({maximum})")
        self.state.role_retries_used += count

    def consume_refinement_round(self) -> None:
        maximum = self.state.request.budget.max_refinement_rounds
        if self.state.refinement_rounds_used + 1 > maximum:
            raise RuntimeError(f"refinement budget exceeded ({maximum})")
        self.state.refinement_rounds_used += 1


@dataclass(frozen=True)
class AgentRunResult:
    run_id: str
    status: str
    phase: AgentPhase
    request: AgentRunRequest
    theme_expansion: Mapping[str, Any] | None
    directions: tuple[ArtDirectionCandidate, ...]
    design_contract: DesignContract | None
    artwork_candidates: tuple[ArtworkCandidate, ...]
    selected_artwork_id: str | None
    artifacts: Mapping[str, Any]
    metrics: Mapping[str, Any]
    decision: Mapping[str, Any]
    events: tuple[AgentEvent, ...]
    checkpoint_path: str
    stop_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


def directions_from_style_plan(
    style: StylePack,
    plan: ArtDirectionSpec,
    *,
    style_family: str | None = None,
    route_b_strategy: str = "master_artwork",
    world_elements: Sequence[str] = (),
) -> tuple[ArtDirectionCandidate, ...]:
    if route_b_strategy not in {"master_artwork", "composition_graph"}:
        raise ValueError("unsupported Route-B direction strategy")
    family = (style_family or style.display_name).strip()
    enriched_world_elements = tuple(
        dict.fromkeys(
            (
                *world_elements,
                *style.motifs,
                *style.visual_vocabulary,
                *style.material_cues,
            )
        )
    )
    roles = dict(style.component_roles)
    risks = tuple(f"avoid {item}" for item in style.avoid[:3]) or (
        "preserve readability after UV mapping",
    )
    quiet = tuple(
        component
        for component, role in roles.items()
        if "quiet" in role.casefold() or component in {"barrel_muzzle"}
    )
    quiet = quiet or ("barrel_muzzle",)

    def master_route_logic(item: Any) -> str:
        vocabulary = ", ".join(style.visual_vocabulary)
        motifs = ", ".join(item.motifs)
        palette = ", ".join(plan.palette)
        materials = ", ".join(style.material_cues)
        avoid = ", ".join(style.avoid)
        return (
            f"Brief: {plan.user_brief}. Style: {style.summary}. Direction: {item.concept}. "
            f"Visual language: {vocabulary}. Motifs: {motifs}. Palette: {palette}. "
            f"Material cues: {materials}. Route B objective: generate one complete, dense, "
            "crop-robust master artwork, fit it across continuous left/right/top weapon space, "
            "then automatically cut and repack it through the OBJ-derived UV atlas. Distribute "
            "useful visual information at multiple scales across the full image; avoid large "
            "empty regions. Subject-part placement on named weapon components is not required "
            f"or evaluated. Avoid: {avoid}."
        )

    return tuple(
        ArtDirectionCandidate(
            direction_id=item.candidate_id,
            title=item.title,
            concept=item.concept,
            style_family=family,
            palette=tuple(plan.palette),
            materials=tuple(style.material_cues),
            hero_strategy=(
                "Dense multi-scale theme artwork whose large crops remain visually complete."
                if route_b_strategy == "master_artwork"
                else roles.get("receiver", item.concept)
            ),
            secondary_strategy=(
                "Distribute supporting motifs and material detail across the full canvas."
                if route_b_strategy == "master_artwork"
                else "; ".join(
                    f"{component}: {roles[component]}"
                    for component in ("stock", "magazine")
                    if component in roles
                )
            ),
            connector_strategy=(
                "Use continuous line, colour, and texture rhythm rather than component stickers."
                if route_b_strategy == "master_artwork"
                else "; ".join(
                    f"{component}: {roles[component]}"
                    for component in ("handguard", "front_assembly")
                    if component in roles
                )
            ),
            background_strategy=(
                "Resolve the background as an active material field with no large dead zones."
                if route_b_strategy == "master_artwork"
                else roles.get("pistol_grip", style.summary)
            ),
            route_a_logic=item.route_a_prompt,
            route_b_logic=(
                master_route_logic(item)
                if route_b_strategy == "master_artwork"
                else item.route_b_prompt
            ),
            quiet_regions=() if route_b_strategy == "master_artwork" else quiet,
            risks=risks,
            recommendation_reason=(
                f"Distinct {item.title} interpretation with explicit Route A and "
                + (
                    "crop-robust master-artwork Route B logic."
                    if route_b_strategy == "master_artwork"
                    else "whole-weapon composition-graph Route B logic."
                )
            ),
            motifs=tuple(item.motifs),
            world_elements=enriched_world_elements,
            generator_brief=item.generator_brief,
        )
        for item in plan.candidates
    )


class SkinSmithAgent:
    """Stateful orchestration runtime for planning and executing one skin-design run."""

    def __init__(
        self,
        workspace: Path,
        tools: ToolRegistry | None = None,
        memory: AgentMemory | None = None,
    ) -> None:
        self.workspace = Path(workspace)
        self.tools = tools or ToolRegistry()
        self.memory = memory or AgentMemory()
        self.state: AgentState | None = None
        self.events: list[AgentEvent] = []
        self.output_dir: Path | None = None

    def run(
        self,
        brief: str,
        asset_id: str,
        style_family: str | None = None,
        candidate_budget: int = 4,
        direction_choice: str | None = None,
        artwork_choice: str | None = None,
        *,
        theme_confirmed: bool = False,
        budget: AgentBudget | None = None,
        output_dir: Path | None = None,
    ) -> AgentRunResult:
        request = AgentRunRequest(
            brief=brief,
            asset_id=asset_id,
            style_family=style_family,
            candidate_budget=candidate_budget,
            direction_choice=direction_choice,
            budget=budget or AgentBudget(),
        )
        self._start(request, output_dir)
        try:
            if self.tools.has("expand_theme"):
                self._expand_theme()
                if not theme_confirmed:
                    self._transition(
                        AgentPhase.AWAITING_THEME,
                        AgentEventType.DECISION,
                        "Theme expansion confirmation is required before direction planning.",
                    )
                    return self._result("awaiting_theme")
                self._confirm_theme()
            self._plan_directions()
            if direction_choice is None:
                self._transition(
                    AgentPhase.AWAITING_DIRECTION,
                    AgentEventType.DECISION,
                    "Direction selection is required before generation.",
                )
                return self._result("awaiting_direction")
            self._lock_direction(direction_choice)
            if self.tools.has("generate_artwork_candidates"):
                self._generate_artwork_candidates()
                if artwork_choice is None:
                    return self._result("awaiting_artwork")
                self._lock_artwork(artwork_choice)
            if not self.tools.has("execute_design"):
                self._transition(
                    AgentPhase.READY_TO_EXECUTE,
                    AgentEventType.CHECKPOINT,
                    "Design contract locked; execution toolchain is not registered yet.",
                )
                return self._result("ready_to_execute")
            return self._execute()
        except Exception as error:
            if self.state is not None:
                self.state.phase = AgentPhase.FAILED
                self.state.stop_reason = str(error)
                self._emit(AgentEventType.ERROR, str(error))
                self._checkpoint()
            raise

    def resume(
        self,
        output_dir: Path,
        direction_choice: str | None = None,
        artwork_choice: str | None = None,
        *,
        theme_confirmed: bool = False,
    ) -> AgentRunResult:
        """Resume an awaiting/ready run from its persisted checkpoint."""

        self.output_dir = Path(output_dir)
        checkpoint_path = self.output_dir / "checkpoint.json"
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        self.state = self._state_from_dict(data["state"])
        self.events = tuple_to_events(data.get("events", ()))

        state = self._require_state()
        try:
            if state.phase == AgentPhase.AWAITING_THEME:
                if not theme_confirmed:
                    return self._result("awaiting_theme")
                self._confirm_theme()
                self._plan_directions()
                if direction_choice is None:
                    self._transition(
                        AgentPhase.AWAITING_DIRECTION,
                        AgentEventType.DECISION,
                        "Direction selection is required before generation.",
                    )
                    return self._result("awaiting_direction")
                self._lock_direction(direction_choice)
                if self.tools.has("generate_artwork_candidates"):
                    self._generate_artwork_candidates()
                    if artwork_choice is None:
                        return self._result("awaiting_artwork")
                    self._lock_artwork(artwork_choice)
            elif state.phase == AgentPhase.AWAITING_DIRECTION:
                if direction_choice is None:
                    return self._result("awaiting_direction")
                state.stop_reason = None
                self._lock_direction(direction_choice)
                if self.tools.has("generate_artwork_candidates"):
                    self._generate_artwork_candidates()
                    if artwork_choice is None:
                        return self._result("awaiting_artwork")
                    self._lock_artwork(artwork_choice)
            elif state.phase == AgentPhase.AWAITING_ARTWORK:
                if artwork_choice is None:
                    return self._result("awaiting_artwork")
                self._lock_artwork(artwork_choice)
            elif state.phase != AgentPhase.READY_TO_EXECUTE:
                raise RuntimeError(f"run cannot resume from phase {state.phase.value}")

            if not self.tools.has("execute_design"):
                state.phase = AgentPhase.READY_TO_EXECUTE
                state.stop_reason = "Design contract is locked; execution toolchain is not registered yet."
                self._emit(AgentEventType.CHECKPOINT, state.stop_reason)
                self._checkpoint()
                return self._result("ready_to_execute")
            return self._execute()
        except Exception as error:
            state.phase = AgentPhase.FAILED
            state.stop_reason = str(error)
            self._emit(AgentEventType.ERROR, str(error))
            self._checkpoint()
            raise

    def revise(
        self,
        output_dir: Path,
        retry_roles: Sequence[str],
        *,
        review_reasons: Mapping[str, str] | None = None,
        additional_image_calls: int = 0,
        reuse_latest_roles: Sequence[str] = (),
    ) -> AgentRunResult:
        """Reopen a completed run for evidence-backed role-local regeneration."""

        self.output_dir = Path(output_dir)
        checkpoint_path = self.output_dir / "checkpoint.json"
        data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        self.state = self._state_from_dict(data["state"])
        self.events = tuple_to_events(data.get("events", ()))
        state = self._require_state()
        roles = tuple(dict.fromkeys(str(role).strip() for role in retry_roles))
        if state.phase not in {AgentPhase.COMPLETED, AgentPhase.FAILED}:
            raise RuntimeError(f"run cannot be revised from phase {state.phase.value}")
        if state.design_contract is None:
            raise RuntimeError("completed run has no locked design contract")
        if not roles:
            raise ValueError("retry_roles must not be empty")
        if not self.tools.has("retry_roles"):
            raise RuntimeError("retry_roles Agent tool is not registered")
        if additional_image_calls < 0:
            raise ValueError("additional_image_calls must not be negative")
        if additional_image_calls:
            old_budget = state.request.budget
            new_budget = replace(
                old_budget,
                max_image_calls=old_budget.max_image_calls + additional_image_calls,
            )
            state.request = replace(state.request, budget=new_budget)
            self._emit(
                AgentEventType.DECISION,
                f"Extended image-call budget by {additional_image_calls}.",
                data={
                    "previous_max_image_calls": old_budget.max_image_calls,
                    "new_max_image_calls": new_budget.max_image_calls,
                },
            )
        try:
            state.phase = AgentPhase.EXECUTING
            state.stop_reason = None
            self._emit(
                AgentEventType.DECISION,
                f"Reopened completed run for role-local retry: {', '.join(roles)}.",
                data={"retry_roles": roles},
            )
            payload = self.tools.call(
                "retry_roles",
                self._context(),
                {
                    "contract": state.design_contract,
                    "roles": roles,
                    "review_reasons": dict(review_reasons or {}),
                    "reuse_latest_roles": tuple(reuse_latest_roles),
                },
            )
            if not isinstance(payload, Mapping):
                raise TypeError("retry_roles must return a mapping")
            state.phase = AgentPhase.COMPLETED
            self._emit(
                AgentEventType.DECISION,
                "Role-local revision completed and remapped.",
            )
            self._checkpoint()
            result = self._result(
                "completed",
                artifacts=payload.get("artifacts", {}),
                metrics=payload.get("metrics", {}),
                decision=payload.get("decision", {}),
            )
            self._write_json("agent_run_result.json", result)
            return result
        except Exception as error:
            state.phase = AgentPhase.FAILED
            state.stop_reason = str(error)
            self._emit(AgentEventType.ERROR, str(error))
            self._checkpoint()
            raise

    def _start(self, request: AgentRunRequest, output_dir: Path | None) -> None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
        self.output_dir = (
            Path(output_dir)
            if output_dir is not None
            else self.workspace / "runs" / "agent_runs" / run_id
        )
        self.output_dir.mkdir(parents=True, exist_ok=False)
        self.state = AgentState(run_id=run_id, request=request)
        self.events = []
        self._emit(AgentEventType.PLAN, "Agent run created from the user brief.")
        self._checkpoint()

    def _plan_directions(self) -> None:
        state = self._require_state()
        state.phase = AgentPhase.PLANNING
        context = self._context()
        self._emit(
            AgentEventType.TOOL_CALL,
            "Compile theme/style and propose art directions.",
            tool="plan_directions",
        )
        planning_payload: Any = state.request
        if state.theme_expansion is not None:
            planning_payload = {
                "request": state.request,
                "theme_expansion": state.theme_expansion,
            }
        raw = self.tools.call("plan_directions", context, planning_payload)
        candidates = tuple(raw)
        if (
            len(candidates) not in (3, 4)
            or len(candidates) > state.request.candidate_budget
        ):
            raise ValueError(
                f"planner returned {len(candidates)} directions; "
                f"expected 3-{state.request.candidate_budget}"
            )
        if len(candidates) != state.request.candidate_budget:
            state.request = replace(
                state.request,
                candidate_budget=len(candidates),
            )
            self._emit(
                AgentEventType.OBSERVATION,
                f"Adjusted candidate budget to {len(candidates)} available directions.",
                data={"candidate_budget": len(candidates)},
            )
        if not all(isinstance(item, ArtDirectionCandidate) for item in candidates):
            raise TypeError("plan_directions must return ArtDirectionCandidate records")
        ids = [item.direction_id for item in candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("art direction ids must be unique")
        concepts = {item.concept.casefold().strip() for item in candidates}
        if len(concepts) != len(candidates):
            raise ValueError("art direction concepts must be meaningfully distinct")
        state.candidates = candidates
        self._emit(
            AgentEventType.OBSERVATION,
            f"Planner produced {len(candidates)} validated art directions.",
            data={"direction_ids": ids},
        )
        self._write_json("directions.json", {"directions": candidates})
        self._checkpoint()

    def _expand_theme(self) -> None:
        state = self._require_state()
        state.phase = AgentPhase.PLANNING
        self._emit(
            AgentEventType.TOOL_CALL,
            "Expand the short theme into a validated visual world.",
            tool="expand_theme",
        )
        raw = self.tools.call("expand_theme", self._context(), state.request)
        if not isinstance(raw, Mapping):
            raise TypeError("expand_theme must return a mapping")
        required = ("theme_id", "display_name", "concept", "palette", "elements")
        missing = [key for key in required if not raw.get(key)]
        if missing:
            raise ValueError(f"theme expansion is missing required fields: {missing}")
        elements = raw.get("elements")
        if not isinstance(elements, Sequence) or isinstance(elements, (str, bytes)):
            raise TypeError("theme expansion elements must be a sequence")
        state.theme_expansion = dict(raw)
        self._emit(
            AgentEventType.OBSERVATION,
            f"Expanded theme {raw['display_name']} with {len(elements)} related elements.",
            data={
                "theme_id": raw["theme_id"],
                "element_count": len(elements),
                "source_mode": raw.get("source_mode"),
            },
        )
        self._write_json("theme_expansion.json", state.theme_expansion)
        self._checkpoint()

    def _confirm_theme(self) -> None:
        state = self._require_state()
        if state.theme_expansion is None:
            raise RuntimeError("theme expansion must exist before confirmation")
        state.stop_reason = None
        self._emit(
            AgentEventType.DECISION,
            f"Confirmed expanded theme {state.theme_expansion['theme_id']}.",
            data={"theme_id": state.theme_expansion["theme_id"]},
        )
        self._checkpoint()

    def _lock_direction(self, direction_choice: str) -> None:
        state = self._require_state()
        try:
            selected = next(
                item for item in state.candidates if item.direction_id == direction_choice
            )
        except StopIteration as error:
            available = ", ".join(item.direction_id for item in state.candidates)
            raise ValueError(
                f"unknown direction_choice {direction_choice!r}; available: {available}"
            ) from error
        state.design_contract = DesignContract(
            brief=state.request.brief,
            asset_id=state.request.asset_id,
            selected_direction=selected,
            locked_at=_utc_now(),
            constraints=(
                "do not silently change the selected concept",
                "Route A and Route B must share the locked palette and visual language",
                "accept final quality only from mapped multi-view previews",
            ),
        )
        state.stop_reason = None
        self._emit(
            AgentEventType.DECISION,
            f"Locked design direction {selected.direction_id}.",
            data={"direction_id": selected.direction_id},
        )
        self._write_json("design_contract.json", state.design_contract)
        self._checkpoint()

    def _generate_artwork_candidates(self) -> None:
        state = self._require_state()
        if state.design_contract is None:
            raise RuntimeError("design direction must be locked before artwork generation")
        self._emit(
            AgentEventType.TOOL_CALL,
            "Generate enriched master artworks and map every candidate to AK previews.",
            tool="generate_artwork_candidates",
        )
        raw = self.tools.call(
            "generate_artwork_candidates",
            self._context(),
            state.design_contract,
        )
        candidates = tuple(raw)
        if len(candidates) != state.request.candidate_budget:
            raise ValueError(
                f"artwork generator returned {len(candidates)} candidates; "
                f"expected {state.request.candidate_budget}"
            )
        if not all(isinstance(item, ArtworkCandidate) for item in candidates):
            raise TypeError(
                "generate_artwork_candidates must return ArtworkCandidate records"
            )
        ids = [item.candidate_id for item in candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("artwork candidate ids must be unique")
        state.artwork_candidates = candidates
        state.phase = AgentPhase.AWAITING_ARTWORK
        state.stop_reason = (
            "Select one candidate after comparing its original artwork and mapped "
            "left/right/top previews."
        )
        self._emit(
            AgentEventType.OBSERVATION,
            f"Generated and pre-mapped {len(candidates)} artwork candidates.",
            data={"artwork_candidate_ids": ids},
        )
        self._write_json(
            "artwork_candidates.json",
            {"artwork_candidates": candidates},
        )
        self._checkpoint()

    def _lock_artwork(self, artwork_choice: str) -> None:
        state = self._require_state()
        try:
            selected = next(
                item
                for item in state.artwork_candidates
                if item.candidate_id == artwork_choice
            )
        except StopIteration as error:
            available = ", ".join(
                item.candidate_id for item in state.artwork_candidates
            )
            raise ValueError(
                f"unknown artwork_choice {artwork_choice!r}; available: {available}"
            ) from error
        state.selected_artwork_id = selected.candidate_id
        state.phase = AgentPhase.READY_TO_EXECUTE
        state.stop_reason = None
        self._emit(
            AgentEventType.DECISION,
            f"Locked mapped artwork candidate {selected.candidate_id}.",
            data={
                "artwork_candidate_id": selected.candidate_id,
                "source_path": selected.source_path,
                "preview_paths": selected.preview_paths,
            },
        )
        self._checkpoint()

    def _execute(self) -> AgentRunResult:
        state = self._require_state()
        state.phase = AgentPhase.EXECUTING
        self._emit(
            AgentEventType.TOOL_CALL,
            "Execute the locked Route A/B generation and evaluation contract.",
            tool="execute_design",
        )
        selected_artwork = next(
            (
                item
                for item in state.artwork_candidates
                if item.candidate_id == state.selected_artwork_id
            ),
            None,
        )
        execution_payload: Any = state.design_contract
        if selected_artwork is not None:
            execution_payload = {
                "contract": state.design_contract,
                "artwork_candidate": selected_artwork,
            }
        payload = self.tools.call(
            "execute_design",
            self._context(),
            execution_payload,
        )
        if not isinstance(payload, Mapping):
            raise TypeError("execute_design must return a mapping")
        state.phase = AgentPhase.COMPLETED
        state.stop_reason = None
        self._emit(AgentEventType.DECISION, "Agent execution completed.")
        self._checkpoint()
        result = self._result(
            "completed",
            artifacts=payload.get("artifacts", {}),
            metrics=payload.get("metrics", {}),
            decision=payload.get("decision", {}),
        )
        self._write_json("agent_run_result.json", result)
        return result

    def _transition(
        self,
        phase: AgentPhase,
        event_type: AgentEventType,
        summary: str,
    ) -> None:
        state = self._require_state()
        state.phase = phase
        state.stop_reason = summary
        self._emit(event_type, summary)
        self._checkpoint()

    def _context(self) -> AgentToolContext:
        return AgentToolContext(
            state=self._require_state(),
            memory=self.memory,
            output_dir=self._require_output_dir(),
            emit=self._emit,
        )

    def _emit(
        self,
        event_type: AgentEventType,
        summary: str,
        *,
        tool: str | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> AgentEvent:
        event = AgentEvent(
            sequence=len(self.events) + 1,
            timestamp=_utc_now(),
            phase=self._require_state().phase,
            event_type=event_type,
            summary=summary,
            tool=tool,
            data=dict(data or {}),
        )
        self.events.append(event)
        events_path = self._require_output_dir() / "events.jsonl"
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(event), ensure_ascii=False) + "\n")
        return event

    def _checkpoint(self) -> None:
        state = self._require_state()
        self._write_json(
            "checkpoint.json",
            {
                "state": state,
                "events": self.events,
                "registered_tools": self.tools.names,
            },
        )

    def _write_json(self, name: str, value: Any) -> None:
        path = self._require_output_dir() / name
        path.write_text(
            json.dumps(_jsonable(value), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _result(
        self,
        status: str,
        *,
        artifacts: Mapping[str, Any] | None = None,
        metrics: Mapping[str, Any] | None = None,
        decision: Mapping[str, Any] | None = None,
    ) -> AgentRunResult:
        state = self._require_state()
        return AgentRunResult(
            run_id=state.run_id,
            status=status,
            phase=state.phase,
            request=state.request,
            theme_expansion=state.theme_expansion,
            directions=state.candidates,
            design_contract=state.design_contract,
            artwork_candidates=state.artwork_candidates,
            selected_artwork_id=state.selected_artwork_id,
            artifacts=dict(artifacts or {}),
            metrics=dict(metrics or {}),
            decision=dict(decision or {}),
            events=tuple(self.events),
            checkpoint_path=str(self._require_output_dir() / "checkpoint.json"),
            stop_reason=state.stop_reason,
        )

    def _require_state(self) -> AgentState:
        if self.state is None:
            raise RuntimeError("Agent run has not started")
        return self.state

    def _require_output_dir(self) -> Path:
        if self.output_dir is None:
            raise RuntimeError("Agent output directory is not initialized")
        return self.output_dir

    @staticmethod
    def _state_from_dict(data: Mapping[str, Any]) -> AgentState:
        request_data = dict(data["request"])
        request_data["budget"] = AgentBudget(**request_data["budget"])
        request = AgentRunRequest(**request_data)
        candidates = tuple(
            ArtDirectionCandidate(
                **{
                    **item,
                    "palette": tuple(item["palette"]),
                    "materials": tuple(item["materials"]),
                    "quiet_regions": tuple(item["quiet_regions"]),
                    "risks": tuple(item["risks"]),
                    "motifs": tuple(item.get("motifs", ())),
                    "world_elements": tuple(item.get("world_elements", ())),
                }
            )
            for item in data.get("candidates", ())
        )
        contract_data = data.get("design_contract")
        contract = None
        if contract_data is not None:
            selected = ArtDirectionCandidate(
                **{
                    **contract_data["selected_direction"],
                    "palette": tuple(contract_data["selected_direction"]["palette"]),
                    "materials": tuple(contract_data["selected_direction"]["materials"]),
                    "quiet_regions": tuple(
                        contract_data["selected_direction"]["quiet_regions"]
                    ),
                    "risks": tuple(contract_data["selected_direction"]["risks"]),
                    "motifs": tuple(
                        contract_data["selected_direction"].get("motifs", ())
                    ),
                    "world_elements": tuple(
                        contract_data["selected_direction"].get("world_elements", ())
                    ),
                }
            )
            contract = DesignContract(
                brief=contract_data["brief"],
                asset_id=contract_data["asset_id"],
                selected_direction=selected,
                locked_at=contract_data["locked_at"],
                constraints=tuple(contract_data.get("constraints", ())),
            )
        artwork_candidates = tuple(
            ArtworkCandidate(
                **{
                    **item,
                    "preview_paths": tuple(item.get("preview_paths", ())),
                    "validation": dict(item.get("validation", {})),
                    "metrics": dict(item.get("metrics", {})),
                }
            )
            for item in data.get("artwork_candidates", ())
        )
        return AgentState(
            run_id=str(data["run_id"]),
            request=request,
            phase=AgentPhase(data["phase"]),
            theme_expansion=(
                dict(data["theme_expansion"])
                if isinstance(data.get("theme_expansion"), Mapping)
                else None
            ),
            candidates=candidates,
            design_contract=contract,
            artwork_candidates=artwork_candidates,
            selected_artwork_id=data.get("selected_artwork_id"),
            image_calls_used=int(data.get("image_calls_used", 0)),
            role_retries_used=int(data.get("role_retries_used", 0)),
            refinement_rounds_used=int(data.get("refinement_rounds_used", 0)),
            stop_reason=data.get("stop_reason"),
        )


def tuple_to_events(items: Sequence[Mapping[str, Any]]) -> list[AgentEvent]:
    return [
        AgentEvent(
            sequence=int(item["sequence"]),
            timestamp=str(item["timestamp"]),
            phase=AgentPhase(item["phase"]),
            event_type=AgentEventType(item["event_type"]),
            summary=str(item["summary"]),
            tool=item.get("tool"),
            data=dict(item.get("data", {})),
        )
        for item in items
    ]
