# SDSC6002 Rubric-to-Evidence Matrix

> Status: Phase 3 submission-readiness document  
> Rubric source: `MSDS Research Projects for Data Science Assessment Form
> 2025_26 (SDSC6002).pdf`  
> Updated: 2026-07-17

## Purpose

This matrix maps every assessment descriptor to report content and preserved
evidence so that technical completion is converted into assessable academic work.

## Assessment mapping

| Assessment item | Target band | Report location | Existing evidence | Remaining action |
|---|---|---|---|---|
| Project significance, aims, objectives, scope | Very Good | Introduction; Research Questions | Complete report draft, `RESEARCH_FRAMING.md`, `PROJECT_OVERVIEW.md` | Apply team/supervisor wording feedback and freeze |
| Time management and milestones | Good to Very Good | Appendix milestone summary | `PROJECT_PLAN.md`, dated runs, `CODEX_CONTEXT.md`, five-member ownership | Confirm the final group record |
| Literature enquiry | Very Good | Related Work | 34 verified primary sources and nine-theme synthesis | Final citation-format review |
| Literature support for methodology | Very Good | Related Work; Methodology | Report links diffusion, texture, UV, evaluation, selection, and collaboration literature to the method | Final supervisor review |
| Methodology | Very Good | Methodology | Implemented method, equations, source code, tests, technical specification, and accepted runs | Freeze the approved wording |
| Analysis, discussion, appraisal, conclusion | Very Good | Results; Discussion; Conclusion | Unified RQ1-RQ5 results, formal A/B/C, sub-ablations, transfer case, failures, and rollback | Final claim and limitation review |
| Documentation and poster presentation | Very Good | Entire submission | Strong engineering documentation; A0 poster and ten-slide supervisor presentation completed and Office-render verified | Freeze the final report PDF and complete the final replay/publication audit |

## CILO mapping

| CILO | SkinSmith evidence | Reporting requirement |
|---|---|---|
| CILO 1: independent problem solving | UV mismatch diagnosis, adapter design, bounded Agent workflow | Explain problem evolution and evidence-based decisions |
| CILO 2: ML/statistical learning | Diffusion/image generation, semantic evaluation, paired statistics, bootstrap CIs | Explain models, metrics, baselines, and statistical procedure |
| CILO 3: method evaluation and ethics | A/B/C ablation, hard constraints, failures, rollback, rights policy | Include validity threats, responsible AI, copyright, provenance, and privacy |
| CILO 4: insights and novel findings | Weapon-space benefit, mapped evaluation, weighted-score failure, safe rollback | State findings by research question without overstating novelty |
| CILO 5: professional report and presentation | Complete report draft, A0 poster, ten-slide supervisor presentation, and reproducible demo | Apply team/supervisor feedback and freeze the final submission versions |

## Evidence rules

- Every reported number must identify a preserved run and machine-readable source.
- Formal A/B/C evidence must not be mixed with earlier diagnostic pools.
- Negative results and rollback must be reported, not hidden.
- Human artwork selection remains authoritative; automated readability is
  recommendation-only.
- AK-47 is the complete case; M4A4 is transfer evidence.
- Formal `runs/` evidence is immutable.

## Research-question evidence inventory

| Question | Formal or primary evidence | Intended report use |
|---|---|---|
| RQ1: weapon-space composition | `runs/abc_ablation_true_weapon_space/ablation_log.json`; `runs/report_ready_ablation_tables/table_abc_paired_summary.csv`; `table_abc_candidates.csv` | Paired Route A versus Route B table and mapped comparison figure |
| RQ2: render-in-the-loop evaluation | `runs/agent_dragon_multicandidate_v1/artwork_candidates.json`; candidate `mapped_preview/` folders; `execution/mapped_element_readability.json` | Source-versus-mapped failure cases and three-view candidate cards |
| RQ3: constrained refinement | `runs/report_ready_ablation_tables/table_selection_policy_comparison.csv`; `table_edge_safety_sweep.csv`; `table_route_c_attempts.csv`; accepted run result | Weighted-score failure, feasible/Pareto choice, locality, and rollback |
| RQ4: three-checkpoint collaboration | `runs/agent_three_checkpoint_dragon_smoke_v4/`; `runs/agent_dragon_multicandidate_v1/`; `streamlit_app.py` | State-machine diagram, three checkpoints, and final human-selected run |
| RQ5: adapter portability | AK-47 accepted run; `runs/m4a4_game_asset_adapter_transfer/`; `GameAssetAdapter` configuration | Separate reusable logic from asset-specific contracts and report transfer limits |

## Milestone evidence

| Phase | Completed work | Evidence of project control |
|---|---|---|
| Scope narrowing | Broad Latent Vision topic narrowed to a technical image-processing/generation Agent | Supervisor guidance in `HANDOFF.md`; locked scope in `CODEX_CONTEXT.md` |
| Feasibility baseline | Procedural generation, seam repair, OBJ render, metrics, and logging | Baseline smoke runs and tests |
| Asset diagnosis | New CS2 geometry bound; incompatible legacy UV rejected | UV diagnostics, mesh hashes, adapter records |
| Weapon-space method | Canonical frame, geometry maps, continuous canvases, UV bake | Route B smoke and formal experiment |
| Constraint-aware Agent | Hard gates, Pareto selection, one bounded correction, rollback | Edge sweep, selection-policy sub-ablation, Route C logs |
| Open-ended creativity | Dynamic ThemePack/StylePack and real image generation | Gemini compilation and generated-source traces |
| Human checkpoints | Theme, direction, and mapped artwork selection | Runtime state, CLI resume, Streamlit, preserved runs |
| Academic production | Revised report draft, A0 poster, ten-slide supervisor presentation, and rubric matrix | `report/overleaf/`, `report/build/`, `RESEARCH_FRAMING.md`, `LITERATURE_REVIEW.md`, `references.bib`, this file |

## Report production gates

- Introduction must state the five research questions from `RESEARCH_FRAMING.md`.
- Related Work must cite and synthesize `LITERATURE_REVIEW.md`.
- Methodology must distinguish inherited literature concepts from SkinSmith's
  adaptation and implementation.
- Results must answer RQ1-RQ5 in order.
- Discussion must include metric validity, failed generations, all Route C
  rollbacks, renderer limitations, and transfer limits.
- Ethics must disclose model use, provenance, rights restrictions, API handling,
  and human authority.
- Appendices must provide reproducibility commands and the evidence-path index.

## Current rubric readiness estimate

| Area | Current readiness |
|---|---:|
| Significance and scope | 95% |
| Time management evidence | 90% |
| Literature enquiry | 95% |
| Literature-supported methodology | 90% |
| Method implementation | 95% |
| Analysis and conclusion | 90% |
| Final documentation and presentation | 85% |
| Overall submission readiness | 90% |

These percentages are planning estimates, not predicted assessor marks.
