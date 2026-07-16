# Two-week delivery plan

> Status update, 16 July 2026: the complete idea-to-Workshop-screenshot chain,
> formal A/B/C experiment, report tables, and one M4A4 adapter transfer case are
> complete. The next critical path is to turn the verified modules into a reusable
> production-style Agent. Streamlit is deferred until the same Agent can run from
> CLI/Python on a previously uncached brief without code changes.

## Definition of done

The course prototype is complete when a user can provide an original, possibly
uncached design brief and receive through one unified Agent run:

1. a validated ThemePack and compatible StylePack created dynamically or reused from cache;
2. three to four clearly distinct `ArtDirectionCandidate` records with concepts,
   palettes, materials, route-specific composition logic, risks, and recommendation reasons;
3. a user-selected art direction followed by three to four enriched horizontal master-artwork candidates;
4. a low-cost OBJ/UV preview pass for every artwork candidate, presented as original artwork plus left/right/top views;
5. a user-selected executable artwork contract; only this candidate receives formal 2048/TGA processing;
6. automatic source compliance checks and candidate-local retry rather than whole-run restart;
7. weapon-space canvases, target UV atlas, scores, hard-constraint decisions, and ranked recommendations;
8. one bounded Route-C observation-diagnosis-action-decision cycle with locality proof and accept/rollback;
9. usable PNG/TGA exports plus prompts, seeds, provider/model IDs, hashes, checkpoints, events, and final AgentRunResult;
10. CLI/Python use independent of Streamlit, followed by a Streamlit client using the same orchestrator;
11. preserved AK-47 Workshop, formal A/B/C, M4A4 transfer, report, poster, and presentation evidence.

Steam Workshop publication is not part of the definition of done.

## Feature freeze

The development feature freeze is **19 July 2026**. After that date, work is limited
to defect fixes, experiments, report figures, the poster, and the presentation.

### 14 July - foundation

- [x] Audit GPU, Python, CS2, and rendering options.
- [x] Create modular generator, constraint, renderer, evaluator, and agent interfaces.
- [x] Run a deterministic smoke pipeline with four candidates.
- [x] Add seam metrics, repair, logging, and regression tests.

### 15 July - real asset loop

- [x] Inspect official CS2 workshop geometry and UV assets.
- [x] Connect one main weapon to the preview renderer.
- [x] Produce left, right, and top views.
- [x] Add multi-view scoring, CSV ranking, timing, and repeatability evidence.
- [x] Verify one exported texture manually in the CS2 Workshop Item Editor; path passed, visual quality failed.

### 16 July - generation backend

- [x] Connect one local diffusion/image-generation backend.
- [x] Generate square, original, no-logo textures from structured briefs.
- [x] Preserve the procedural backend for deterministic testing.
- [x] Record model revision, prompt tokens, seed, runtime, and peak VRAM.

### 17 July - scoring and agent iteration

- [x] Add semantic alignment and multi-view scoring.
- [x] Add one bounded refinement round.
- [x] Save candidate ranking and decision traces.
- [x] Derive the AK-47 paintable atlas, UV islands, and diagnostic views from the selected OBJ.
- [x] Build and test the mesh-derived UV seam graph/metric.
- [x] Bind the selected asset version and prepare semantic component masks for the UV-aware route.
- [x] Build and test the constraint-first/Pareto candidate gate.

### 18 July - interface and transfer

