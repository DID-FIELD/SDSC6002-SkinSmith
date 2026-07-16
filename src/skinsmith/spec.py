from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


Motif = Literal["waves", "diagonal", "circuits"]


@dataclass(frozen=True)
class DesignSpec:
    theme_name: str
    description: str
    palette: tuple[str, ...]
    motif: Motif
    size: int = 512
    candidate_count: int = 4
    seed: int = 20260714
    refinement_directives: tuple[str, ...] = ()
    prompt_motif: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ViewMetrics:
    view_name: str
    foreground_ratio: float
    contrast_score: float
    saturation_score: float
    detail_score: float
    mean_luminance: float


@dataclass(frozen=True)
class MultiViewScore:
    views: tuple[ViewMetrics, ...]
    consistency_score: float
    total_score: float


@dataclass(frozen=True)
class SemanticScore:
    text: str
    texture_cosine: float
    view_cosines: tuple[float, ...]
    combined_cosine: float
    total_score: float


@dataclass(frozen=True)
class CandidateScore:
    candidate_id: str
    seam_score: float
    contrast_score: float
    saturation_score: float
    coverage_score: float
    texture_score: float
    multi_view: MultiViewScore | None
    semantic: SemanticScore | None
    total_score: float

    def to_dict(self) -> dict:
        return asdict(self)
