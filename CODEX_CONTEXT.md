# SkinSmith Codex Context

> Canonical continuity file for future Codex sessions. Read this file first.  
> Status date: 2026-07-20, Asia/Shanghai.
> Project root: `D:\project\SDSC6002-SkinSmith`.

## 1. Mission and academic requirement

Build a completed technical image-processing/generation agent for SDSC6002. The supervisor explicitly advised narrowing the scope because less than three weeks remained; the work does not need to stay with the original broad Latent Vision direction. A technically complete image-processing agent is sufficient.

Working title:

`SkinSmith: A Constraint-Aware Generative Agent for Game Weapon Skin Design - A Counter-Strike 2 Case Study`

CS2 is the case study. The research contribution is the general pipeline for constrained texture generation, render-in-the-loop evaluation, and bounded agent refinement.

Final deadline: **2026-08-02 at 12:00 noon**. Required academic deliverables include the report PDF and an A0 landscape poster PowerPoint (1189 × 841 mm). The poster PPTX must be sent to the supervisor and General Office (`ds.go@cityu.edu.hk`) by the deadline, and the group must arrange a poster presentation with the supervisor before then. The group decided not to request an extension.

## 2. Current phase and decision

Current phase: **the Agent and thin Streamlit client implement the clarified three-checkpoint interaction contract, the English report draft includes the accepted group contribution record and an explicit material-channel boundary, and the A0 poster has been revised against the preserved project evidence while retaining its original layout. A fresh `flower` case now demonstrates the complete transferable workflow: CP1 expanded the single keyword into `Withered Petal Covenant`; CP2 offered four textual directions and locked `Decay Gradient`; CP3 compared four indivisible source + left/right/top candidate cards and human-selected `artwork_04`; formal execution reused that exact source and exported a 2048 Route-B PNG/TGA. The existing dragon run remains accepted evidence. The supervisor presentation must next be rebuilt around the complete flower flow after the user supplies fixed left/right/top CS2 Workbench captures plus a settings screenshot for the new flower TGA. AK-47 is the fully accepted client target, M4A4 remains adapter-level transfer evidence, and output remains base-colour Custom Paint Job rather than generated PBR material. The reviewed repository is published at `https://github.com/DID-FIELD/SDSC6002-SkinSmith`; supervisor feedback is still pending before final report freeze**.

Question tested: can the project reliably execute texture generation, seam processing, real UV mapping, multi-view rendering, quantitative evaluation, automatic ranking, and evidence logging before adding diffusion?

Decision: **GO — the core chain is feasible and the project should continue.**

The procedural generator remains the deterministic baseline. SD-Turbo is now the accepted local generation backend, but not necessarily the final model-quality optimum.

## 3. Locked final scope

Required final chain:

```text
Design brief
  -> AssetCreativeProfile (weapon type, silhouette, component functions, anchors)
  -> ThemeCompiler (reuse cache or synthesize a new validated ThemePack from zero)
  -> ThemePack (expand a broad theme into a rich world of subjects, symbols, environment, connectors, and micro-detail)
  -> StyleCompiler (reuse a compatible cache or synthesize a Theme/asset-specific StylePack)
  -> 3-4 textual ArtDirectionCandidates (how to depict it)
  -> user selects one direction
  -> 3-4 horizontal, dense, crop-robust master-artwork candidates
  -> low-cost OBJ/UV mapping of every candidate
  -> present original artwork + AK left/right/top previews together
  -> user selects the best mapped candidate
  -> Route A PatternDesigner: dense crop-tolerant tileable template
  -> Route B WeaponThemeDesigner: selected master artwork -> continuous weapon canvas -> OBJ-driven square UV atlas
  -> Route C: Route B plus one bounded render-conditioned correction
  -> UV-aware Custom Paint candidate composition
  -> real weapon UV application
  -> multi-view rendering
  -> semantic + 2D technical + 3D render evaluation
  -> one bounded evaluator-driven refinement round
  -> automatic selection and export
  -> reproducible experiment log
```

Clarified minimum client checkpoint contract on 16 July:

```text
Checkpoint 1: select a registered weapon + enter one short theme keyword
  -> Agent expands associated subjects, symbols, environment, materials, palette,
     connectors, atmosphere, and forbidden content
  -> user confirms or edits the expanded ThemePack

Checkpoint 2: Agent proposes 3-4 materially different textual art directions
  -> user selects one direction

Checkpoint 3: Agent generates 3-4 artworks for that selected direction
  -> every candidate is mapped through the selected weapon's own OBJ/UV adapter
  -> source + left + right + top are one indivisible candidate card
  -> model review is recommendation-only; user selects the artwork

Then: exact selected source -> formal bake/evaluation/bounded refinement -> export
```

“Expand/search related words” means semantic theme-world expansion through the
ThemeCompiler and validated local knowledge/cache by default, not uncontrolled web
search. Internet retrieval is optional evidence enrichment only if explicitly added
later. Weapon portability means the same Agent contract can register another
`GameAssetAdapter`; it never means one texture or UV contract works on every weapon.
AK-47 currently has full end-to-end formal acceptance. M4A4 currently demonstrates
adapter-level transfer and is not yet equivalent to a fully accepted selectable
client target; the UI must label this distinction honestly.

Three report-level contributions:

1. UV-layout-aware constrained texture generation, with the generic tileable route retained as baseline.
2. Render-in-the-loop multi-view evaluation.
3. Multi-objective agent refinement.

Definition of done:

- one main weapon completes the full chain;
- one additional weapon may be used only for transfer validation;
- diffusion/image generation and procedural baseline both work through the same interface;
- one bounded feedback/regeneration round works;
- formal runs preserve all inputs, outputs, metrics, decisions, time, seeds, and model versions;
- ablations compare at least raw generation, seam processing, render scoring, and full agent;
- one reusable Agent API/CLI handles free briefs, explicit direction choice, real execution tools, checkpoints, budgets, and standardized results; Streamlit is only a client after this passes;
- the Agent exposes an explicit `awaiting_artwork` checkpoint after generating candidate source-and-three-view groups, and formal export cannot start before an artwork candidate is selected;
- report/poster figures are produced from preserved experiment evidence.
- one final showcase candidate uses deliberate AK-47 whole-weapon composition baked into the UV atlas rather than an unconstrained square pattern.

Route decision after official Valve guide review:

- Valve documents original-UV tiling and triplanar pattern application, while Custom Paint applies a full-color image through the weapon's original UVs;
- Gunsmith combines Patina and Custom Paint, but its full material complexity is optional and outside the current critical path;
- Route A (current generic square/tileable texture) is frozen as baseline and seam-ablation evidence;
- Route B (AK-47 UV-aware Custom Paint) is the required final-showcase route;
- Route B must use a mesh-derived canonical weapon frame, per-UV-pixel position/normal maps, UV-island, paintable-area, component, and UV-edge constraints plus render-in-the-loop checks;
- Route B still outputs one flat square texture, but the design source is one dense master artwork fitted to continuous left/right/top weapon canvases and then baked through the AK-47 OBJ position/normal maps;
- Route-B source generation is landscape-oriented. A broad request such as “dragon” must be expanded into a visually rich family of associated elements instead of one oversized dragon on an empty field. Primary and supporting elements remain medium/small enough to survive crop and UV fragmentation; no single element may dominate the whole canvas;
- source beauty alone is not an acceptance signal. Each candidate is judged from the original horizontal artwork and its mapped left/right/top AK views together;
- the resulting UV atlas may look fragmented because it stores OBJ-driven cuts of the continuous artwork; the mapped 3D weapon reconstructs the intended image flow;
- component masks and the older composition graph remain optional diagnostics/local constraints, not the default source-generation model;
- official reference: `https://www.counter-strike.net/workshop/workshopfinishes#gunsmith`.

## 4. Implemented and verified

Baseline pipeline:

- `ProceduralTextureGenerator` creates four deterministic candidates.
- `make_seamless` repairs periodic boundaries.
- `seam_error` measures boundary pixel and gradient discontinuity.
- `ObjMultiViewRenderer` parses Valve OBJ/UV data and renders left/right/top views.
- 2D and multi-view scores participate in final ranking.
- final real-model score uses 65% texture score and 35% multi-view score.
- JSON log and ranking CSV are written for each run.
- per-candidate and total runtime are recorded.

Generation backend accepted on 15 July:

- `DiffusionTextureGenerator` uses `stabilityai/sd-turbo`;
- pinned revision: `b261bac6fd2cf515557d5d0707481eafa0485ec2`;
- 512 × 512, two inference steps, guidance scale 0;
- prompt is 74/77 CLIP tokens and overlength prompts now fail instead of truncating;
- observed peak allocated VRAM: about 3.03 GB;
- cached four-candidate generation + seam repair + AK-47 render + ranking: about 28 seconds;
- latest diffusion full-chain winner: `candidate_02`;
- evidence: `runs/diffusion_real_model/agent_log.json` and `run_summary.csv`.

Seam repair update:

- direct border blending was rejected after visual inspection because it created a mirrored frame;
- centre-offset inpainting reduced but did not eliminate a blurred frame;
- current implementation uses frequency-domain periodic-plus-smooth decomposition;
- 3 × 3 visual tiling shows no obvious boundary line and high-detail content is preserved.

Local Valve asset status:

- official geometry ZIP downloaded under ignored `third_party/downloads/`;
- `weapon_rif_ak47.obj` extracted under ignored `third_party/valve_geometry/`;
- AK-47 model has 21,548 UV coordinates and 26,133 triangles;
- official Workshop Resources index: `https://www.counter-strike.net/workshop/workshopresources`;
- the optional legacy Workbench package and the new CS2 geometry are separate official downloads;
- the legacy `UVSheets/ak-47.tga` is 2048 x 2048 but does not match the new CS2 AK-47 OBJ atlas;
- bind mesh version and UV source in one `AssetSpec`; never mix the legacy sheet with the new geometry;
- mesh-derived coverage, islands, and seams remain valid for self-owned/general model targets, but deployment into an existing game must bind that game's authoritative model/UV/material contract; official sheets are required when the target workflow provides them;
- never commit or redistribute these assets.

UV asset analysis implemented on 15 July:

- `src/skinsmith/uv_asset.py` derives welded mesh topology, UV islands, true 3D-corresponding UV seam pairs, paintable masks, wireframes, island maps, and seam-graph diagnostics;
- Valve's new OBJ duplicates geometric vertices at many UV seams, so seam detection first welds coordinate-identical vertices before comparing UV edges;
- new CS2 AK-47: 21,548 vertices, 14,055 welded vertices, 26,133 triangles, 928 UV islands, 77 mesh components, and 4,999 UV seam pairs;
- the accepted Route-A `candidate_02` measures asset seam color error 0.29538, gradient error 0.02916, and combined asset seam error 0.22883;
- this provides quantitative evidence that the old square-border seam metric can pass while real internal asset seams remain inconsistent;
- the legacy Workbench AK-47 pair contains 7,539 vertices, 8,605 UVs, 13,069 triangulated faces, 195 UV islands, and 2,254 seam pairs;
- `ObjMultiViewRenderer.load_obj` now fan-triangulates textured OBJ polygon faces, including legacy quad faces;
- preserved diagnostics: `runs/uv_asset_diagnostics/uv_asset_log.json`, `paintable_mask.png`, `uv_wireframe.png`, `uv_islands.png`, `uv_seam_graph.png`, and `official_ak47_uv_sheet.png`;
- official archives and extracted assets remain ignored under `third_party/`.

Versioned Route-B asset preparation accepted on 15 July:

- `AssetSpec` is implemented in `src/skinsmith/asset_spec.py` and loaded from `config/assets/ak47_cs2.json`;
- the original technical asset is the new-CS2 Workshop AK-47 geometry with locked SHA-256 `dae29ee5cadfbf17f84d50d0fe1d50500988e45886571f17bf5eab0d4065654f`; it remains valid mesh-derived portability evidence but is no longer the CS Workbench deployment adapter;
- the spec binds mesh version/path/hash, mesh-derived UV source, 2048 texture size, TGA export profile, camera views, ordered semantic rules, and fallback region;
- semantic rules combine stable topology-component IDs with 3D face-centroid ranges rather than manually guessing positions on the flat UV image;
- accepted masks: stock, receiver, magazine, pistol grip, handguard, front assembly, and barrel/muzzle;
- all 26,133 faces receive exactly one semantic face label;
- binary mask UV union covers 72.7201% of the 2048 square; only 0.5646% of pixels have two labels at antialiased/shared boundaries, maximum overlap two;
- visual inspection of left/right/top calibration passed: all seven visible regions occupy the intended weapon parts;
- hard region boundaries are diagnostic only; the compositor must feather transitions instead of exposing calibration colour cuts;
- evidence: `runs/route_b_asset_prep/asset_prep_log.json`, `mask_validation.json`, semantic atlas/masks, topology calibration, legends, and multi-view renders.

