# SkinSmith Technical Contributions

This document defines the contribution claims and the boundaries that should be
used consistently in the report, poster, and presentation.

## 1. Weapon-Space-to-UV Constrained Generation

### Problem

A visually attractive square image is not necessarily a usable texture. Real weapon
UVs fragment, rotate, scale, and separate the visible surface. A generic pattern can
pass a square-border seam test while failing across internal asset seams.

### Method

SkinSmith derives a canonical weapon frame from the target mesh and bakes per-UV-
pixel 3D position and normal maps. Route B first composes the selected master artwork
on continuous left, right, and top weapon-space canvases. It then samples those
canvases through the OBJ geometry maps into the existing square UV atlas.

The flat output is allowed to look fragmented. Coherence is evaluated after mapping
the texture back to the 3D model.

### Constraints

- authoritative asset and UV binding;
- paintable-area mask;
- component and visibility metadata;
- UV-island and true seam graph;
- edge-safety correction;
- mapped multi-view evaluation.

### Evidence

The accepted AK-47 Route B result:

- asset seam: `0.0007776109029832148`;
- multi-view: `0.8166198880536247`;
- total score: `0.8291228922780649`;
- all hard constraints passed.

The formal A/B experiment shows that the weapon-space route improves both asset
seam and multi-view performance across all four paired candidates.

### Claim boundary

The contribution is not "automatic UV unwrapping." SkinSmith uses the target
asset's existing UV contract. The contribution is composing in a coherent
mesh-derived weapon space and baking that design into the authoritative atlas.

## 2. Render-in-the-Loop Multi-View Evaluation

### Problem

Texture-only evaluation cannot observe whether a motif is readable on the receiver,
lost on a narrow barrel, split by the UV layout, or inconsistent across visible
views.

### Method

Every candidate is mapped to the real weapon geometry and rendered from left,
right, and top views. Evaluation combines:

- texture-level contrast, saturation, detail, and coverage;
- asset-seam error;
- mapped multi-view quality;
- optional semantic and mapped-element readability evidence.

The source image and three mapped views are presented as one indivisible candidate.

### Human authority

The mapped-element reviewer reports source fulfillment and per-view readability.
Its recommendation score weights the left view most strongly, but it never approves,
rejects, or selects the final artwork. Human selection is authoritative.

### Claim boundary

The current software renderer is deterministic and suitable for controlled
comparison. It is not a photorealistic substitute for CS2 Workbench.

## 3. Multi-Objective Bounded Agent Refinement

### Problem

A weighted aggregate can hide an invalid hard constraint. A candidate may score
well visually while exceeding the asset-seam threshold.

### Method

SkinSmith uses:

1. hard-constraint filtering;
2. feasible candidate selection;
3. Pareto dominance;
4. deterministic objective ordering;
5. one bounded diagnosis and correction round;
6. a minimum `+0.01` improvement gate;
7. rollback when the correction is not beneficial.

Route C produces exactly two local correction candidates. Locality is measured, and
changes outside the target component plus its transition halo must be zero.

### Evidence

In the fixed edge-width pool, equal weighted ranking selects width 4 even though its
asset seam exceeds `0.01`. Constraint-first/Pareto selects width 8, which satisfies
both the seam and retention constraints.

In the accepted dragon run, Route C changed the locked score by
`-0.02195902089447299`, so the Agent correctly rolled back to Route B.

### Claim boundary

Rollback is a successful Agent outcome. The contribution is safe bounded decision
making, not a guarantee that every correction improves the design.

## 4. Three-Checkpoint Human-Agent Collaboration

The product workflow contains three explicit checkpoints:

1. confirm the Agent-expanded ThemePack;
2. select one textual art direction;
3. select one mapped artwork candidate.

This structure separates:

- what visual world should be depicted;
- how it should be depicted;
- which generated image survives real asset mapping.

The Agent can begin from one keyword such as `dragon`; the user does not need to
author a production prompt.

## 5. Adapter-Based Portability

SkinSmith separates the reusable Agent from game- and weapon-specific contracts.

Reusable:

- theme and style compilation;
- image generation;
- weapon-space composition;
- evaluation and selection;
- bounded refinement;
- evidence logging.

Adapter-specific:

- mesh and UV;
- material and paintable-area rules;
- canonical axes and component anchors;
- cameras;
- export format;
- deployment validation.

AK-47 is the full accepted case. M4A4 demonstrates core transfer but does not yet
match the AK-47 joint seam/retention acceptance. This supports adapter portability,
not universal compatibility.

## 6. Experimental Evidence

Formal comparisons:

- A versus B;
- final C versus B;
- B before versus after seam correction;
- weighted ranking versus constraint-first/Pareto;
- AK-47 versus M4A4 transfer behavior.

Report paired mean, median, standard deviation, win rate, and bootstrap 95%
confidence intervals. Do not combine the formal A/B/C pool with the earlier
edge-width technical sweep.

## Recommended contribution statement

> SkinSmith introduces a constraint-aware Agent workflow that expands a compact
> design theme, composes generated artwork in a mesh-derived weapon space, bakes
> the result into an authoritative UV atlas, evaluates candidates through
> multi-view rendering, and performs one bounded multi-objective correction with
> hard-constraint rollback.

## Required limitations

- one primary CS2 weapon provides the full case study;
- M4A4 is transfer evidence, not an equivalent deployment result;
- the renderer is a technical evaluator, not a game-engine renderer;
- image quality depends on the external generation backend;
- automatic readability scores do not replace human judgment;
- Steam Workshop publication is outside scope.
