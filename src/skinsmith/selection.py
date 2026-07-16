from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class Constraint:
    metric: str
    minimum: float | None = None
    maximum: float | None = None

    def violation(self, metrics: Mapping[str, float]) -> float:
        value = float(metrics[self.metric])
        violation = 0.0
        if self.minimum is not None and value < self.minimum:
            violation += (self.minimum - value) / max(abs(self.minimum), 1e-8)
        if self.maximum is not None and value > self.maximum:
            violation += (value - self.maximum) / max(abs(self.maximum), 1e-8)
        return violation


@dataclass(frozen=True)
class Objective:
    metric: str
    maximize: bool


@dataclass(frozen=True)
class SelectionDecision:
    selected_id: str
    feasible_ids: tuple[str, ...]
    rejected_ids: tuple[str, ...]
    pareto_ids: tuple[str, ...]
    violations: dict[str, float]
    policy: str

    def to_dict(self) -> dict:
        return asdict(self)


def constraint_first_pareto_select(
    candidates: Mapping[str, Mapping[str, float]],
    constraints: Iterable[Constraint],
    objectives: Iterable[Objective],
) -> SelectionDecision:
    if not candidates:
        raise ValueError("At least one candidate is required")
    constraints = tuple(constraints)
    objectives = tuple(objectives)
    if not objectives:
        raise ValueError("At least one objective is required")
    violations = {
        candidate_id: sum(rule.violation(metrics) for rule in constraints)
        for candidate_id, metrics in candidates.items()
    }
    feasible = tuple(candidate_id for candidate_id in candidates if violations[candidate_id] <= 1e-12)
    rejected = tuple(candidate_id for candidate_id in candidates if candidate_id not in feasible)
    pool = feasible or tuple(
        candidate_id
        for candidate_id, violation in violations.items()
        if violation == min(violations.values())
    )
    pareto = tuple(
        candidate_id
        for candidate_id in pool
        if not any(
            _dominates(candidates[other], candidates[candidate_id], objectives)
            for other in pool
            if other != candidate_id
        )
    )
    selected = sorted(
        pareto,
        key=lambda candidate_id: _objective_sort_key(candidates[candidate_id], objectives)
        + (candidate_id,),
    )[0]
    return SelectionDecision(
        selected_id=selected,
        feasible_ids=feasible,
        rejected_ids=rejected,
        pareto_ids=pareto,
        violations=violations,
        policy="hard constraints -> Pareto front -> lexicographic fixed objectives",
    )


def weighted_rank(
    candidates: Mapping[str, Mapping[str, float]],
    weighted_objectives: Mapping[Objective, float],
) -> list[tuple[str, float]]:
    if not candidates:
        raise ValueError("At least one candidate is required")
    if not weighted_objectives:
        raise ValueError("At least one weighted objective is required")
    scores = {candidate_id: 0.0 for candidate_id in candidates}
    for objective, weight in weighted_objectives.items():
        values = {key: float(metrics[objective.metric]) for key, metrics in candidates.items()}
        minimum = min(values.values())
        span = max(values.values()) - minimum
        for candidate_id, value in values.items():
            normalized = 1.0 if span <= 1e-12 else (value - minimum) / span
            if not objective.maximize:
                normalized = 1.0 - normalized
            scores[candidate_id] += float(weight) * normalized
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def _dominates(
    left: Mapping[str, float],
    right: Mapping[str, float],
    objectives: tuple[Objective, ...],
) -> bool:
    comparisons = []
    for objective in objectives:
        left_value = float(left[objective.metric])
        right_value = float(right[objective.metric])
        comparisons.append(left_value - right_value if objective.maximize else right_value - left_value)
    return all(value >= -1e-12 for value in comparisons) and any(value > 1e-12 for value in comparisons)


def _objective_sort_key(
    metrics: Mapping[str, float], objectives: tuple[Objective, ...]
) -> tuple[float, ...]:
    return tuple(
        -float(metrics[objective.metric]) if objective.maximize else float(metrics[objective.metric])
        for objective in objectives
    )