Route-B component-aware compositor smoke accepted on 15 July:

- `src/skinsmith/uv_compositor.py` implements semantic-mask composition, per-component detail/orientation/strength styles, soft region transitions, and a mesh-atlas UV-edge safety band;
- the deterministic smoke reuses one 512 x 512 procedural `neon_tide` source and produces a 2048 x 2048 exact-fit PNG/TGA without invoking diffusion;
- receiver retains high detail; stock and handguard use lower frequency; magazine rotates the motif; pistol grip, front assembly, and barrel/muzzle are progressively subdued;
- the shared dark base colour at UV-island edges provides a deterministic asset-seam correction and a direct B-before/B-after sub-ablation;
- before correction asset seam error: 0.193931; selected 8 px correction: 0.005522; relative improvement: 97.1525%;
- before multi-view score: 0.706715; selected 8 px correction: 0.696973; the 0.009742 decrease retains 98.62% of the raw score;
- visual review passed the technical path: semantic regions remain correct and soft transitions replace calibration colours, but this procedural image is not final showcase art;
- evidence: `runs/route_b_composition_smoke/composition_log.json`, `composition_validation.json`, before/after textures, 24-bit TGA, edge-safety map, and both multi-view sets.

Edge-safety sweep and constraint-first/Pareto selection accepted on 15 July:

- `config/route_b.json` now locks all component styles, 8 px semantic transition sigma, candidate widths `[0,2,4,8,12,16,24]`, seam threshold 0.01, minimum multi-view retention 95%, objective order, and weighted baseline;
- `src/skinsmith/selection.py` implements hard-constraint violations, feasible filtering, Pareto dominance, deterministic objective-order selection, and normalized weighted ranking;
- the sweep reuses one unchanged composed texture and varies only UV edge-safe width, so it adds no generation cost;
- feasible/Pareto widths: 8, 12, and 16 px;
- selected operating point: 8 px, asset seam 0.005522, multi-view 0.696973;
- 24 px achieves lower seam 0.001447 but fails minimum multi-view 0.671380 with score 0.662934;
- equal 50/50 weighted ranking selects 4 px, but its seam 0.016600 violates the hard 0.01 threshold;
- this is direct evidence for the Weighted-vs-Constraint-first/Pareto sub-ablation: a soft aggregate can hide an invalid asset condition;
- evidence: `runs/route_b_edge_sweep/edge_sweep_log.json`, `edge_sweep.csv`, `selection_validation.json`, per-width textures/renders, and selected 2048 PNG/TGA.

Route-C render-conditioned local refinement accepted on 15 July:

- `src/skinsmith/component_feedback.py` renders reusable white-on-black semantic visibility maps and measures component detail only inside eroded visible regions, excluding silhouette edges;
- locked targets, two correction intensities, 40/35/25 agent-score weights, hard constraints, and the +0.01 acceptance threshold are stored in `config/route_b.json` before execution;
- Round 0 is the accepted 8 px Route-B texture; no new source image or diffusion inference is used;
- diagnosis selected `receiver`: rendered detail density 0.219485 versus target 0.100000, relative excess 119.48%;
- exactly two Round-1 candidates modify only receiver blur, contrast, and motif strength; other component style parameters are unchanged;
- candidate 01 changes 27.4854% of atlas pixels, with zero changed pixels outside the receiver plus 24 px transition halo; it is hard-constraint feasible but agent score falls from 0.558838 to 0.535746;
- candidate 02 changes 28.9223%, also with zero outside-halo change; it lowers receiver detail further but fails minimum multi-view retention;
- the hard gate selects candidate 01 as the only feasible Round-1 candidate, then the +0.01 improvement policy rejects it because improvement is -0.023093;
- final decision correctly rolls back to Route-B Round 0; visual review agrees that both corrections make important receiver surfaces too dark;
- this is valid Agent evidence: a targeted action was diagnosed and executed, its locality was measured, and a harmful result was rejected;
- evidence: `runs/route_c_local_refinement/agent_log.json`, `run_summary.csv`, `validation.json`, component visibility maps, two Round-1 candidates, and selected Round-0 PNG/TGA.

Critical Route-B correction agreed on 15 July:

- the first unified procedural A/B/C runner completed, but its current B implementation is not accepted as the formal UV-aware design route;
- current B only takes one generic square source and applies different blur/rotation/strength settings under semantic masks; this is `B0 mask-aware remapping`, not genuine component-specific design with whole-weapon composition;
- diagnostic paired results expose the limitation: B0 improves asset seam by mean 0.263263 and component-detail balance by 0.114857, but reduces multi-view score by 0.116174 and agent score by 0.026065 across all four shared candidates;
- preserve `runs/abc_ablation_smoke/` as negative/design-motivation evidence only; do not report it as proof that formal Route B improves visual quality, and do not use its Route-C acceptance as a formal C result;
- Route A remains pattern-first: a repeated all-over image needs only theme, palette, motif, and tiling quality;
- true Route B must be asset/layout-first: define a global visual hierarchy on the weapon, give each component a deliberate role, and make component artwork combine into one coherent weapon-level design;
- the implementation direction is a mesh-derived canonical weapon coordinate plus UV-baked object-space position/side maps: design on left/right/top weapon-space canvases, then bake the coherent layout into the existing UV atlas;
- component masks become secondary local layers and constraints, not the primary source of composition;
- example distinction: Route A may repeat cat/dog motifs uniformly; Route B should place a hero subject on the receiver, continue its lines/forms through stock and handguard, use the magazine as a secondary motif, and preserve intentional quiet areas;
- this correction does not discard existing work: AssetSpec, UV masks, seam graph/correction, renderer, component feedback, selection, and rollback are all retained; only the formal Route-B source/composition model changes.

True Route-B weapon-space technical smoke accepted on 15 July:

- `src/skinsmith/weapon_space.py` implements `CanonicalWeaponFrame`, `UVGeometryMaps`, `WeaponDesignPlan`, OBJ-to-UV barycentric geometry-map baking, weapon-space canvas rendering, and weapon-space-to-UV texture baking;
- the design exists coherently on continuous left/right/top canvases before UV packing; the resulting flat atlas is intentionally fragmented, and coherence is judged after reconstruction on the model;
- the locked AK-47 mesh produces a 512 map with 185,225 valid pixels (`70.6577%`), 961 overlap pixels (`0.3666%`), and maximum coverage count 18 in small stacked/overlap areas;
- moving the focal longitudinal coordinate to `t=0.77` places the hero motif on the receiver instead of the magazine; longitudinal flow reconstructs across the weapon body;
- raw asset seam is `0.094424`; the 2 px correction at 512, equivalent to the locked 8 px width at 2048, reduces it to `0.005303` and passes the `0.01` hard threshold;
- raw multi-view score is `0.560486`; corrected multi-view score is `0.548435`;
- visual review status is `pass_true_route_b_technical_path_not_final_art`: geometry mapping, fragmented UV storage, and 3D reconstruction are accepted, while the procedural motif remains a placeholder rather than showcase art;
- report/PPT-ready concept evidence is `runs/weapon_space_route_b_smoke/route_b_weapon_space_concept.png`; machine-readable evidence is `weapon_space_log.json` and `visual_validation.json` in the same directory.

Weapon-space generated-content layer and projection blending accepted on 15 July:

- `WeaponSpaceLayerSpec` and `compose_weapon_space_layers` place preserved/generated images on continuous left/right/top canvases with normalized placement, scale, rotation, opacity, normal/screen/multiply blending, fit mode, right-side mirroring, and soft edge feathering;
- generated content is addressed by a logical layer ID and copied into the run directory with its SHA-256, so it never guesses fragmented UV coordinates and formal evidence retains the exact source;
- left/right/top projection selection now uses canonical surface-normal direction and power-weighted side/top blending (`projection_blend_power = 4.0`) instead of a hard surface-chart switch;
- projection-only control: corrected asset seam `0.005242`, corrected multi-view `0.546672`; compared with the original hard switch (`0.005303`, `0.548435`), the automatic view score is effectively neutral/slightly lower, so do not claim a quality gain from blending alone;
- content integration reuses the preserved SD-Turbo `candidate_02` at 12% screen opacity as a restrained material layer; it does not invoke new generation and is not pasted directly into UV;
- content result: corrected asset seam `0.006003` (passes `0.01`) and corrected multi-view `0.576644`, an increase of `0.029972` over the projection-only control;
- visual review passes content integration: the material layer remains subordinate while the receiver focal motif, longitudinal flow, and quiet muzzle are still controlled by `WeaponDesignPlan`; it remains a technical content-layer smoke, not final art;
- evidence: `runs/weapon_space_projection_blend_smoke/` and `runs/weapon_space_content_smoke/`.

General art-direction and route-semantics correction on 15 July:

