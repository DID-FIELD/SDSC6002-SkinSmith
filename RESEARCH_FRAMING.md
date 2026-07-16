# SkinSmith Research Framing

> Status: Phase 1 working document  
> Updated: 2026-07-16  
> Course: SDSC6002 Research Project

## Locked working title

**SkinSmith: A Constraint-Aware Generative Agent for Game Weapon Skin Design -
A Counter-Strike 2 Case Study**

The title identifies the reusable research object (a constraint-aware generative
Agent), the application (game weapon skin design), and the evaluation boundary
(a CS2 case study). It does not claim universal game compatibility.

## Research problem

Text-to-image systems generate visually plausible rectangular images, but a game
weapon texture must also survive a fragmented UV atlas, reconstruct a coherent
design on a narrow three-dimensional asset, satisfy technical export constraints,
and remain readable from multiple views. A visually attractive source image is
therefore not sufficient evidence of a usable weapon skin.

SkinSmith studies whether a human-supervised generative Agent can transform one
compact theme keyword into a technically valid, mapped, evaluated, and reproducible
weapon texture.

## Research questions

### RQ1 - Weapon-space composition

Does composing artwork in a mesh-derived continuous weapon space and then baking it
to the authoritative UV atlas improve mapped asset-seam and multi-view performance
relative to a generic tileable-pattern baseline?

### RQ2 - Render-in-the-loop evaluation

What failures become observable when candidates are evaluated after mapping to the
real weapon from left, right, and top views rather than only as source images or
flat texture atlases?

### RQ3 - Constraint-aware refinement

Can hard-constraint filtering, Pareto-based selection, and a bounded correction
with rollback prevent an Agent from accepting technically invalid or lower-quality
updates that a soft aggregate score might prefer?

### RQ4 - Human-Agent collaboration

Can three explicit human checkpoints separate theme intent, art-direction choice,
and mapped-artwork selection while allowing the Agent to begin from one short
keyword instead of a production-ready prompt?

### RQ5 - Adapter-based portability

Which parts of the pipeline transfer to a second weapon through a GameAssetAdapter,
and which geometry, material, camera, and deployment contracts remain
asset-specific?

## Contribution claims

### C1 - Weapon-space-to-UV constrained generation

SkinSmith composes a selected master artwork in a canonical frame derived from the
target mesh and bakes it into the existing UV atlas through per-UV-pixel position
and normal maps.

Claim boundary: this is not automatic UV unwrapping. The authoritative target UV
contract is retained.

### C2 - Render-in-the-loop multi-view evaluation

Every artwork candidate is mapped to the real weapon and evaluated from left,
right, and top views together with texture and true asset-seam evidence.

Claim boundary: the deterministic software renderer supports controlled technical
comparison but is not a photorealistic replacement for CS2 Workbench.

### C3 - Multi-objective bounded Agent refinement

SkinSmith combines hard constraints, feasible-set filtering, Pareto dominance,
deterministic selection, one local correction round, a minimum improvement gate,
and rollback.

Claim boundary: the method provides bounded no-regression behavior; it does not
guarantee that every attempted correction improves visual quality.

### C4 - Three-checkpoint human-Agent workflow

The user separately confirms the expanded ThemePack, selects one textual art
direction, and selects one source-plus-mapped-views artwork candidate. Automatic
review remains recommendation-only.

### C5 - Adapter-based portability

The reusable Agent is separated from asset-specific mesh, UV, material, camera, and
export contracts. AK-47 is the accepted full case; M4A4 is transfer evidence only.

## Primary evidence mapping

| Research question | Principal evidence |
|---|---|
| RQ1 | Formal Route A/B paired experiment and report-ready ablation tables |
| RQ2 | Source plus left/right/top candidate groups and mapped readability reports |
| RQ3 | Weighted-versus-constraint-first sub-ablation and Route C rollback |
| RQ4 | Three-checkpoint runtime, CLI, Streamlit client, and dragon smoke/run |
| RQ5 | AK-47 accepted run and M4A4 GameAssetAdapter transfer case |

## Required claim discipline

- Do not claim support for every weapon or game.
- Do not describe M4A4 as equivalent to the accepted AK-47 deployment.
- Do not treat automatic readability as a replacement for human judgment.
- Do not claim that all Route C attempts improve the result.
- Do not describe the software renderer as a game-engine renderer.
- Do not claim automatic UV unwrapping.
- Do not claim novelty over all prior work until the literature review supports a
  carefully bounded comparison.

## Phase 1 completion checklist

- [x] Lock working title.
- [x] Lock research problem and five research questions.
- [x] Lock bounded contribution claims.
- [x] Verify 25-40 primary academic sources.
- [x] Complete thematic related-work synthesis.
- [x] Complete `references.bib`.
- [x] Complete the rubric-to-evidence matrix.
- [x] Audit citation keys and document cross-references.
- [ ] Read the six closest 3D-texturing papers in full and finalize the
  paper-level comparison table before writing the report.
