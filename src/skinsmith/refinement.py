from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from .spec import DesignSpec


@dataclass(frozen=True)
class RefinementDiagnosis:
    semantic_score: float | None
    saturation_score: float
    mean_detail_score: float | None
    seam_error: float
    prompt_directives: tuple[str, ...]
    processing_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RefinementDecision:
    accepted: bool
    round_0_score: float
    round_1_score: float
    improvement: float
    selected_round: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def diagnose_candidate(record: dict[str, Any]) -> RefinementDiagnosis:
    """Convert evaluator output into the one permitted feedback action set."""

    scores = record["scores"]
    semantic = scores.get("semantic")
    semantic_score = float(semantic["total_score"]) if semantic else None
    saturation_score = float(scores["saturation_score"])
    multiview = scores.get("multi_view")
    view_details = [float(view["detail_score"]) for view in multiview["views"]] if multiview else []
    mean_detail = sum(view_details) / len(view_details) if view_details else None
    seam = float(record["seam_error_after"])

    directives: list[str] = []
    processing_actions: list[str] = []
    if semantic_score is not None and semantic_score < 0.70:
        directives.append("strong theme focus")
    if saturation_score < 0.70:
        directives.append("vivid palette contrast")
    if mean_detail is not None and mean_detail < 0.45:
        directives.append("clear medium-scale motifs")
    elif mean_detail is not None and mean_detail > 0.90:
        directives.append("larger clean shapes, reduced micro-detail")
    if seam > 0.08:
        processing_actions.append("retain frequency-domain seam repair")

    return RefinementDiagnosis(
        semantic_score=semantic_score,
        saturation_score=saturation_score,
        mean_detail_score=mean_detail,
        seam_error=seam,
        prompt_directives=tuple(directives),
        processing_actions=tuple(processing_actions),
    )


def make_round_1_spec(spec: DesignSpec, diagnosis: RefinementDiagnosis) -> DesignSpec:
    """Create exactly two Round-1 candidates at base_seed + 1000/+1001."""

    return replace(
        spec,
        candidate_count=2,
        seed=spec.seed + 1000,
        refinement_directives=diagnosis.prompt_directives,
    )


def decide_refinement(round_0_score: float, round_1_score: float, minimum_improvement: float = 0.01) -> RefinementDecision:
    improvement = float(round_1_score - round_0_score)
    accepted = improvement >= minimum_improvement
    return RefinementDecision(
        accepted=accepted,
        round_0_score=float(round_0_score),
        round_1_score=float(round_1_score),
        improvement=improvement,
        selected_round=1 if accepted else 0,
        reason=(
            f"Round 1 improved by {improvement:.6f}, meeting the {minimum_improvement:.6f} threshold"
            if accepted
            else f"Round 1 improved by {improvement:.6f}, below the {minimum_improvement:.6f} threshold"
        ),
    )