- the user clarified that the target is a general design agent: a detailed natural-language style brief should lead to style research/knowledge, attractive 2D texture alternatives, weapon previews, scoring, and several recommended choices; cats/dogs are one example, not the final fixed theme;
- the first `StylePlanner` iteration proved reusable style knowledge, but incorrectly treated A and B as two prompts from one planner; the user rejected this because A and B have different design objects and generation logic;
- `src/skinsmith/design_routes.py` now separates `ThemePack` (content/narrative) from `StylePack` (visual language), and implements `PatternDesigner`, `WeaponThemeDesigner`, `RouteDesignPlanner`, and the fixed definition of C as B plus feedback;
- Route A explicitly designs a dense, varied-scale, crop-tolerant square template and requires a 3x3 tile check plus AK-47 left/right/top previews;
- Route B generates four classes of square semantic source assets (hero, secondary, connector, background), composes them in continuous weapon space, bakes the composition into the square UV atlas, and requires the final UV plus AK-47 left/right/top previews;
- B source squares are not reusable patterns, and the final B square is fragmented UV storage rather than a standalone illustration;
- `config/design_themes/wild_lotus.json` defines Wild Lotus hero/secondary/connector/background elements and a complete seven-component weapon narrative; `config/styles/modern_chinese_botanical.json` defines its default visual language independently;
- AK-47 semantic canvas anchors are preserved in `config/assets/ak47_weapon_space_anchors.json`; receiver prominence is 1.0 while barrel/muzzle detail density is 0.08;
- the preserved plan is `runs/design_planning_wild_lotus/route_design_bundle.json`; it spends no image-generation run and is the contract for the next mapped test;
- the user further clarified that the agent must accept open-ended prompts such as landscape painting, relief, marble, electronics, and chip circuitry; theme packs are examples/caches, not an allowed-theme list;
- `AssetCreativeProfile` now exposes weapon type, silhouette notes, component functions, and normalized anchors to creative planning;
- `ThemeCompiler` reuses a compatible cached theme or calls an injected `ThemeSynthesisBackend` to create a new ThemePack for the target weapon, then validates elements, palette, element references, and exact component coverage;
- `ThemePack.target_components` and `WeaponThemeDesigner` no longer hard-code the seven AK component names, allowing a compiled theme to target a different weapon component set;
- an uncached landscape-painting unit test uses a fake backend to prove dynamic ThemePack creation and target-weapon validation;
- a preserved real Codex-agent response compiles the uncached chip-circuit brief into `silicon_pulse_v1 / Silicon Vein`, and `runs/theme_compilation_chip_circuit/route_design_bundle.json` proves the result enters the distinct A/B/C planner;
- `src/skinsmith/api_backends.py` implements OpenAI Responses and Gemini Interactions structured ThemePack/StylePack generation plus OpenAI/Gemini image generation; all use swappable model IDs and environment-variable keys;
- API traces preserve provider, model, endpoint, redacted request, raw response, and validation evidence; keys are never written;
- live Gemini acceptance: `gemini-3.5-flash` returned sustained high-demand 500/timeout, `gemini-2.5-flash` returned unavailable-to-new-users 404, and `gemini-3.1-flash-lite` successfully compiled the uncached marble/gold-vein brief. This model is now the default theme compiler;
- the generated `tectonic_gilded_fissure / Obsidian Vein AK-47` theme has four semantic elements and exact seven-component coverage, and its A/B/C bundle plus redacted trace are preserved under `runs/theme_compilation_marble/`;
- the first live result selected `modern_chinese_botanical_v1`, which is semantically unsuitable for marble. This was direct evidence that dynamic ThemeCompiler plus a static style whitelist was incomplete;
- `src/skinsmith/style_planner.py` now implements provider-neutral `StyleCompiler`: it can reuse a compatible cached style or call a synthesis backend, validates exact target-component roles, and overwrites the generated palette with the validated Theme palette so Theme and Style cannot drift;
- `src/skinsmith/api_backends.py` now implements OpenAI/Gemini structured StylePack adapters and a dynamic JSON Schema requiring exact target-component role keys, four candidate directions, A/B-specific composition rules, rights-safe reference policy, evaluation criteria, and a procedural fallback;
- `scripts/plan_design_routes.py` now performs live Theme compilation followed by live Style compilation for a generated theme, saving `compiled_theme.json`, `theme_api_trace.json`, `compiled_style.json`, `style_api_trace.json`, and the final A/B/C bundle;
- second live Gemini acceptance: the marble brief generated `abyssal_vein_marble / Gilded Strata AK-47` plus `abyssal_vein_marble_v1`; the style vocabulary is geological/material (obsidian, stratification, fissures, gold mineral flow), exact seven-component roles and four candidate directions validate, legacy botanical/porcelain terms count is zero, and secret matches across preserved output files are zero;
- dynamic Theme+Style evidence is preserved under `runs/theme_compilation_marble_dynamic_style/`; this was text-only and made no paid Nano Banana image call;
- `ApiTextureGenerator` connects either image API to the existing candidate interface; Route-B may call the same image backend directly for hero/secondary/connector/background source assets;
- the user selected Nano Banana as the production image backend; lock the nickname to `gemini-3.1-flash-image` (Nano Banana 2), 1K, 1:1, with `gemini-3.1-flash-lite` for Theme/Style compilation. OpenAI remains optional comparison only;
- `config/creative_api.json` is the authoritative provider/model/budget-gate configuration, and `scripts/generate_route_assets.py` expands a bundle into one A candidate plus four B semantic source jobs with per-call traces and hashes;
- paid-image runner hardening: `scripts/generate_route_assets.py` now checkpoints before and after every job, verifies bundle/backend identity, hashes completed outputs, skips valid completed jobs on rerun, and records provider failures so an interrupted five-job smoke does not blindly duplicate image charges;
- first Route-A image request exposed that the current Gemini Interactions image endpoint accepts `image/jpeg`, not `image/png`; `GeminiImageBackend` and its regression test now enforce JPEG response MIME while the saved source file remains PNG;
- after Paid Tier activation, the locked five-image smoke completed: one Route-A source and four Route-B semantic sources. Transient TLS failures occurred, and the checkpoint safely reused two completed B jobs rather than regenerating them;
- `generation_log.json` records five completed jobs, provider/model, prompts, output hashes and per-call traces; secret matches across the run remain zero;
- `scripts/preview_route_a_asset.py` now executes generated Route A through raw/repaired 3x3 tiling, AK UV application, barycentric left/right/top rendering, square-seam, asset-seam and automatic scoring;
- live Route-A marble evidence: raw square seam `0.074328`, repaired square seam `0.018168`, repaired asset seam `0.116078`, multi-view `0.617104`, total `0.684366`; the material looks attractive but repeat structure and internal UV discontinuity confirm A as baseline rather than showcase route;
- `src/skinsmith/route_b_composition.py` compiles any RouteDesignBundle component layout into a generated-asset WeaponDesignPlan and expands four semantic roles into seven continuous weapon-space layers; it is not a marble-specific coordinate file;
- `scripts/weapon_space_route_b_smoke.py` accepts a dynamic route bundle plus generated-assets directory, then performs semantic composition, position/normal-map UV bake, edge safety, AK left/right/top rendering and evidence logging;
- live Route-B marble evidence: raw asset seam `0.095290`, corrected asset seam `0.006756` (passes `0.01`), corrected multi-view `0.741879`, total `0.775921`; relative to A, multi-view improves `0.124775` and total improves `0.091555`;
- mapped B reconstructs a receiver-led gold focal flow and quiet muzzle, but visual source review found weapon/mockup fragments in hero and connector and rectangular overlays on the continuous canvas. Mark this Round 0 `technical_smoke_pass_final_art_fail`, even though automatic scores improve;
- full Round-0 evidence is preserved under `runs/nano_banana_marble_dynamic_style/`, including five sources, redacted traces, A tile/mapped previews, B weapon-space canvases, UV atlas, AK previews and logs;
- `src/skinsmith/route_asset_generation.py` now has a shared semantic-source contract that treats weapon/component names only as placement metadata and forbids weapons, parts, mockups, UV layouts, rectangular material samples and presentation boards; role-specific contracts distinguish isolated hero, quiet secondary, sparse connector and edge-to-edge background;
- `scripts/generate_route_assets.py --role` selectively generates one or more B semantic roles, enabling minimal-cost failure-local retry without replacing accepted sources;
- the separate refinement run regenerated only hero and connector (two 1K calls, estimated `$0.134`) and reused the exact Round-0 secondary/background files. Connector passes source review; hero clears the weapon/mockup/material-board hard gate but retains a substantial irregular geological mass, so it is `pass_with_caveat`;
- refined B evidence: raw asset seam `0.092557`, corrected asset seam `0.006540` (passes `0.01`), corrected multi-view `0.725273`, total `0.763492`; versus A, multi-view improves approximately `0.108169` and total improves `0.079126`;
- mapped refined AK left/right/top views preserve the receiver-led black-gold flow without a visible ghost weapon or exposed rectangular source boundary. Accept it as `accept_512_refinement_candidate_not_final_showcase`; preserve evidence and hashes under `runs/nano_banana_marble_dynamic_style_refined/`;
- `scripts/generate_route_assets.py --direction` resolves a validated StylePack `candidate_directions.direction_id`, locks its concept/motifs/route emphasis into distinct job IDs and prompts, and rejects output-directory reuse across directions; this makes candidate diversity explicit rather than random repeated sampling;
- candidate-role contracts now state that role priority overrides direction-wide imagery. The first `tectonic_cluster` source round kept an attractive hero but failed secondary/connector/background role separation; a separate three-role retry passed. Seven successful 1K outputs across the initial and targeted rounds cost an estimated `$0.469`; a transient failed TLS request was checkpointed, and secret matches across candidate evidence are zero;
- mapping the clean cluster sources exposed a coordinate-convention bug: bundle `canvas_center` uses top-left image coordinates, while procedural focal/secondary anchors use canonical longitudinal/up coordinates. Content layers had been given canonical-up values and therefore placed the receiver hero on the magazine;
- `src/skinsmith/route_b_composition.py` now separates `_canvas_center` from `_canonical_center`. The fixed cluster multi-view rises from `0.348902` to `0.536669` and total from `0.473477` to `0.600985` without any new image generation; this is preserved as a generation-vs-layout diagnosis case;
- fair anchor-fixed 512 comparison selects the refined single-fissure candidate: corrected asset seam `0.007113`, multi-view `0.735170`, total `0.782189`. The cluster candidate passes source/mapped/seam gates but remains a darker alternative;
- `scripts/weapon_space_route_b_smoke.py --size` now supports 512/1024/2048, scales the seam safety band proportionally, and writes a 24-bit RGB TGA at the asset's formal size;
- the earlier new-geometry 2048 result remains preserved: 8 px corrected asset seam `0.003943`, multi-view `0.749259`, total `0.739976`, TGA SHA-256 `24b50fb227e1106c6e756551ac62384482808dc516825cc2b26f8d4fbe4438d5`; it is correct for its bound OBJ but is not the formal CS Workbench deployment artifact;
- CS Workbench screenshots on 15 July exposed deployment asset mismatch: the general/new-geometry atlas did not reproduce the same placement inside Workbench. Do not describe this as a failure of Theme/Style generation, weapon-space design, UV baking, or TGA production;
- `config/assets/ak47_workbench_official.json` now binds the official Workbench `OBJs/ak-47.obj` (SHA-256 `e0e2eab0...2e675`) to `UVSheets/ak-47.tga` (SHA-256 `c670e11e...bc60`). Formal CS deployment reads this official UV; it never generates a replacement unwrap;
- 1,432 of 13,069 official OBJ faces contain coordinates outside the 0-1 paint atlas. A diagnostic that forcibly repeated all of them produced `54.64%` overlapping atlas pixels and was rejected. The accepted `discard_outside` contract bakes only 11,637 official-atlas faces and treats the remainder as unpainted surfaces;
- official-atlas 512 edge sweep showed that asset constraints need adapter-specific calibration. The final 2048 run uses 16 px edge safety and simultaneously passes the original gates: corrected asset seam `0.004429`, corrected multi-view `0.682693`, and `96.16%` raw multi-view retention;
- the new Workbench candidate is `runs/nano_banana_marble_dynamic_style_refined/route_b_showcase_2048_official_workbench_uv/uv_baked_corrected__route-b__custom-paint-job__official-workbench-uv.tga`, SHA-256 `3eb5e0323f2ddcf2685c9d0d9e7c9329d123b9ecdaff1ee918ce6130652618b7`. PNG/TGA decoded pixels are identical. Status: `offline_pass_pending_cs2_workbench_reimport`;
- the 16 July reimport rejected that legacy-UV deployment hypothesis. The actual unified `weapons/models/ak47/weapon_rif_ak47.vmdl` contains `body_hd` (26,133 triangles) and `body_legacy` (13,483 triangles); the downloadable `weapon_rif_ak47.obj` matches `body_hd` exactly, while the older Workbench package is the legacy branch;
- generated `uv_baked_corrected.econitem` matches Valve's Custom Paint example on the mapping controls: scale `1.0`, offsets/rotation `0`, and `Ignore Weapon Size Scale=true`. The TGA origin bit also matches the Valve example, so finish selection, random placement, and the basic TGA header are not the cause;
- the earlier screenshot-only V-flip resemblance is not sufficient evidence. Viper's Workshop-confirmed AK UV sheet is pixel-aligned with our original new-CS2-OBJ wireframe in the normal displayed orientation, not vertically flipped. Keep the V-flip TGA only as a preserved diagnostic artifact; do not make it the next required import and do not change the renderer/baker convention from it;
- calibration references are preserved under `runs/uv_asset_diagnostics/viper_reference/`: AK UV SHA-256 `9eb7fe892fab327594e22d919d7befd90c44a5290289b1c7422179c75b99980b` and AK albedo SHA-256 `bbede432dce1c2ecee776887f37af73afbcac526dd3702469107fd537258ee72`. The page says maps are 4096, but the Wix endpoint exposed in this session returned 512 preview files; preserve that distinction;
- portability has two separate claims. Cross-game portability reuses the Theme/Style compiler, generation, weapon-space composition, evaluation, selection, and bounded feedback while a game-specific `GameAssetAdapter` binds the target game's authoritative mesh, UV/material contract, paintable range, cameras, and export format. Within-CS cross-weapon portability reuses the same Agent for AK-47, M4A4, M4A1-S, and other weapons while replacing each weapon's official OBJ/UV, semantic components, composition anchors, cameras, and export profile; it never means applying the same AK TGA to every weapon;
- Gemini Pro consumer subscription is not Developer API billing. Theme compilation can use the current free text tier, while Nano Banana 2 image generation needs Gemini Paid Tier. Current prepay setup generally requires at least $10; disable auto-reload and set a spend cap;
- current official estimate: Gemini 3.1 Flash Image 1K is about $0.067/image, so one A plus four B source assets is about $0.335 plus inputs;
- `src/skinsmith/style_planner.py` retains the reusable style library and candidate-direction infrastructure and now also owns dynamic StyleCompiler; blue-and-white porcelain planning remains useful but is no longer the next image-generation target;
- the first porcelain brief expands into four alternatives: peony medallion, landscape scroll, lotus pond, and ruyi geometry; the preserved plan is `runs/style_planning_blue_white/art_direction.json`;
- Route A and Route B share style vocabulary, palette, motifs, copyright boundary, and evaluation criteria, but Route A is planned as a complete arbitrary tile while Route B assigns one weapon-level composition to receiver, magazine, stock, handguard, and quiet muzzle roles;
- `DesignSpec.prompt_motif` now separates formal art motifs from the procedural `waves/diagonal/circuits` fallback, preventing technical test primitives from leaking into generation prompts;
- the supplied cat/dog image is a composition/readability reference only; do not copy any exact character, costume, pose, layout, watermark, or text, and do not store or redistribute the reference image;
- semantic anchor centers are derived from the mesh/masks rather than guessed: receiver canvas center approximately `(0.45, 0.20)`, magazine `(0.50, 0.56)`, stock `(0.14, 0.31)`, handguard `(0.72, 0.11)`, quiet muzzle after longitudinal `x=0.84`;
- the earlier generated Neon Tide wave is preserved but rejected as the final direction because it remains an abstract motif; it may be used only as historical/C+ exploration evidence;
- the old renderer was found to destroy character/hero art because each triangle used one UV-centroid colour; `ObjMultiViewRenderer` now defaults to barycentric per-pixel UV interpolation, bilinear texture sampling, and z-buffer visibility, while `sampling="flat"` is retained for a direct renderer ablation;
- a gradient triangle unit test proves that the barycentric renderer preserves more than eight colours inside one face; official UV-sheet binding and UV-address-mode tests are now included; 62 unit tests pass;
- full-AK barycentric visual/metric validation now runs on generated direction candidates; a formal 2048 TGA is selected and only Workbench visual confirmation remains before final-art acceptance.

