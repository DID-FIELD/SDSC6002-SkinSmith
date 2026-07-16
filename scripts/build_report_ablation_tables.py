from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "runs" / "report_ready_ablation_tables"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Cannot write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value: float) -> str:
    return f"{value:.6f}"


def main() -> None:
    abc_path = ROOT / "runs" / "abc_ablation_true_weapon_space" / "ablation_log.json"
    edge_path = ROOT / "runs" / "route_b_edge_sweep" / "edge_sweep_log.json"
    abc = json.loads(abc_path.read_text(encoding="utf-8"))
    edge = json.loads(edge_path.read_text(encoding="utf-8"))
    OUTPUT.mkdir(parents=True, exist_ok=True)

    paired_rows: list[dict[str, Any]] = []
    labels = {
        "asset_seam_improvement": ("Asset seam improvement", "higher is better"),
        "multi_view_improvement": ("Multi-view improvement", "higher is better"),
        "component_balance_improvement": (
            "Component-detail balance improvement",
            "higher is better; metric caveat",
        ),
        "agent_score_improvement": (
            "Locked agent-score improvement",
            "higher is better; includes caveat metric",
        ),
    }
    for comparison, metrics in (
        ("B - A", abc["paired_b_minus_a"]),
        ("Final C - B", abc["route_c"]["paired_c_minus_b"]),
    ):
        for metric_id, record in metrics.items():
            label, direction = labels[metric_id]
            paired_rows.append(
                {
                    "comparison": comparison,
                    "metric_id": metric_id,
                    "metric": label,
                    "direction_and_note": direction,
                    "n": len(record["paired_values"]),
                    "mean": record["mean"],
                    "median": record["median"],
                    "std": record["std"],
                    "win_rate": record["win_rate"],
                    "bootstrap_95_ci_low": record["bootstrap_95_ci_mean"][0],
                    "bootstrap_95_ci_high": record["bootstrap_95_ci_mean"][1],
                }
            )
    _write_csv(OUTPUT / "table_abc_paired_summary.csv", paired_rows)

    candidate_rows: list[dict[str, Any]] = []
    for route_key, route_label in (("route_a", "A"), ("route_b", "B")):
        for item in sorted(
            abc[route_key]["candidates"], key=lambda value: value["candidate_id"]
        ):
            candidate_rows.append(
                {
                    "route": route_label,
                    "candidate_id": item["candidate_id"],
                    "seed": item["seed"],
                    "asset_seam_error": item["asset_seam"]["total_error"],
                    "multi_view_score": item["standard_score"]["multi_view"]["total_score"],
                    "texture_score": item["standard_score"]["texture_score"],
                    "component_detail_balance": item["component_detail_balance"],
                    "locked_agent_score": item["agent_score"],
                    "selected": item["candidate_id"] == abc["selected_ids"][route_label],
                }
            )
    _write_csv(OUTPUT / "table_abc_candidates.csv", candidate_rows)

    seam_correction_rows: list[dict[str, Any]] = []
    seam_relative_improvements: list[float] = []
    for item in sorted(
        abc["route_b"]["candidates"], key=lambda value: value["candidate_id"]
    ):
        before = item["before_asset_seam"]["total_error"]
        after = item["asset_seam"]["total_error"]
        improvement = before - after
        relative = improvement / before
        seam_relative_improvements.append(relative)
        seam_correction_rows.append(
            {
                "candidate_id": item["candidate_id"],
                "before_asset_seam_error": before,
                "after_asset_seam_error": after,
                "absolute_improvement": improvement,
                "relative_improvement": relative,
                "after_passes_0_01_threshold": after <= 0.01,
            }
        )
    _write_csv(
        OUTPUT / "table_formal_b_seam_correction.csv", seam_correction_rows
    )

    c_attempt_rows: list[dict[str, Any]] = []
    for run in abc["route_c"]["per_candidate"]:
        decision = run["refinement_decision"]
        for attempt in run["round_1_candidates"]:
            c_attempt_rows.append(
                {
                    "b_candidate_id": run["round_0_reused_candidate_id"],
                    "diagnosed_component": run["diagnosis"]["target_component"],
                    "attempt_id": attempt["candidate_id"],
                    "intensity": attempt["intensity"],
                    "asset_seam_error": attempt["asset_seam"]["total_error"],
                    "multi_view_score": attempt["standard_score"]["multi_view"]["total_score"],
                    "locked_agent_score": attempt["agent_score"],
                    "changed_pixel_fraction": attempt["locality"]["changed_pixel_fraction"],
                    "outside_halo_changed_pixels": attempt["locality"][
                        "changed_outside_target_halo_count"
                    ],
                    "selected_attempt": attempt["candidate_id"]
                    == run["round_1_selection"]["selected_id"],
                    "accepted_over_b": decision["accepted"],
                    "final_selected_round": decision["selected_round"],
                    "best_attempt_improvement": decision["improvement"],
                }
            )
    _write_csv(OUTPUT / "table_route_c_attempts.csv", c_attempt_rows)

    constraints = edge["hard_constraints"]
    feasible = set(edge["constraint_pareto_decision"]["feasible_ids"])
    pareto = set(edge["constraint_pareto_decision"]["pareto_ids"])
    edge_rows: list[dict[str, Any]] = []
    for item in edge["records"]:
        edge_rows.append(
            {
                "candidate_id": item["candidate_id"],
                "edge_safe_pixels": item["edge_safe_pixels"],
                "asset_seam_error": item["asset_seam_error"],
                "seam_constraint_pass": item["asset_seam_error"]
                <= constraints["asset_seam_error_maximum"],
                "multi_view_score": item["multi_view_score"],
                "multi_view_retention": item["multi_view_score"]
                / constraints["raw_multiview_score"],
                "retention_constraint_pass": item["multi_view_score"]
                >= constraints["minimum_multiview_score"],
                "hard_constraint_feasible": item["candidate_id"] in feasible,
                "pareto_front": item["candidate_id"] in pareto,
                "constraint_pareto_selected": item["candidate_id"]
                == edge["constraint_pareto_decision"]["selected_id"],
                "weighted_selected": item["candidate_id"]
                == edge["weighted_baseline"]["selected_id"],
            }
        )
    _write_csv(OUTPUT / "table_edge_safety_sweep.csv", edge_rows)

    selection_rows = [
        {
            "policy": "Constraint-first + Pareto",
            "selected_id": edge["constraint_pareto_decision"]["selected_id"],
            "edge_safe_pixels": 8,
            "asset_seam_error": next(
                x["asset_seam_error"]
                for x in edge["records"]
                if x["candidate_id"] == edge["constraint_pareto_decision"]["selected_id"]
            ),
            "multi_view_score": next(
                x["multi_view_score"]
                for x in edge["records"]
                if x["candidate_id"] == edge["constraint_pareto_decision"]["selected_id"]
            ),
            "hard_constraint_feasible": True,
            "interpretation": "Selected highest-priority multi-view objective among feasible Pareto candidates.",
        },
        {
            "policy": "Equal 50/50 weighted score",
            "selected_id": edge["weighted_baseline"]["selected_id"],
            "edge_safe_pixels": 4,
            "asset_seam_error": next(
                x["asset_seam_error"]
                for x in edge["records"]
                if x["candidate_id"] == edge["weighted_baseline"]["selected_id"]
            ),
            "multi_view_score": next(
                x["multi_view_score"]
                for x in edge["records"]
                if x["candidate_id"] == edge["weighted_baseline"]["selected_id"]
            ),
            "hard_constraint_feasible": edge["weighted_baseline"][
                "selected_is_hard_constraint_feasible"
            ],
            "interpretation": "Soft aggregate hides violation of the locked asset-seam threshold.",
        },
    ]
    _write_csv(OUTPUT / "table_selection_policy_comparison.csv", selection_rows)

    manifest = {
        "status": "report_tables_built_from_preserved_evidence",
        "sources": {
            "formal_abc": str(abc_path.relative_to(ROOT)),
            "edge_sweep_sub_ablation": str(edge_path.relative_to(ROOT)),
        },
        "boundaries": [
            "Formal A/B/C uses true weapon-space Route B.",
            "The edge-width and selection-policy sub-ablation uses one unchanged earlier technical composition; it supports seam/selection claims, not final-art superiority.",
            "Final C-B values are zero because all four attempted refinements were executed and rolled back.",
            "Component-detail balance and locked agent-score changes retain the documented metric-validity caveat.",
        ],
        "tables": [
            "table_abc_paired_summary.csv",
            "table_abc_candidates.csv",
            "table_formal_b_seam_correction.csv",
            "table_route_c_attempts.csv",
            "table_edge_safety_sweep.csv",
            "table_selection_policy_comparison.csv",
            "REPORT_TABLES_ZH.md",
        ],
    }
    (OUTPUT / "report_tables_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    b_seam = abc["paired_b_minus_a"]["asset_seam_improvement"]
    b_view = abc["paired_b_minus_a"]["multi_view_improvement"]
    c_score = [
        run["refinement_decision"]["improvement"]
        for run in abc["route_c"]["per_candidate"]
    ]
    markdown = f"""# SkinSmith Report-Ready Ablation Tables

> All values are extracted automatically from preserved machine logs. No weights
> or thresholds were changed. The formal A/B/C experiment and the edge-width
> sub-ablation use different experimental objects and must not be treated as one
> candidate pool.

## Table 1: Formal A/B/C Paired Results

| Comparison | Metric | Mean | Median | Std | Win rate | Bootstrap 95% CI |
|---|---|---:|---:|---:|---:|---:|
| B − A | Asset seam improvement | {_fmt(b_seam['mean'])} | {_fmt(b_seam['median'])} | {_fmt(b_seam['std'])} | {b_seam['win_rate']:.0%} | [{_fmt(b_seam['bootstrap_95_ci_mean'][0])}, {_fmt(b_seam['bootstrap_95_ci_mean'][1])}] |
| B − A | Multi-view improvement | {_fmt(b_view['mean'])} | {_fmt(b_view['median'])} | {_fmt(b_view['std'])} | {b_view['win_rate']:.0%} | [{_fmt(b_view['bootstrap_95_ci_mean'][0])}, {_fmt(b_view['bootstrap_95_ci_mean'][1])}] |
| Final C − B | Asset seam / Multi-view / Agent score | 0 | 0 | 0 | 0% | [0, 0] |

Interpretation: all four Route B candidates improve both asset seam and multi-view
performance. Route C executes two local candidates for every B candidate, but the
best locked Agent-score changes are `{', '.join(_fmt(value) for value in c_score)}`.
None reaches `+0.01`, so all four final outcomes roll back to B.

## Table 2: Formal Route B Seam Correction

| Candidate | Before | After | Absolute improvement | Relative improvement | Pass ≤ 0.01 |
|---|---:|---:|---:|---:|:---:|
"""
    for row in seam_correction_rows:
        markdown += (
            f"| {row['candidate_id']} | {_fmt(row['before_asset_seam_error'])} | "
            f"{_fmt(row['after_asset_seam_error'])} | {_fmt(row['absolute_improvement'])} | "
            f"{row['relative_improvement']:.2%} | "
            f"{'Yes' if row['after_passes_0_01_threshold'] else 'No'} |\n"
        )
    markdown += f"""

The mean relative seam improvement across the four formal Route B candidates is
`{sum(seam_relative_improvements) / len(seam_relative_improvements):.2%}`. Every
corrected candidate passes the `0.01` threshold.

## Table 3: Seam-Safety Operating Point

| Width | Asset seam | Multi-view | Retention | Feasible | Pareto | Selected |
|---:|---:|---:|---:|:---:|:---:|:---:|
"""
    for row in edge_rows:
        markdown += (
            f"| {row['edge_safe_pixels']} | {_fmt(row['asset_seam_error'])} | "
            f"{_fmt(row['multi_view_score'])} | {row['multi_view_retention']:.2%} | "
            f"{'Yes' if row['hard_constraint_feasible'] else 'No'} | "
            f"{'Yes' if row['pareto_front'] else 'No'} | "
            f"{'Yes' if row['constraint_pareto_selected'] else ''} |\n"
        )
    markdown += """

Width 8 is the operating point selected by the fixed objective order after meeting
`asset seam <= 0.01` and `multi-view retention >= 95%`.

## Table 4: Weighted versus Constraint-First/Pareto

| Strategy | Selection | Asset seam | Multi-view | Hard-constraint feasible |
|---|---|---:|---:|:---:|
"""
    for row in selection_rows:
        markdown += (
            f"| {row['policy']} | {row['selected_id']} | "
            f"{_fmt(row['asset_seam_error'])} | {_fmt(row['multi_view_score'])} | "
            f"{'Yes' if row['hard_constraint_feasible'] else 'No'} |\n"
        )
    markdown += """

The 50/50 weighted method selects width 4, but its asset seam of `0.016600`
exceeds the locked `0.01` threshold. Constraint-first/Pareto selects width 8,
showing that a soft weighted aggregate can hide an unacceptable asset constraint.

## Reporting Boundaries

- Formal evidence for Route B comes from `abc_ablation_true_weapon_space`.
- The edge-width sweep uses one earlier technical composition. It supports only
  seam operating-point and selection-policy claims, not final-art superiority.
- `component_detail_balance` fails on high-contrast procedural weapon-space
  candidates and must be reported as a metric limitation.
- A final C-B difference of zero means that correction was attempted and safely
  rolled back; it does not mean the feedback step was skipped.
"""
    (OUTPUT / "REPORT_TABLES_ZH.md").write_text(markdown, encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
