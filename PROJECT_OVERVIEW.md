# SkinSmith Project Overview

> Updated: 2026-07-16  
> Course: SDSC6002 Research Project

## Project definition

SkinSmith is a constraint-aware generative Agent for game weapon skin design,
evaluated through a Counter-Strike 2 case study.

The project is not primarily a fan-skin generator. Its research focus is a general
pipeline for:

1. constrained texture generation;
2. weapon-space composition and UV baking;
3. render-in-the-loop evaluation;
4. multi-objective bounded refinement;
5. reproducible evidence logging.

CS2 provides a practical asset and deployment case. Portability means reusing the
Agent with another registered GameAssetAdapter, not reusing one AK-47 texture on
every weapon or game.

## User workflow

The final client uses three explicit human checkpoints:

```text
Select a registered weapon + enter one short theme keyword
  -> Agent expands a validated visual world
  -> Checkpoint 1: user confirms the ThemePack
  -> Agent generates 3-4 distinct textual art directions
  -> Checkpoint 2: user selects one direction
  -> Agent generates 3-4 dense landscape master artworks
  -> every artwork is mapped to left/right/top weapon previews
  -> Checkpoint 3: user selects one source-and-views candidate
  -> exact selected source is reused for formal execution
  -> evaluation, one bounded correction, rollback if needed, and export
```

Automatic review is recommendation-only. It cannot override human selection.

## Design routes

### Route A: Pattern baseline

Route A generates a dense, crop-tolerant, tileable square texture. It is the
generic baseline and supports seam-processing ablations.

### Route B: Weapon-space design

Route B creates one dense landscape master artwork, fits it to continuous
left/right/top weapon-space canvases, and bakes it into the fragmented UV atlas
using OBJ-derived position and normal maps.

The flat atlas may look fragmented. The intended composition is reconstructed when
the texture is mapped back to the 3D weapon.

Component masks are secondary constraints and diagnostics. They are not the default
source-generation model.

### Route C: Bounded refinement

Route C reuses Route B Round 0, diagnoses one visible problem, produces two local
correction candidates, and accepts a change only when:

- hard constraints pass; and
- the locked Agent score improves by at least `0.01`.

Otherwise the Agent rolls back to Route B.

## Accepted AK-47 result

Formal run:

`runs/agent_dragon_multicandidate_v1/`

- Selected direction: `Treasured Relic`
- Human-selected source: `artwork_04`
- Route B asset seam: `0.0007776109029832148`
- Route B multi-view: `0.8166198880536247`
- Route B total: `0.8291228922780649`
- Route C change: `-0.02195902089447299`
- Final decision: rollback to Route B
- Final PNG/TGA: 2048 x 2048 RGB with identical decoded pixels

The mapped-element reviewer records source fulfillment and left/right/top
readability, while preserving human authority.

## Technical contributions

1. **Weapon-space-to-UV constrained generation**  
   The design is composed in a mesh-derived canonical frame and baked through
   per-UV-pixel geometry maps.

2. **Render-in-the-loop evaluation**  
   Candidate quality is evaluated after mapping to the real 3D weapon from
   multiple views, not only as a square image.

3. **Multi-objective bounded Agent refinement**  
   Hard constraints, Pareto selection, local diagnosis, measured locality, and
   rollback prevent an aggregate score from hiding invalid outputs.

## Experiment design

- A: tileable pattern baseline.
- B: weapon-space composition and UV bake.
- C: B plus one bounded render-conditioned correction.
- Seam sub-ablation: identical B texture before and after edge correction.
- Selection sub-ablation: weighted ranking versus constraint-first/Pareto.
- Transfer case: M4A4 through GameAssetAdapter.

Formal paired statistics report mean, median, standard deviation, win rate, and
bootstrap 95% confidence intervals.

## Portability

### Within CS2

AK-47 is the accepted full workflow. M4A4 demonstrates that the Agent can reuse its
theme, style, generation, weapon-space, rendering, and evaluation logic with a new
asset adapter. Its joint seam/retention constraint is not yet equivalent to the
accepted AK-47 result, so it remains transfer evidence rather than a formal client
target.

### Across games

The reusable core remains the same, but each game requires an authoritative adapter
for:

- model and UV contract;
- material and paintable-area rules;
- semantic anchors;
- cameras;
- export format;
- deployment validation.

## Scope boundaries

- The completed pipeline generates and evaluates base-colour / Custom Paint Job
  textures. Normal, roughness, metallic, height, and displacement channels are
  outside the current implementation.
- Workbench lighting is deployment context, not evidence of model-generated
  physical surface properties.
- Steam Workshop publication is outside the course deliverable.
- Do not use logos, brands, teams, copyrighted characters, copied skins, or
  unlicensed images.
- Do not commit or redistribute Valve assets or model weights without permission.
- Do not train a large model from scratch.
- Do not expand to every weapon.
- Do not claim universal game compatibility from one CS2 case study.

## Prioritised next improvements

1. Capture the accepted dragon TGA in fixed Workbench left, right, and top views,
   plus one settings-panel screenshot.
2. Add spatially aligned normal, roughness, and metallic generation with
   cross-channel validation.
3. Automate fixed-camera engine capture and evidence logging.
4. Extend the adapter study beyond AK-47 and the bounded M4A4 transfer case.
5. Run a user study measuring revision effort, perceived control, and disagreement
   between source-only and mapped candidate choices.

Remaining academic work is final report PDF compilation, revised presentation
verification, supervisor feedback integration, and final reproducibility and
submission QA.