Latest verified result:

- 62 unit tests pass, including official OBJ/UV-sheet hash binding, deployment UV addressing, candidate-direction job locking, role-specific source-contract validation, image/canonical anchor separation, Nano Banana A/B source-job planning, provider-neutral Theme/Style API payload/parsing/key-redaction tests, dynamic theme/style/weapon-space-plan compilation, generated-role layer expansion, asset creative profiles, ThemePack/StylePack validation, A/B semantic separation, automatic style resolution, style-pack planning, normalized source-crop placement and barycentric per-pixel UV rendering plus weapon-space generated layers, projection blending, canonical-frame/UV-bake, ablation, component feedback, selection, composition, asset, renderer, and generation tests;
- 2D baseline selects `candidate_02`;
- real AK-47 four-candidate run selects `candidate_02`;
- real run takes approximately 2.2 seconds;
- seam error typically improves from about 0.14–0.22 to 0.007–0.009;
- two consecutive real runs produced zero SHA-256 differences across 24 image files;
- `candidate_03` has the best multi-view score, but `candidate_02` has the best balanced final score.

Semantic evaluation accepted on 15 July:

- `ClipSemanticEvaluator` uses `openai/clip-vit-base-patch32`;
- pinned revision: `3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268`;
- input is the repaired texture plus left/right/top renders; the multiview contact sheet is excluded;
- `candidate_02` combined cosine: 0.28299; scaled semantic score: 0.70747;
- cached CUDA inference: about 3.76 seconds; peak allocated VRAM: about 0.584 GB;
- evidence: `runs/semantic_smoke/semantic_log.json`;
- this acceptance reused existing images and did not regenerate a texture.
- all four existing diffusion candidates were then rescored offline with the complete design description and 45% texture / 30% multi-view / 25% semantic weights;
- ranking remained `candidate_02`, `candidate_01`, `candidate_03`, `candidate_04`;
- semantic-aware `candidate_02` final score: 0.86054; semantic score: 0.70265;
- ranking evidence: `runs/semantic_existing_candidates/agent_log.json` and `run_summary.csv`.

Latest ranking is in `runs/real_model_smoke/run_summary.csv`. Full evidence is in `runs/real_model_smoke/agent_log.json`.

Bounded refinement accepted on 15 July:

- `BoundedRefinementAgent` executes exactly four Round-0 and two Round-1 candidates in separate preserved directories;
- Round-0 diagnosis found excessive multi-view detail (`mean_detail_score = 1.0`) and applied `larger clean shapes, reduced micro-detail`;
- the compact Round-1 prompt measured 73/77 CLIP tokens;
- Round-0 winner: `candidate_02`, score 0.86050;
- Round-1 winner: `candidate_01`, score 0.82772;
- improvement was -0.03278, so the 0.01 gate correctly rejected Round 1 and retained Round-0 `candidate_02`;
- full agent runtime: about 72.85 seconds;
- evidence: `runs/diffusion_refinement/agent_log.json` and `run_summary.csv`.

CS2 Workbench path validation completed on 15 July:

- the selected `candidate_02_seamless.png` imported successfully on the AK-47;
- three screenshots cover the left, top, and right views;
- the weapon surface is covered with no missing/transparent regions or obvious within-island seam at screenshot scale;
- technical path result: pass;
- visual-quality result: fail for final artwork — UV islands show abrupt blue-white/purple transitions, stripe detail is too dense, and the design lacks weapon-aware composition;
- use these screenshots only as pipeline evidence, not as the final showcase artwork;
- evidence: `runs/diffusion_refinement/workbench_validation.json` and `workshop_0000.png` through `workshop_0002.png`.

## 5. Current gaps, in priority order

This list supersedes older V-flip, legacy-UV, B0-runner, M4A4, and “build UI next”
notes elsewhere in historical documents.

1. Receive supervisor feedback and freeze the final report PDF.
2. Revisit the A0 poster and supervisor presentation only after a direct request;
   dissatisfaction is recorded, but revision is currently deferred.
3. Complete the final reproducibility, disclosure, copyright-boundary, and visual
   QA.
4. Keep approved changes synchronized with the published GitHub `main` branch.
5. Optionally import the accepted `artwork_04` TGA into Workbench for the final
   presentation screenshot; this is visual evidence, not a change to the UV route.

Already complete and not gaps: known-good HD AK OBJ/UV calibration, true Route-B
weapon-space/UV bake, formal A/B/C experiment, M4A4 transfer case, real single-
master Gemini acceptance, CLI/Python Agent orchestration, the real two-selection
workflow, mapped-readability recommendation, the thin Streamlit/replay client,
the revised report draft, the A0 academic poster, and the supervisor
presentation.

Known-good HD UV calibration prepared on 16 July:

- `scripts/make_known_good_uv_calibration.py` deterministically creates a 2048×2048 RGB calibration atlas on the new CS2 HD OBJ contract, with U/V corner blocks, a centre cross, and 24 stable major-island colours/labels;
- output: `runs/known_good_uv_calibration/ak47_hd_uv_calibration_2048__custom-paint-job.tga`, SHA-256 `aa1688c8e9ab3155b162fdf7ee0f514b0ddc588607b40a1fa67245abb82bfe77`;
- decoded PNG/TGA pixels are exactly identical and the TGA header is 24-bit; local barycentric left/right/top previews and a machine-readable manifest are preserved in the same directory;
- local visual review passed; no Nano Banana call, legacy UV, or V-flip convention was used;
- Workshop evidence: three 1280×720 fixed-setting left/right/top screenshots are preserved in the same directory and recorded with SHA-256 hashes in `calibration_manifest.json`;
- island-by-island visual comparison passes: the left cyan-stock/blue-magazine/purple-cover layout, right green-stock/red-magazine/orange-receiver layout, and top cyan-purple-blue ordering all match the local renders;
- status: `pass_known_good_hd_uv_export_import_contract`; there is no global V/H flip, rotation, offset, or island mismatch. Keep the normal-orientation 24-bit RGB TGA convention.

Calibrated marble Route-B re-export completed on 16 July:

- `scripts/weapon_space_route_b_smoke.py` now defaults back to `config/assets/ak47_cs2.json`; the retired legacy Workbench adapter and `official-workbench-uv` filename are no longer defaults;
- reused the exact preserved refined hero, secondary, connector, and background hashes; new image/API calls: zero;
- output directory: `runs/nano_banana_marble_dynamic_style_refined/route_b_showcase_2048_hd_calibrated/`;
- formal TGA: `uv_baked_corrected__route-b__custom-paint-job.tga`, SHA-256 `d6b8bbb830bf71f09f5f5d59f5cbb4b26c107759e8804984eaec120dc32237cc`;
- verified 2048×2048 RGB 24-bit, decoded PNG/TGA pixels identical, mesh hash `dae29ee5...4065654f`, 8 px edge safety, corrected asset seam `0.000441`, corrected multi-view `0.749464`;
- three Workshop screenshots confirm the receiver-led gold focal area, flow through stock/handguard/magazine, and quiet muzzle; there are no flipped/mismatched islands, mockup fragments, or rectangular source boundaries;
- final deployment status: `pass_route_b_new_hd_uv_workshop_deployment`; evidence hashes and conclusions are recorded in `deployment_validation.json`.

True weapon-space A/B/C runner update and first formal run on 16 July:

- `src/skinsmith/ablation.py` no longer implements B as B0 mask-aware remapping. A now receives one pattern source per candidate, while B receives distinct hero/secondary/connector/background sources, composes them on continuous weapon-space canvases, bakes through the new-HD position/normal UV maps, and applies the locked 8 px seam band;
- fairness is now correctly recorded as shared theme/style/palette/backend/resolution/base candidate seeds/asset/cameras/metrics, while route-specific generation logic remains different; the same generic square source is explicitly not required;
- `scripts/abc_ablation_formal.py` runs four deterministic marble-theme technical candidates without paid/API image calls, preserving the Nano Banana marble result separately as the final-art/deployment case;
- evidence: `runs/abc_ablation_true_weapon_space/ablation_log.json`, `ablation_summary.csv`, per-candidate sources/canvases/textures/renders, and `visual_validation.json`;
- paired B-A asset seam improvement: mean `0.269344`, median `0.269142`, win rate `100%`, bootstrap 95% CI for the mean `[0.247543, 0.291145]`;
- paired B-A multi-view improvement: mean `0.060124`, median `0.066701`, win rate `100%`, bootstrap 95% CI `[0.036363, 0.077307]`;
- the older component-detail targets assign zero balance to all four B candidates and produce mean agent-score change `-0.124828`. Visual review shows this is driven by high-contrast connector/detail lines exceeding targets calibrated on B0; retain and report this as a negative metric-validity caveat, and do not post-hoc change weights/targets to manufacture a positive result;
- selected B is `candidate_04`; both C candidates modify only `barrel_muzzle` plus a 24 px halo, with zero changed pixels outside the halo, asset seam about `0.000796`, and multi-view about `0.8429`;
- C Round 1 improves the locked agent score by `-0.000880`, below `+0.01`, so it correctly rolls back to B Round 0;
- C was subsequently expanded across all four B candidates: every diagnosis targets the over-detailed `barrel_muzzle`; the best attempted locked-score changes are `-0.001097`, `-0.001095`, `-0.000816`, and `-0.000880`;
- all eight attempted C textures pass the seam constraint, and every selected attempt has zero changed pixels outside the target component plus 24 px halo;
- all four final C outcomes roll back to B, so paired final C-B changes are exactly zero. Report this as safe no-regression behavior; do not imply that no correction was attempted;
- 63 unit tests pass, including the new zero-outside-halo regression test.

Report-ready ablation tables completed on 16 July:

- `scripts/build_report_ablation_tables.py` deterministically extracts the preserved formal A/B/C log and the fixed-candidate edge-width/selection-policy sub-ablation;
- outputs under `runs/report_ready_ablation_tables/`: paired summary, per-candidate A/B metrics, formal-B seam before/after, all C attempts/locality, edge sweep, selection policy comparison, manifest, and Chinese report-ready Markdown;
- the four formal B candidates average `99.62%` relative asset-seam improvement and all pass the `0.01` threshold;
- reporting boundary is explicit: the old edge-width sweep supports seam operating-point and selection-policy claims only, not final-art superiority.

M4A4 GameAssetAdapter transfer completed on 16 July:

- official `weapon_rif_m4a4.obj` extracted from the already local Valve geometry ZIP; SHA-256 `37179368f9bcd869776d3f7a34bfad39125b74ca02ba9f394dfd6c9b307b4a55`;
- M4A4 statistics: 45,422 triangles, 39,881 UVs, 1,747 UV islands, 11,341 true seam pairs, 60.62% valid coverage at 512, 0.29% overlap pixels;
- `src/skinsmith/game_asset_adapter.py` now binds each asset's mesh/UV/export contract and canonical axes; both AK and M4A4 use this shared adapter path;
- M4A4 reused the preserved marble semantic sources with zero image/API calls and successfully produced continuous canvases, UV maps, baked atlas, and left/right/top renders;
- raw seam `0.084939`, raw multi-view `0.695145`; the AK-equivalent all-edge band reaches seam `0.004915` but only 87.37% retention;
- paired-colour seam averaging plus a minimum passing interpolation reaches seam `0.009938` and 94.02% retention, still below the locked 95%;
- final status: `partial_pass_core_transfer_success_joint_constraints_fail`. Core cross-weapon portability is supported, while seam correction is shown to require asset-specific topology-aware improvement;
- evidence: `runs/m4a4_game_asset_adapter_transfer/transfer_final.json` and `TRANSFER_VALIDATION_ZH.md`. Do not add a third weapon.

