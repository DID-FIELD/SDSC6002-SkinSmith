from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class DesignElement:
    element_id: str
    label: str
    description: str
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.element_id.strip() or not self.label.strip():
            raise ValueError("design element id and label must not be empty")
        if not self.description.strip():
            raise ValueError("design element description must not be empty")
        if self.weight <= 0:
            raise ValueError("design element weight must be positive")


@dataclass(frozen=True)
class ElementReadability:
    element_id: str
    source_score: float
    left_score: float
    right_score: float
    top_score: float
    best_view: str
    source_evidence: str
    mapped_evidence: str
    confidence: float

    def __post_init__(self) -> None:
        for name in (
            "source_score",
            "left_score",
            "right_score",
            "top_score",
            "confidence",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.best_view not in {"left", "right", "top", "none"}:
            raise ValueError("best_view must be left, right, top, or none")


def build_readability_report(
    elements: Sequence[DesignElement],
    matches: Sequence[ElementReadability],
    *,
    visible_threshold: float = 0.55,
) -> dict[str, Any]:
    """Aggregate explainable semantic matches as recommendation-only evidence."""

    if not elements:
        raise ValueError("at least one design element is required")
    element_map = {item.element_id: item for item in elements}
    match_map = {item.element_id: item for item in matches}
    if set(match_map) != set(element_map):
        missing = sorted(set(element_map) - set(match_map))
        extra = sorted(set(match_map) - set(element_map))
        raise ValueError(
            f"readability matches do not align with elements; missing={missing}, extra={extra}"
        )
    total_weight = sum(item.weight for item in elements)

    def weighted(field: str) -> float:
        return float(
            sum(
                element.weight * float(getattr(match_map[element.element_id], field))
                for element in elements
            )
            / total_weight
        )

    source = weighted("source_score")
    left = weighted("left_score")
    right = weighted("right_score")
    top = weighted("top_score")
    multiview = 0.60 * left + 0.25 * right + 0.15 * top
    recommendation = 0.25 * source + 0.50 * left + 0.15 * right + 0.10 * top
    visible = sum(
        1
        for item in matches
        if max(item.left_score, item.right_score, item.top_score) >= visible_threshold
    )
    records = []
    for element in elements:
        match = match_map[element.element_id]
        records.append(
            {
                "element": asdict(element),
                "match": asdict(match),
                "visible_in_any_view": (
                    max(match.left_score, match.right_score, match.top_score)
                    >= visible_threshold
                ),
            }
        )
    return {
        "status": "recommendation_only",
        "human_selection_is_authoritative": True,
        "formula": {
            "multiview_readability": "0.60*left + 0.25*right + 0.15*top",
            "recommendation_score": (
                "0.25*source_design_fulfillment + 0.50*left + 0.15*right + 0.10*top"
            ),
            "visible_threshold": visible_threshold,
        },
        "source_design_fulfillment": source,
        "left_readability": left,
        "right_readability": right,
        "top_readability": top,
        "multiview_readability": multiview,
        "recommendation_score": recommendation,
        "visible_element_count": visible,
        "element_count": len(elements),
        "visible_element_ratio": visible / len(elements),
        "elements": records,
    }


def design_elements_from_records(
    theme_elements: Sequence[Mapping[str, Any]],
    motifs: Sequence[str],
    world_elements: Sequence[str],
    *,
    maximum: int = 16,
) -> tuple[DesignElement, ...]:
    """Build a compact, stable evaluation list without theme-specific keyword rules."""

    records: list[DesignElement] = []
    seen: set[str] = set()
    seen_subject_nouns: set[str] = set()

    def subject_noun(text: str) -> str | None:
        words = re.findall(r"[a-z]+", text.casefold())
        if not words:
            return None
        noun = words[-1]
        if noun.endswith("s") and len(noun) > 4:
            noun = noun[:-1]
        if noun in {
            "art",
            "detail",
            "element",
            "field",
            "fragment",
            "material",
            "motif",
            "pattern",
            "subject",
            "texture",
        }:
            return None
        return noun

    def add(element_id: str, label: str, description: str, weight: float) -> None:
        keys = {
            " ".join(label.casefold().split()),
            " ".join(description.casefold().split()),
        }
        keys.discard("")
        noun = subject_noun(label)
        if (
            not keys
            or keys & seen
            or (noun is not None and noun in seen_subject_nouns)
            or len(records) >= maximum
        ):
            return
        seen.update(keys)
        if noun is not None:
            seen_subject_nouns.add(noun)
        records.append(DesignElement(element_id, label, description, weight))

    for index, item in enumerate(theme_elements):
        label = str(item.get("display_name", "")).strip()
        description = str(item.get("generation_description", label)).strip()
        element_id = str(item.get("element_id", f"theme_{index + 1:02d}")).strip()
        role = str(item.get("semantic_role", "")).strip()
        weight = 1.35 if role == "hero" else 1.0
        add(element_id, label, description, weight)
    for index, motif in enumerate(motifs):
        text = str(motif).strip()
        add(f"motif_{index + 1:02d}", text, text, 1.2)
    for index, value in enumerate(world_elements):
        text = str(value).strip()
        if not text or len(text) > 72:
            continue
        add(f"world_{index + 1:02d}", text, text, 0.8)
    return tuple(records)