- [x] Implement component-aware UV-atlas composition with soft region transitions for one AK-47 Custom Paint path candidate.
- [x] Validate it through left/right/top rendering and record B-before/B-after asset-seam evidence.
- [x] Select 8 px UV-edge safety width under joint seam and multi-view constraints.
- [x] Add one render-conditioned component-detail action with two candidates and rollback.
- [x] Preserve the first shared-seed B0 run as negative evidence that mask-aware remapping is not whole-weapon design.
- [x] Derive a canonical weapon frame and per-UV-pixel position/normal maps.
- [x] Run and visually accept the 512 weapon-space design -> UV bake -> 3D reconstruction path.
- [x] Add controlled generated-content layers and normal-weighted side/top projection blending.
- [x] Reuse one preserved SD-Turbo image to verify content placement without new inference.
- [x] Replace one-off abstract prompting with a reusable StylePack/ArtDirectionSpec planner.
- [x] Add blue-and-white porcelain, original mascot, and retro-futurist neon style packs.
- [x] Produce four porcelain alternatives from one natural-language brief.
- [x] Separate ThemePack (what to depict) from StylePack (how to depict it).
- [x] Split Route A into PatternDesigner and Route B into WeaponThemeDesigner; lock C as B plus feedback.
- [x] Preserve the first `Wild Lotus` A/B/C route-design bundle.
- [x] Add `AssetCreativeProfile` and an injectable `ThemeCompiler` for uncached prompts and weapon-specific theme compilation.
- [x] Reject unknown themes when no real creative backend is configured; do not fake open-ended creation with keyword rules.
- [x] Connect Gemini structured output and preserve compiled ThemePack/model provenance with redacted traces.
- [x] Add dynamic StyleCompiler and provider adapters; verify an uncached marble brief receives a geological/material StylePack instead of a cached botanical style.
- [x] Upgrade the preview renderer to barycentric per-pixel UV sampling with a z-buffer; retain flat sampling as ablation.
- [x] Generate the first Nano Banana mapped A/B pair from the dynamic marble bundle; preserve 3×3, UV, left/right/top, metrics, traces, and hashes.
- [x] Compile a true Route-B WeaponDesignPlan from bundle component semantics and validate the generated draft at 512.
- [x] Tighten semantic-source compliance, regenerate only hero/connector, reuse secondary/background, and remap without overwriting Round-0 evidence.
- [x] Expand a distinct Route-B direction, fix the image/canonical anchor mismatch, select the strongest 512 candidate, and export the 2048 RGB TGA.
- [x] Preserve the mesh-derived result as general-model evidence after Workbench exposed a deployment UV mismatch.
- [x] Add the official AK-47 Workbench OBJ/UV Sheet adapter, reject forced wrapping of out-of-atlas faces, and export the corrected 2048 official-UV TGA.
- [x] Reimport the official-UV TGA into Workbench and accept left/right/top placement.
- [x] Integrate true Route B into the shared-seed A/B/C experiment runner.
- [x] Defer UI until the UV-aware main route is accepted.

### 19-22 July - reusable Agent orchestration

- [x] Define `AgentState`, `AgentEvent`, `AgentMemory`, `ToolRegistry`, run budgets,
  checkpoints, pause/resume, and `AgentRunResult`.
- [x] Unify brief -> Theme/Style -> multiple explicit art directions -> selection -> design contract.
- [x] Connect real A/B generation, role gates/retry, weapon-space/UV, evaluation,
  Pareto selection, bounded correction/rollback, and export.
- [x] Validate one new uncached theme/style through CLI without source-code edits.
- [x] Freeze the Agent API after this acceptance; keep the known-good HD asset binding
  as the default and reject contract/AssetSpec mismatches.
- [x] Replace fixed four-role Route-B placement with a validated component-relationship
  graph supporting spanning, grouped, independent, and background art units.
- [x] Preserve backward compatibility for existing themes without a graph.
- [x] Add and verify the dragon-body / magazine-claw / muzzle-head scenario offline.
- [x] Run the real Gemini component-relationship graph through scope-guided
  generation and exact mesh-semantic UV-region fitting; preserve the technically
  passing but visually rejected revision as evidence.
- [x] Stop per-component dragon generation after it exposed avoidable semantic
  failure modes; retain the run as negative/design-motivation evidence.
- [x] Implement one dense master-artwork source as the default Route-B design object.
- [x] Run one real master-artwork -> continuous weapon space -> OBJ UV bake acceptance
  before starting UI work.

### 23-24 July - usable client and evidence

- [x] Add the `awaiting_artwork` Agent phase and CLI/Python resume contract.
- [x] Generate 3-4 enriched horizontal master-artwork candidates after direction selection.
- [x] Pre-map every candidate and expose original + left/right/top as one selection group.
- [x] Run formal 2048/TGA processing only after artwork selection.
- [x] Start a real Gemini dragon multi-candidate run and preserve four direction choices.
- [x] Select one real direction and generate four source-plus-three-view artwork groups.
- [x] Human-select one mapped group and export its formal 2048 TGA without source regeneration.
- [x] Add recommendation-only design-element matching across source and left/right/top views.
- [x] Build Streamlit as a thin client over the accepted two-stage Agent API.
- Support free brief, optional style family, direction selection, run progress,
  tool/observation/decision events, candidate comparison, and export.
- Keep an evidence replay mode for reliable presentation, but do not make replay
  the only functional mode.
- [x] Record one full new-style Agent run and one replayable marble case.

### 25-29 July - report and poster

- [ ] Write method, implementation, experiments, discussion, and limitations.
- [ ] Produce the final report PDF.
- [ ] Create the A0 landscape poster PowerPoint and obtain supervisor feedback.
- [ ] Prepare the supervisor presentation.

### 30 July-1 August - final QA

- Re-run reproducibility checks.
- Verify the PDF and A0 PowerPoint visually.
- Package code, logs, figures, and presentation material.

## Five-person work split

1. Integration owner: repository, interfaces, acceptance tests, final demo.
2. Generation owner: prompt planner and image-generation backend.
3. Texture owner: seam repair, palette, masks, and export constraints.
4. Rendering owner: UV/model loading and multi-view preview generation.
5. Evaluation owner: metrics, experiments, charts, report and poster coordination.

Every owner must provide code, a short method note, test evidence, and one report-ready
figure for their component.