Environment/safety status:

- project dependencies now use the independent `.venv`; do not install into or run from shared Anaconda base;
- failed `.conda-env` residue has been removed;
- SD-Turbo loads without an active safety checker; keep it local, restrict prompts to original and rights-safe visual designs, manually review outputs, and do not expose an unfiltered public service.

Renderer limitation: the current software renderer now uses barycentric per-pixel UV interpolation, bilinear texture sampling, and a z-buffer; it still uses simple orthographic projection and flat per-face lighting, so it is not a photorealistic replacement for CS2 Workbench. Legacy centroid/painter rendering remains only as an ablation mode.

## 6. Immediate next actions

Execute in this order unless the user changes priority:

1. Receive supervisor feedback and freeze the final report.
2. Leave the poster and presentation unchanged until the user resumes that work.
3. Complete reproducibility, disclosure, copyright-boundary, and visual QA.
4. Follow `SECURITY_RELEASE_CHECKLIST.md` for every subsequent GitHub update.
5. Do not add a third weapon, return to legacy UV, or resume per-part dragon
   generation before deliverables are stable.
Implementation checkpoint (2026-07-16):

- `src/skinsmith/agent_runtime.py` now includes `ArtworkCandidate`, the `awaiting_artwork` phase, persisted original/preview groups, explicit `artwork_choice`, and exact selected-source handoff to formal execution.
- `src/skinsmith/route_execution.py` generates four compositionally distinct landscape variants, validates each, maps each at configurable preview resolution, and preserves source plus mapped previews before selection. Formal execution records and reuses the selected candidate instead of drawing another image.
- `src/skinsmith/agent_tools.py` enriches cached and generated themes with related symbolic, environmental, atmospheric, and micro-detail ingredients; the dragon cache explicitly includes clouds, waves, treasure, flaming pearls, mountains, lightning, mist, jade, and architectural ornament.
- Gemini defaults are now 16:9 for master artwork while Route A remains square; the master source gate requires landscape format, dense local detail, multiple medium/small clusters, little dead space, and no dominant full-width subject.
- `scripts/run_skinsmith_agent.py` supports `--artwork`. The intended CLI sequence is direction selection -> `awaiting_artwork` -> artwork selection -> formal 2048/TGA execution.
- Real multi-candidate run: `runs/agent_dragon_multicandidate_v1/` is now
  `completed`, locked to `candidate_04_d4_mythic_relic` and `artwork_04`, with 4
  artwork candidates, 6 image calls, 1 role retry, and 1 bounded refinement round.
  At its preserved second checkpoint, `artwork_03` was correctly rejected
  once for isolated sticker-like clusters and excessive dark gaps, then regenerated
  locally. All four final sources are 1376×768, have zero low-detail grid patches,
  pass Gemini semantic/composition review, and pass the 256 preview-bake seam gate.
- Preview totals: artwork_01 `0.811703`, artwork_02 `0.807840`, artwork_03
  `0.785085`, artwork_04 `0.842104`. These scores support inspection but do not
  replace the user's source-plus-three-view art choice.
- Final real selection: `artwork_04`. Its source and formal canonical source share
  SHA-256 `0299f43512b9a946eeedc0a58c418424c7bddfad8e0c9dd54610a4c13f63750a`.
  Formal Route B selected 4 px, asset seam `0.000777611`, multi-view `0.816620`,
  total `0.829123`, and passed all constraints. Route C changed the score by
  `-0.021959` and rolled back. Final TGA SHA-256 is
  `82d18671e50cf59501c901ad86916a04637464883e79d5375b4cb37f96bc2aac`;
  the 2048 RGB PNG and TGA decoded pixels are identical.
- `src/skinsmith/mapped_readability.py`,
  `GeminiMappedReadabilityReviewer`, and
  `scripts/evaluate_mapped_readability.py` add explainable design-element matching.
  The stored `mapped_element_readability.json` is explicitly recommendation-only:
  source fulfillment `0.938562`, left `0.601634`, right `0.601634`, top
  `0.399346`, multiview readability `0.571291`, recommendation `0.665637`, with
  8/16 elements above the `0.55` visibility threshold. Human selection remains
  authoritative and these values are not hard constraints.
- The runtime deliberately stops at `awaiting_direction` or `ready_to_execute` when the corresponding real tool is absent; it does not report a generated skin from planning-only execution.
- Existing `StylePlanner` output can be adapted into the richer Agent direction contract through `directions_from_style_plan`.
- `tests/test_agent_runtime.py` covers direction planning, contract locking, persisted resume, bounded tool calls, evidence-backed memory, execution results, and the existing-style adapter.
- `src/skinsmith/agent_tools.py` now registers a real `CreativePlanningTool`: AssetCreativeProfile validation -> ThemeCompiler -> conditional dynamic StyleCompiler -> StylePlanner -> rich Agent directions, with a planning manifest and evidence-backed memory snapshot.
- `scripts/run_skinsmith_agent.py` is the first thin CLI client over the same Agent API. It supports cached offline planning or live OpenAI/Gemini structured compilation for uncached briefs, and honestly stops before generation until `execute_design` is registered.
- Offline CLI smoke evidence is preserved under `runs/agent_runtime_smoke/`: the cached wild-lotus brief produced three distinct directions, a planning manifest, memory snapshot, event log, and resumable `awaiting_direction` checkpoint.
- `src/skinsmith/route_execution.py` now provides the real `execute_design` stage for Route A/B/C: five generated sources, provider-neutral structural source gates, role-local retry, Route-A seamless/mapped evaluation, Route-B weapon-space composition, known-good HD OBJ/UV bake, edge-width hard-constraint/Pareto selection, and one bounded receiver-focal weapon-space correction with two intensities, no new image call, locality measurement, +0.01 acceptance, and rollback.
- `src/skinsmith/source_validation.py` validates square isolated-role assets and landscape master artworks, including size/aspect, local density, dead-space ratio, border/slab drift, and optional Gemini multimodal composition/forbidden-content review.
- `scripts/run_skinsmith_agent.py` supports three resumable stages: plan to `awaiting_direction`; resume with `--direction` to generate and pre-map artwork candidates; resume with `--artwork` at 2048 for formal TGA export.
- A synthetic-backend integration test exercises the same executor through the known-good HD AK OBJ/UV, actual weapon-space bake, renderer, seam metric, and selection without claiming synthetic images as art evidence.
- Failed role attempts are preserved as separate images and hashes; the canonical role filename is written only after that role passes. Regression coverage confirms that a failed connector retries only connector and consumes exactly one image-call and one role-retry budget unit.
- The synthetic integration run also covers Route C and verifies zero changed pixels outside its weapon-space target halo. It is technical orchestration evidence, not visual-quality evidence.
- The previously uncached live Agent acceptance is complete under `runs/agent_live_astrolabe/`. Revisions 01 and 02 accidentally used the retired legacy Workbench adapter and are explicitly rejected as final evidence. Revision 04 remaps both existing Route A and Route B with zero new image calls under `cs2_ak47_new_geometry`, mesh SHA-256 `dae29ee5...4065654f`, the known-good normal-orientation mesh-derived UV, and a 2048 RGB export.
- The live brief produced four directions and selected `Radial Orrery`. The budget was explicitly extended from 8 to 12 image calls after a preserved failure; actual use remained 9. Secondary, connector, and background were corrected through role-local evidence-preserving revision rather than full regeneration.
- Revision-04 Route A records asset seam `0.111407`, multi-view `0.829641`, and total `0.793197`; it fails the locked asset-seam constraint. Route B selects 12 px, records asset seam `0.000187`, multi-view `0.794076`, total `0.792397`, and passes all hard constraints. Constraint-first selection therefore correctly chooses B even though A has slightly higher soft scores.
- Route C used zero additional image calls, failed the `+0.01` improvement rule with `-0.029224`, and rolled back. Automatic soft-alpha extraction removed the previously visible rectangular source boundaries.
- Final Route-B TGA: `runs/agent_live_astrolabe/execution/revisions/revision_04/route_b/selected__route-b__custom-paint-job.tga`; SHA-256 `a03336d7473393357b182d647c02432df1812c362f16bca0b9817e85e3c1eff7`; PNG/TGA decoded pixels are identical. Acceptance record: `runs/agent_live_astrolabe/AGENT_ACCEPTANCE_ZH.md`.

Technical-contribution framing is documented in `TECHNICAL_CONTRIBUTIONS.md`. The locked enhancement scope is: mesh-derived canonical frame and UV position/normal maps; weapon-space whole-composition baked to UV; mesh-derived UV seam graph/metric; paintable and component masks as secondary constraints; constraint-first plus Pareto candidate selection; at least one local corrective action; A/B/C ablation; and M4A4 transfer through `GameAssetAdapter`. Internal five-person team blind rating is not primary evidence because of conflict/bias; automatic metrics, ablations, and Workbench cases are primary, with external non-team preference ratings optional.

Component-relationship composition graph upgrade accepted offline on 16 July:

- `ThemePack` now optionally carries validated `composition_groups`. Each theme element belongs to exactly one group; group modes are `spanning`, `grouped`, `independent`, or `background`.
- A group records its element IDs, target components, narrative purpose, left/right/top surfaces, right-side mirroring, and whether a deliberate muzzle focal subject overrides the default quiet-muzzle rule.
- Existing cached ThemePacks without groups keep the exact legacy four-role fallback, so marble/astrolabe evidence remains reproducible.
- New structured Theme API schemas require composition groups. New image jobs are named by group (`route_b_{group_id}.png`) instead of collapsing multiple hero or connector subjects into one role file.
- `route_b_composition.py` compiles spanning groups into one continuous wide weapon-space layer across all assigned component anchors; grouped/independent units compile into component-specific consumers of the same source; background remains a shared full-weapon field.
- `route_execution.py` now validates, retries, preserves, and reloads multiple files that may share one semantic role without filename collisions.
- `config/design_themes/celestial_dragon.json` is the first explicit acceptance scenario: dragon body spans stock/receiver/handguard, claw marks are independent on the magazine, dragon head spans front assembly/muzzle with an intentional muzzle focal override, cloud flow connects the silhouette, and lacquer is the shared background.
- Preserved no-image-call evidence: `runs/composition_graph_dragon/route_design_bundle.json`. It compiles 5 composition groups into 5 image jobs and 8 weapon-space layers; `quiet_strength` becomes `0.0` because the dragon-head group explicitly permits muzzle focus.
- `src/skinsmith/uv_region_composition.py` is now the explicit-graph Route-B path. For each group it derives the exact semantic face set and per-UV-pixel component union from the locked OBJ/AssetSpec, filters the requested left/right/top surfaces, samples the generated source through canonical position, and hard-clips all pixels outside the declared group region.
- Gemini image generation can receive a procedural scope-guide reference. Spanning groups receive a bounded horizontal allowed zone with component divisions; generated content outside the allowed zone is treated as removable background. Historical graph bundles that lack the newer `composition_mode` and `target_components` fields recover them from `weapon_theme.composition_graph`.
- Live evidence is preserved under `runs/agent_dragon_composition_dynamic_style/`. The first seven-call execution passed numeric constraints but was visually rejected because the dragon-body source formed a firearm silhouette and the head source was a complete circular dragon.
- An offline remap of those unchanged sources proved the exact UV-region path but also proved that correct geometry cannot repair a semantically invalid source.
- Revision 01 used two additional Gemini calls with scope-guide references and the exact UV-region compositor. Route B selected 4 px, asset seam `0.001259`, multi-view `0.775128`, total `0.791333`, and passed all hard constraints. Image-call use is now 9 of an explicitly extended 12.
- Revision 01 is still **not final-art accepted**: the body source is a complete dragon rather than torso/tail only, while the head source is claw/blade decoration on a framed slab rather than a head plus short neck. The mapped group boundaries are correct; source semantics are wrong. Review evidence: `hero_group_review_revision_02.json`.
- Historical conclusion: the graph geometry was valid, but per-part semantic generation was unnecessarily fragile. The run is frozen as negative/design-motivation evidence and is not scheduled for further hero retries.

Default Route-B art-model decision on 16 July:

- The per-group dragon retry is stopped. Its evidence remains useful for showing why asking an image model to generate separate anatomical/component assets adds unnecessary semantic failure modes.
- The product-default Route B now generates exactly one `master_artwork` source.
- The master artwork must be visually strong, dense, richly detailed, edge-to-edge, and robust under crop. It may contain a complete dragon, marble veins, clouds, flowers, machinery, or another original theme; the Agent does not require a particular subject part to appear at a predetermined component.
- The same source is fitted to continuous left/right/top weapon canvases. The locked OBJ canonical position and normal maps then sample those canvases into the fragmented UV atlas. This is automatic image cutting/repacking, not direct painting on UV islands.
- Acceptance focuses on source image quality/density, forbidden text/logo/mockup content, UV seam constraints, and mapped left/right/top visual quality. It does not require detecting whether a dragon head, tail, claw, or other semantic subpart landed on a named component.
- Composition groups, exact component-region fitting, and multimodal part review remain preserved optional research branches, not the main user workflow.

Real Gemini master-artwork acceptance on 16 July:

- Run: `runs/agent_dragon_master_artwork/`; selected direction: `candidate_01_dir_01_gold_ink / Classic Gold Ink`.
- The run used the known-good `cs2_ak47_new_geometry` AssetSpec, 2048 OBJ-derived UV bake, and `continuous_master_artwork_obj_uv_bake`; it never used legacy UV.
- The first source mapped well but exposed that global density alone could miss local dead zones (`low_detail_patch_ratio = 0.111111`). The validator now measures a 6 x 6 local-detail grid and rejects ratios above `0.10`.
- A denser retry produced a visible firearm silhouette. This invalid high-scoring attempt is preserved, and the Gemini master-artwork reviewer is now deliberately narrow: it ignores dragon-head/body/component placement but rejects weapons, weapon parts, mockups, UV layouts, text, logos, watermarks, borders, framed panels, and presentation boards.
- Attempt 03 was automatically rejected as a framed-panel composition. Attempt 04 passed with no forbidden content, `detail_density = 0.306265`, `low_detail_patch_ratio = 0.0`, and minimum local detail density `0.151305`.
- Five image calls were used in total: one Route-A source plus four preserved Route-B master-artwork attempts. Only `master_artwork` was regenerated; Route A, direction, palette, style, OBJ/UV, and all previous evidence were reused.
- Accepted artifact: `runs/agent_dragon_master_artwork/execution/revisions/revision_02/route_b/selected__route-b__custom-paint-job.tga`.
- Accepted Route B selects 4 px edge safety, asset seam `0.000305723`, multi-view `0.792136`, total `0.787674`, multi-view retention `0.995283`, and passes all hard constraints.
- Visual review passes the final source and AK left/right/top previews: coherent black/gold/teal dragon-scale and cloud language covers stock, receiver, magazine, handguard, and top surfaces without weapon/mockup fragments or framed-source boundaries.
- Future direction planning now describes master-artwork crop robustness instead of the old “head at muzzle/body at receiver” contract. Explicit composition-graph planning remains available only when requested.

Locked experiment design:

- A = generic square/tileable pattern + Custom Paint;
- B = coherent weapon-space layout + UV position/normal-map bake + paintable/component constraints + asset seam handling + Custom Paint;
- C = B Round 0 reused, then render-conditioned local correction with two new candidates and the existing 0.01 rollback gate;
- C+ = one best C candidate with Gunsmith material enhancement for Workbench/PPT/poster only, excluded from ablation statistics;
- sub-ablation 1 compares B before/after asset seam correction using identical candidates;
- sub-ablation 2 compares weighted ranking against constraint-first/Pareto using the identical candidate pool;
- A/B/C share theme, palette, seed, model revision, candidate count, resolution, AK-47, Custom Paint, cameras, and common metrics;
- Workbench lookup is now local and locked: formal A/B/C all use `Custom Paint Job`; optional Route-A `Hydrographic`/`Spray-Paint` previews are showcase-only; C+ uses `Gunsmith`. Consult `WORKBENCH_VIEWING_GUIDE.md` or `config/workbench_finish_profiles.json`, not the Valve website, for routine checks;
- formal TGA names append both route and finish style: `__route-a__custom-paint-job`, `__route-b__custom-paint-job`, `__route-c__custom-paint-job`, or `__route-c-plus__gunsmith`;
- report paired B-A and C-B mean/median/std, win rate, and bootstrap 95% CI; no internal team rating is required.

Refinement implementation status:

- `src/skinsmith/refinement.py` owns structured diagnosis, Round-1 spec creation, and the 0.01 acceptance threshold;
- Round 1 is fixed to two candidates at `base_seed + 1000` and `base_seed + 1001`;
- `DesignSpec.refinement_directives` records feedback without changing the evaluation text;
- the refinement prompt uses a compact template because the accepted Round-0 prompt already consumes 74/77 CLIP tokens;
- the complete real-model feedback loop passed and correctly rejected a lower-scoring refinement;
- `pytest` is not installed in the clean `.venv`; tests use the repository's built-in `unittest` suite and no package was added solely for execution.

The Workbench calibration, formal ablation runner, M4A4 transfer, uncached Agent CLI/API acceptance, offline composition-graph gates, real single-master acceptance, real Gemini multi-candidate source-plus-three-view selection chain, recommendation-only mapped readability review, and thin Streamlit client are complete. The next stage is report/poster/presentation production; do not add a third weapon, switch to legacy UV, or broaden the route.

Thin Streamlit client accepted on 16 July:

- `streamlit_app.py` is a thin UI over `scripts/run_skinsmith_agent.py`; it does not reimplement planning, generation, UV baking, evaluation, checkpoint, or export logic.
- replay mode discovers preserved `agent_run_result.json` records and defaults to `runs/agent_dragon_multicandidate_v1/`;
- each artwork is presented as one indivisible source + left + right + top candidate card;
- the client shows selected direction/artwork, phase, events, budgets, retries, refinement use, Route-C rollback, recommendation-only mapped readability, and final PNG/TGA downloads;
- new-task mode accepts a free brief and optional style family, then uses the existing `awaiting_direction` and `awaiting_artwork` resume checkpoints;
- formal artwork selection resumes at 2048 with TGA export and reuses the exact human-selected source;
- `src/skinsmith/replay.py` provides repository-bounded persisted-path resolution and replay loading;
- two replay unit tests pass, `compileall` passes, the accepted run resolves to completed / `candidate_04_d4_mythic_relic` / `artwork_04` with 6 image calls, 1 retry, and 1 refinement round, and headless Streamlit startup reaches a live local URL.

Gemini unknown-theme planning compatibility fix on 16 July:

- the first Streamlit free-brief test (`deep-sea ruins`, style family `Material`) reached the uncached ThemeCompiler and failed before any image call with HTTP 400 `invalid_request`;
- cached-theme runs had not exercised the enlarged live ThemePack schema;
- this account's working rollout contract is `/v1beta/interactions` with `Api-Revision: 2026-05-20` and object-form `response_format`; `/v1beta2/interactions` returns 404 for this project;
- optional `composition_groups` were removed from the live unknown-theme structured schema because default Route B uses one master artwork and Gemini rejected the enlarged schema; explicit groups remain supported by cached/hand-authored research themes and local validation;
- the exact failed brief was rerun without image generation under `runs/streamlit_api_fix_validation_v4/`;
- live result: `awaiting_direction`, with `Clockwork Blooming`, `Crusted Architrave`, `Hydrothermal Leak`, and `Submerged Cipher`;
- no image call was consumed during diagnosis or validation.

Three-checkpoint keyword workflow accepted on 16 July:

- `AgentPhase.AWAITING_THEME` is now persisted before `awaiting_direction` and `awaiting_artwork`;
- the runtime remains backward-compatible with older `plan_directions` tools, while clients that register `expand_theme` receive the new checkpoint;
- `CreativePlanningTool.expand_theme` exposes the validated ThemePack concept, narrative, palette, semantic roles, related world elements, evaluation criteria, provenance mode, and source path;
- theme confirmation resumes through CLI `--confirm-theme`; Gemini is the configured default creative provider so checkpoint resume does not silently lose its backend;
- after theme confirmation, direction style is dynamically synthesized for the confirmed theme/weapon instead of reusing an unrelated cached style;
- direction count automatically remains within the accepted 3-4 range when a validated style exposes only three alternatives;
- Streamlit now asks for a weapon and short keyword, displays the theme expansion, and labels the three human checkpoints explicitly;
- weapon selector status is honest: AK-47 full end-to-end is enabled; M4A4 transfer evidence is shown but formal execution is disabled;
- replay loading now supports in-progress checkpoint-only runs as well as completed `agent_run_result.json` records;
- live smoke `runs/agent_three_checkpoint_dragon_smoke_v4/` used the exact input `dragon`, stopped at `awaiting_theme`, then after confirmation produced four relevant directions: `Minimalist Calligraphic`, `Opulent Lacquer`, `Cloud-Enveloped`, and `Relief Carving`;
- this smoke made no image calls; full regression is 100 tests passing and Streamlit headless startup passed.

## 7. Commands and expected results

Run from the project root with the configured Python:

```powershell
& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v
& '.\.venv\Scripts\python.exe' scripts\smoke_test.py
& '.\.venv\Scripts\python.exe' scripts\real_model_smoke_test.py
```

Expected as of this status date:

- 100 tests pass;
- both smoke scripts complete;
- both select `candidate_02`;
- real-model outputs appear under `runs/real_model_smoke/`;
- `agent_log.json` and `run_summary.csv` are regenerated.

Diffusion full-chain command after the one-time download:

```powershell
$env:HF_HOME = "$PWD\third_party\huggingface"
$env:HF_HUB_OFFLINE = "1"
& '.\.venv\Scripts\python.exe' scripts\diffusion_real_model_test.py
```

Python/environment:

- Python: project-local `.venv\Scripts\python.exe`, Python 3.13;
- GPU: NVIDIA RTX 4060 Laptop, 8GB VRAM;
- PyTorch: 2.9.1+cu128, CUDA available;
- available: NumPy, Pillow, OpenCV, SciPy, Torch, Transformers, Streamlit, Safetensors;
- installed for generation: PyTorch 2.9.1+cu128, Diffusers 0.39.0, Accelerate 1.14.0, Transformers 5.13.1;
- absent at last check: Trimesh, Pyrender, Blender.

## 8. Important files

- `TECHNICAL_SPEC.md`: authoritative locked technical route and parameter specification; consult before changing models, weights, formulas, or experiments.
- `TECHNICAL_CONTRIBUTIONS.md`: authoritative contribution/novelty framing and reusable report/PPT/poster wording.
- `PROJECT_OVERVIEW.md`: user/team-facing scope and phase explanation.
- `PROJECT_STRUCTURE.md`: current six-layer architecture, directory ownership, entrypoints, and phase boundary.
- `WORKBENCH_VIEWING_GUIDE.md`: authoritative local A/B/C Workbench inspection and TGA naming memo.
- `PROGRESS_AND_COMPLETION_CHECKLIST.md`: user-facing current progress, two-layer portability statement, completion criteria, and next-session checklist.
- `NEXT_SESSION_HANDOFF.md`: concise current-task handoff with completed work, exact real-run checkpoint, direction IDs, resume commands, remaining deliverables, and non-negotiable boundaries.
- `SECURITY_RELEASE_CHECKLIST.md`: GitHub publication candidate, secret-scan
  result, required exclusions, and pre-stage/post-stage release gates.
- `VERIFICATION.md`: exact verification evidence and interpretation.
- `PROJECT_PLAN.md`: dated delivery plan.
- `README.md`: setup and quick start.
- `src/skinsmith/generator.py`: generator interface, procedural/local diffusion baselines, and `ApiTextureGenerator` adapter.
- `src/skinsmith/api_backends.py`: OpenAI/Gemini structured theme/style and image REST adapters with redacted traces.
- `src/skinsmith/route_asset_generation.py`: provider-neutral A/B internal image-job planner.
- `src/skinsmith/route_b_composition.py`: generic RouteDesignBundle-to-WeaponDesignPlan compiler with explicit component-relationship graph placement plus the preserved four-role legacy fallback.
- `config/creative_api.json`: locked Gemini/Nano Banana provider, exact model IDs, image size, candidate gate, and acceptance boundary.
- `config/workbench_finish_profiles.json`: machine-readable finish-style controls and route-aware TGA suffixes.
- `src/skinsmith/style_planner.py`: general style-pack loader, dynamic StyleCompiler, and A/B art-direction planner.
- `src/skinsmith/design_routes.py`: AssetCreativeProfile, injectable ThemeCompiler, ThemePack, distinct PatternDesigner/WeaponThemeDesigner, and Route-C contract.
- `config/styles/*.json`: blue-and-white porcelain, original mascot, and retro-futurist neon style knowledge packs using one schema.
- `config/styles/modern_chinese_botanical.json`: default independent style for the Wild Lotus theme.
- `config/design_themes/wild_lotus.json`: hero/secondary/connector/background elements and seven-component weapon narrative.
- `config/design_themes/celestial_dragon.json`: spanning/grouped/independent/background composition-graph acceptance theme.
- `runs/composition_graph_dragon/route_design_bundle.json`: no-image-call proof that five art groups compile into named jobs and dynamic weapon-space layers.
- `runs/master_artwork_dragon/route_design_bundle.json`: no-image-call proof that the default planner emits exactly one `master_artwork` source and the continuous-canvas/OBJ-UV-bake pipeline.
- `runs/agent_dragon_master_artwork/execution/revisions/revision_02/`: accepted real Gemini single-master-artwork run, local-density/forbidden-content retry evidence, mapped previews, metrics, and final 2048 TGA. Final source SHA-256 `ee808922...bd5d19`; TGA SHA-256 `2cf32fc0...a1a0a`.
- `config/assets/ak47_weapon_space_anchors.json`: normalized semantic anchors used by the route-design plan.
- `scripts/plan_design_routes.py`: natural-language brief to corrected A/B/C route-design bundle.
- `scripts/generate_route_assets.py`: Nano Banana/OpenAI internal source generation with per-call traces and hashes; supports role-local B regeneration through repeatable `--role`; outputs are not accepted before mapping.
- `scripts/preview_route_a_asset.py`: generated Route-A raw/repaired tiling, real-AK mapping, multiview scoring, and asset-seam evidence.
- `runs/theme_compilation_chip_circuit/recorded_agent_theme.json`: preserved uncached Codex-agent theme response.
- `runs/theme_compilation_chip_circuit/route_design_bundle.json`: accepted chip-circuit A/B/C design contract.
- `runs/theme_compilation_marble_dynamic_style/`: live Gemini Theme+Style compilation evidence and redacted traces for the marble/gold-vein brief.
- `runs/nano_banana_marble_dynamic_style/`: preserved Round-0 five-image Nano Banana smoke, checkpoint/traces/hashes, mapped Route-A evidence, and dynamic weapon-space Route-B evidence; technical smoke passes, final art fails source compliance.
- `runs/nano_banana_marble_dynamic_style_refined/`: two-call hero/connector correction, anchor-fixed selection, preserved new-geometry TGA, failed legacy-Workbench-UV adapter evidence, and the current Source2 V-axis diagnostic.
- `runs/nano_banana_marble_dynamic_style_refined/route_b_showcase_2048/workbench_mapping_diagnosis.json`: current engine/VPK evidence, failed screenshot hash, V-flip hypothesis, diagnostic TGA hash, and one-import acceptance test.
- `runs/nano_banana_marble_dynamic_style_refined/official_workbench_uv_manifest.json`: diagnosis, rejected wrap attempt, official asset hashes, edge sweep, selected 2048 metrics, and reimport gate.
- `runs/nano_banana_marble_candidates/`: direction-locked `tectonic_cluster` first round, targeted three-role retry, failed/fixed anchor mappings, manifests, and final two-candidate comparison.
- `runs/design_planning_wild_lotus/route_design_bundle.json`: preserved no-generation Wild Lotus design contract.
- `scripts/plan_style.py`: natural-language brief to preserved multi-candidate `ArtDirectionSpec` CLI.
- `runs/style_planning_blue_white/art_direction.json`: four-direction porcelain planning evidence from one user brief.
- `src/skinsmith/seamless.py`: seam metric and repair.
- `src/skinsmith/obj_renderer.py`: OBJ/UV loader with polygon triangulation and multi-view renderer.
- `src/skinsmith/uv_asset.py`: mesh welding, UV islands, asset seam graph/metric, and diagnostics.
- `src/skinsmith/asset_spec.py`: versioned asset binding and ordered semantic-region configuration.
- `config/assets/ak47_cs2.json`: locked new-CS2 AK-47 adapter and semantic rules.
- `config/assets/ak47_workbench_official.json`: retired legacy deployment-diagnosis adapter retained only as historical evidence; do not use it as the Agent default or formal HD route.
- `scripts/uv_asset_diagnostics.py`: preserved AK-47 UV diagnostic runner.
- `scripts/prepare_ak47_route_b.py`: reproducible Route-B mask and calibration preparation.
- `src/skinsmith/uv_compositor.py`: component-aware soft composition and UV-edge safety correction.
- `src/skinsmith/selection.py`: hard constraints, Pareto front, deterministic selection, and weighted baseline.
- `src/skinsmith/component_feedback.py`: semantic visibility rendering, per-component detail metrics, diagnosis, and local style action.
- `config/route_b.json`: locked Route-B component styles, 8 px edge width, thresholds, and objectives.
- `scripts/route_b_composition_smoke.py`: deterministic B-before/B-after path test.
- `scripts/route_b_edge_sweep.py`: fixed-candidate width sweep and selection sub-ablation.
- `scripts/route_c_local_refinement.py`: two-candidate local action and +0.01 rollback smoke.
- `src/skinsmith/ablation.py`: shared-source A/B/C runner; its first output currently evaluates B0 and is diagnostic, not formal Route B evidence.
- `scripts/abc_ablation_smoke.py`: B0 negative/control run retained under `runs/abc_ablation_smoke/`.
- `src/skinsmith/weapon_space.py`: canonical weapon frame, per-UV-pixel geometry maps, continuous weapon-space canvases, and UV baking.
- `config/weapon_design_plan.json`: current focal zone, longitudinal flow, quiet zone, anchors, palette, and canvas parameters.
- `config/weapon_design_showcase_plan.json`: content-ready Route-B plan with a restrained generated material layer and projection blend power.
- `config/themes/night_shift_critters.json`: legacy pre-StylePack character-theme record retained as design-history evidence.
- `config/showcase_character_prompt.json`: earlier character-led 2:1 prompt retained as art-direction history, not the project-wide fixed theme.
- `config/showcase_hero_prompt.json`: rejected abstract Neon Tide prompt retained as design-history evidence.
- `assets/showcase/neon_tide_hero_v1.png` and `.json`: frozen built-in generated wave asset, hash and restricted showcase-only provenance; not formal A/B/C evidence.
- `scripts/weapon_space_route_b_smoke.py`: accepted 512 true Route-B geometry/bake/render smoke and concept-figure generator.
- `runs/weapon_space_route_b_smoke/weapon_space_log.json`: map statistics, seam metrics, multi-view metrics, plan, and asset binding.
- `runs/weapon_space_route_b_smoke/visual_validation.json`: explicit visual acceptance and final-art limitation.
- `runs/weapon_space_route_b_smoke/route_b_weapon_space_concept.png`: report/PPT-ready coherent-space -> fragmented-UV -> 3D-reconstruction figure.
- `runs/weapon_space_projection_blend_smoke/weapon_space_log.json`: projection-only control after replacing the hard chart switch.
- `runs/weapon_space_content_smoke/weapon_space_log.json`: generated-content integration metrics, exact source hash, plan, and outputs.
- `runs/uv_asset_diagnostics/uv_asset_log.json`: machine-readable UV evidence.
- `runs/route_b_asset_prep/asset_prep_log.json`: version, mask coverage, component statistics, and outputs.
- `runs/route_b_composition_smoke/composition_log.json`: compositor parameters, seam ablation, and multi-view evidence.
- `runs/route_b_edge_sweep/edge_sweep_log.json`: operating-point and Weighted/Pareto evidence.
- `runs/route_c_local_refinement/agent_log.json`: Route-C diagnosis, locality, hard-gate, and rollback evidence.
- `src/skinsmith/evaluation.py`: 2D and multi-view metrics.
- `src/skinsmith/pipeline.py`: orchestration, ranking, timing, JSON/CSV logging.
- `scripts/real_model_smoke_test.py`: current end-to-end AK-47 validation.
- `scripts/diffusion_smoke_test.py`: one-image GPU acceptance.
- `scripts/diffusion_real_model_test.py`: four-candidate diffusion + AK-47 full chain.
- `runs/real_model_smoke/agent_log.json`: latest complete machine-readable evidence.
- `runs/diffusion_real_model/agent_log.json`: latest diffusion full-chain evidence.

## 8.1 English-submission cleanup (2026-07-16)

- Project-owned source code, code comments, tests, configuration, Streamlit UI copy,
  and submission-facing Markdown are now English.
- Chinese-suffixed documentation was replaced by English filenames:
  `PROJECT_OVERVIEW.md`, `PROJECT_STRUCTURE.md`,
  `TECHNICAL_CONTRIBUTIONS.md`, `PROGRESS_AND_COMPLETION_CHECKLIST.md`,
  `NEXT_SESSION_HANDOFF.md`, and `WORKBENCH_VIEWING_GUIDE.md`.
- All references to the retired `_ZH.md` filenames were updated.
- Formal files under `runs/` were intentionally not translated because they are
  immutable experiment evidence with recorded hashes, prompts, traces, and replay
  contracts.
- Verification after the cleanup: 100 unit tests pass, `compileall` passes, all 20
  JSON configuration files parse, and Streamlit reaches a healthy headless startup.

## 8.2 Academic Phase 1 completed (2026-07-16)

- `RESEARCH_FRAMING.md` locks the English working title, research problem, five
  research questions, five bounded contribution claims, and evidence mapping.
- `LITERATURE_REVIEW.md` synthesizes nine related-work themes: diffusion,
  controllable generation, texture synthesis, UV parameterization, 3D texturing,
  rendering/evaluation, constrained multi-objective selection, iterative
  Agents/human-AI collaboration, and responsible AI.
- The closest-work comparison explicitly positions SkinSmith against TEXTure,
  Text2Tex, TexFusion, Point-UV Diffusion, Paint3D, and synchronized multi-view
  diffusion. Do not claim that SkinSmith is the first diffusion mesh-texturing
  system.
- `references.bib` contains 34 unique primary academic sources. Every citation key
  used by `LITERATURE_REVIEW.md` resolves to one unique BibTeX entry.
- `RUBRIC_EVIDENCE_MATRIX.md` maps all seven SDSC6002 assessment dimensions and
  five CILOs to report sections, preserved evidence, milestones, and production
  gates.
- Next academic stage: build the report manuscript around the locked research
  questions and verify detailed closest-work claims against full paper sections
  while drafting Related Work.

## 8.3 Academic Phase 2 report draft completed and revised (2026-07-17)

- `report/overleaf/` is a complete Overleaf-ready English report project using
  pdfLaTeX, BibTeX, modular section files, TikZ/PGFPlots, formal-run figures, and
  copied machine-readable table data.
- The manuscript contains the abstract, introduction, all five research questions,
  related work, methodology and equations, experimental design, RQ1-RQ5 results,
  discussion, conclusion, reproducibility appendix, evidence index, milestone
  summary, and contribution statement.
- The report uses all 34 verified bibliography entries. There are no missing or
  unused citation keys, undefined cross-references, placeholders, local absolute
  paths, assistant/tool markers, or non-ASCII source characters.
- The locally compiled revised draft has 33 pages and approximately 6,800
  body-text words.
  Page rendering was visually checked for the cover, workflow, equations, tables,
  result figures, edge-width plot, references, and appendices; no clipping,
  overlap, broken glyphs, or overflow remains.
- The cover records all five English group-member names and student IDs, Prof. Yu
  Yang as supervisor, the SkinSmith research title, and the registered umbrella
  topic `Latent Vision -> Image Generation`.
- The Introduction, Discussion, and Appendix document the supervisor-approved
  narrowing from the broad registered topic to the completed technical
  image-processing Agent.
- The contribution statement assigns five substantive work packages. YUAN Ye is
  explicitly the project lead and integration owner; CHEN Yuhong owns creative
  planning and literature; Ben Tangjie owns generation backends and
  reproducibility; Wang Zhengye owns game-asset, UV, and rendering validation; and
  WANG Lihui owns evaluation, statistical reporting, and delivery quality. The
  group must confirm this record before submission.
- The GitHub reproduction link is locked to
  `https://github.com/DID-FIELD/SDSC6002-SkinSmith`.
- The report contains no statement that its code, prose, or presentation material
  was written by an assistant. It does disclose the Gemini and SD-Turbo models
  that are part of the experimental system, together with provenance, limitations,
  and rights boundaries.
- The current PDF is a review draft, not the final submission PDF. The next report
  action is student/team/supervisor review followed by final freeze. Poster and
  presentation production follow from the verified report narrative.

## 8.4 Academic Phase 3 poster and presentation completed (2026-07-17)

- `report/build/SkinSmith_A0_Poster.pptx` is a true A0 landscape PowerPoint with
  a page size of 1189.04 x 841.11 mm.
- The poster follows the requested traditional academic-poster convention:
  institutional header, bordered section panels, Introduction, Methodology,
  Human-Agent Checkpoints, Experimental Setup, Results and Analysis, and
  Conclusion. It is not an infographic-style substitute.
- `report/build/SkinSmith_A0_Poster.pdf` and the PowerPoint-rendered PNG were
  exported for visual inspection. The Office render is complete and unclipped.
- `report/build/SkinSmith_Supervisor_Presentation.pptx` is a ten-slide,
  audience-facing presentation covering the mapped-asset problem, three human
  checkpoints, weapon-space method, formal A/B evidence, constraint-first
  selection, live `dragon` case, bounded rollback, AK/M4A4 portability boundary,
  conclusion, and group ownership.
- `report/build/SkinSmith_Supervisor_Presentation.pdf` and ten PowerPoint-rendered
  slide PNGs were exported for Office-level visual QA.
- The presentation passed the automated slide overflow test. Every slide was
  inspected individually at full size, and the final PowerPoint montage showed no
  clipping, unintended overlap, broken glyphs, or layout drift.
- Poster and presentation numerical claims use the preserved formal evidence:
  mean seam `0.26997 -> 0.00063`, mean mapped-view score
  `0.76898 -> 0.82911`, four of four paired Route-B candidates improving both,
  live seam `0.0007776109029832148`, live multi-view
  `0.8166198880536247`, live total `0.8291228922780649`, and Route-C rollback
  after `-0.02195902089447299`.
- No GitHub push has occurred. Before publication, perform a final tracked and
  untracked secret scan, verify `.gitignore`, exclude private APIs, Valve assets,
  model weights, caches, and unsuitable experiment payloads, then publish only
  after the user explicitly confirms.
- The first release-safety audit found no credential-format match in any
  non-ignored publication candidate. Three matches under ignored `runs/` were
  verified as false positives inside large model-signature or image-data fields,
  not credential fields.
- `.gitignore` now also excludes `.env.*`, Streamlit secrets, private-key
  formats, `tmp/`, local editor/Agent metadata, PowerPoint QA subdirectories, and
  artifact-tool inspection records. `SECURITY_RELEASE_CHECKLIST.md` records the
  complete publication gate.
- GitHub publication completed on 2026-07-17. The initial project commit is
  `0522ad2`; the preserved remote history and project commit were merged and
  published as `ee628e1` on `main`. The published tree had zero forbidden-prefix
  paths and no common credential-format match.
- End-of-day status on 2026-07-17: implementation, report draft, A0 poster,
  supervisor presentation, release-safety audit, and initial GitHub publication
  are complete. The project is paused pending supervisor and group feedback.
- On receipt of feedback, preserve each comment's source and wording, classify it
  by deliverable and scope, resolve contradictions explicitly, and update the
  continuity documents with accepted, rejected, and deferred actions.
- Group feedback confirms the five-member contribution statement. The detailed
  contribution table remains unchanged, and the provisional paragraph requesting
  later group confirmation is removed from the report appendix.
- The root `README.md` is rewritten as a reader-facing project description rather
  than a chronological development log. It now explains the problem, three
  checkpoints, design routes, verified findings, setup, execution, repository
  structure, artifacts, limitations, and publication boundaries.
- The user is dissatisfied with the current poster and presentation, but has
  explicitly deferred those revisions. Do not modify either artifact until later
  feedback or a direct request.

## 8.5 Presentation rebuild and material-scope revision (2026-07-17)

- The user directly requested a presentation rebuild, superseding the earlier
  deferral for the presentation only. The A0 poster remains unchanged.
- `report/build/SkinSmith_Supervisor_Presentation.pptx` is now a 13-slide
  evidence-led deck using the restrained Codex Grid visual system.
- Every slide contains English speaker notes. The exported PPTX contains 13
  `notesSlides`, and the deck passed the automated overflow test.
- Microsoft PowerPoint exported the matching PDF and 13 slide PNGs. The Office
  montage was inspected with no clipping, overlap, broken glyph, or layout drift.
- Actual CS2 Workbench evidence is used in two distinct roles: the known-good UV
  calibration proves orientation/import correctness, and the calibrated
  black-and-gold marble case proves coherent in-engine colour-texture deployment.
- The deck does not represent the black-and-gold case as the accepted dragon Agent
  result. The exact final dragon TGA still needs fixed left/right/top Workbench
  captures and one settings-panel screenshot.
- The report Discussion and Conclusion, root `README.md`, `PROJECT_OVERVIEW.md`,
  and `WORKBENCH_VIEWING_GUIDE.md` now state that the implemented output is a
  base-colour / Custom Paint Job texture, not a full PBR material. Workbench
  lighting is not evidence of generated normal, roughness, metallic, height, or
  displacement channels.
- Prioritised future work is: aligned multi-channel material generation and
  validation; automated fixed-camera engine capture; broader asset adapters;
  stronger perceptual measures; and a user study of the three checkpoints.
- The updated report compiles successfully to 33 pages. The revised material
  boundary and conclusion pages were rendered and visually inspected without
  clipping or pagination defects.
- `report/build/SkinSmith_Overleaf.zip` was regenerated from the tracked Overleaf
  source on 2026-07-20. The package contains 28 required files, includes the
  revised Discussion and Conclusion, and compiles independently to the same
  33-page, 3,794,036-byte PDF.
- The root `README.md` is intentionally limited to the software project, its
  workflow, setup, verified findings, and technical boundaries. Academic report,
  poster, presentation, Overleaf, and test-count inventories remain in the
  repository as backup but are not presented as GitHub deliverables.

## 8.6 A0 poster evidence correction and submission-ready PPTX (2026-07-20)

- The user directly requested revision of the supplied A0 poster while preserving
  its overall format. `report/build/SkinSmith_A0_Poster.pptx` retains the original
  A0 landscape page, three-column grid, numbered section bands, palette, image
  gallery placement, and footer structure.
- The final PPTX measures 1188.993 x 840.978 mm in OOXML, satisfying the required
  1189 x 841 mm A0 landscape specification. The PPTX is the primary submission
  artifact; the PDF is only a print and visual-QA derivative.
- Claims now match the preserved evidence: exactly 100 automated tests; three
  fixed mapped views; four paired formal candidates rather than four viewpoints;
  AK-47 as the complete target; M4A4 as adapter-level transfer; and base-colour
  PNG/TGA output rather than normal/PBR material generation.
- The paired mapped-view chart uses candidate_01 through candidate_04 and the
  preserved Route-A/Route-B scores. The correction chart distinguishes four
  formal candidate-level rejections from the separate live dragon rollback.
- The Route-B process graphic identifies geometry normals as baking guidance and
  the exported asset as an RGB/base-colour texture. CP1 is theme confirmation;
  source artwork is generated after CP2 and inspected at CP3.
- The footer includes all five members, student IDs, and supervisor. The Office
  PDF export and a full-size 4494 x 3179 render were visually inspected without
  clipping, overlap, or page-size drift.
- Submission remains an external action: send the A0 PPTX to the supervisor and
  `ds.go@cityu.edu.hk` by 12:00 noon on 2026-08-02 and arrange the poster
  presentation with the supervisor before the deadline.

## 8.7 Fresh flower workflow and resumable candidate recovery (2026-07-20)

- `runs/agent_flower_demo_v1/` is the new presentation case. CP1 expanded
  `flower` into `Withered Petal Covenant`; CP2 produced four distinct directions
  and the human choice locked `candidate_04_dir_04_decay_gradient`; CP3 produced
  four source-plus-three-view cards and the human choice locked `artwork_04`.
- `artwork_04` had the highest preview multi-view score (`0.721016`) and highest
  preview total (`0.795516`). Formal Route B used the same source at 2048,
  selected edge width 4, passed constraints, scored `0.744018` multi-view and
  `0.778297` total, and exported
  `execution/route_b/selected__route-b__custom-paint-job.tga`.
- Route C was correctly rolled back because its score decreased by `0.020942`;
  Route B remained selected. The formal TGA is a 2048 x 2048 base-colour Custom
  Paint Job texture and is now waiting for fixed Workbench left/right/top and
  settings screenshots from the user.
- The live run exposed a recovery defect: an interrupted candidate batch retained
  passing source files and validation JSON but regenerated them on resume,
  consuming image-call and retry budgets. `RouteExecutionTool` now reuses a
  canonical Route-B source only when its preserved validation explicitly records
  `passed: true`. The regression is covered in `test_route_execution.py`; all
  100 tests pass after the change.
- The interrupted attempts, one transient SSL failure, rejected candidates, and
  corrected final run remain preserved as evidence. No API key is logged.
- After visual review, the user rejected the colourful `artwork_04` mapping as
  unattractive. A preserved branch at `runs/agent_flower_ornamental_v2/` selects
  `artwork_02` (`Ornamental Tapestry`) and exports an independent 2048 Route-B
  PNG/TGA. Its formal asset seam is `0.000575`, multi-view score is `0.738551`,
  and Route C is rolled back after a `-0.018890` change. Use this cleaner floral
  version for the next Workbench comparison unless the user rejects it too.
- Raw `runs/` contains 2.43 GB and remains ignored. The tracked
  `experiments/public/flower_workflow_v1/` package publishes 66 evidence files
  (about 27.2 MB): checkpoints, events, planning, all four source/mapped cards,
  source gates, sanitized API traces, final ornamental PNG/TGA, views, metrics,
  and a SHA-256 manifest. Actual API keys, authorization values, Valve assets,
  repeated intermediate textures, geometry caches, and long embedded binary
  response fields remain excluded.

## 8.8 Garden replacement and public evidence package (2026-07-20)

- The user rejected both flower mappings and requested a new one-word task:
  `garden`. `runs/agent_garden_demo_v1/` is now the current visual case.
- CP1 expanded `garden` into the bioluminescent `Midnight Serenity` world with
  spectral koi, glowing lotus, stone lanterns, bamboo, water ripples, willow, and
  fireflies. CP2 produced four directions and locked
  `candidate_02_direction_koi_flow` (`Spectral Movement`). CP3 compared four
  source-plus-three-view cards and selected `artwork_02` (`Ornamental Tapestry`)
  by visual judgment rather than the maximum automatic score.
- Formal Route B selected edge width 4, asset seam `0.001246`, multi-view
  `0.811677`, and total `0.817374`. Route C decreased the score by `0.016233` and
  was rolled back. The 2048 TGA is
  `runs/agent_garden_demo_v1/execution/route_b/selected__route-b__custom-paint-job.tga`
  with SHA-256 `8615e42473d86719a6ebb1dc2f2fa239381f635ab9c648475c94430fe28f4bb0`.
- `experiments/public/garden_workflow_v1/` publishes 49 evidence files (about
  25.1 MB) with the same redaction and hash policy as the flower package. Both
  package manifests verify and the combined public evidence scan finds no API
  credential pattern.
- The next action is user Workbench validation of the garden TGA, followed by a
  presentation rebuild using garden CP1/CP2/CP3, formal export, and fixed engine
  views. Do not use either flower mapping as the final visual case.

## 9. Non-negotiable boundaries

- Never inspect, modify, move, or delete other projects under `D:\project`.
- Work only inside `D:\project\SDSC6002-SkinSmith` unless the user explicitly authorizes another path.
- Steam Workshop publication is outside the course deliverable.
- Do not use logos, brands, anime characters, team marks, copied skins, or unlicensed images.
- Use original prompts/themes and disclose AI/model use.
- Do not commit or redistribute Valve assets, model weights without suitable licensing, or secrets.
- Do not expand to every weapon, train a large model from scratch, or build a commercial platform.
- Preserve the procedural baseline and current evidence while adding new backends.
- Do not delete old runs unless explicitly authorized; formal runs are research evidence.

## 10. Session protocol

At the start of every future session:

1. Read this file completely.
2. Inspect `git status` and the latest `agent_log.json`/`run_summary.csv`.
3. Run tests only when relevant; do not redo environment discovery without evidence of change.
4. Continue from the highest-priority incomplete action.
5. Update this file after any material change to scope, architecture, verified evidence, blockers, or next actions.

This file is the authoritative Codex continuity source. If `HANDOFF.md` conflicts with it, follow this file.
