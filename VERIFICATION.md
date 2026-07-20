# SkinSmith MVP verification

Verified through 16 July 2026 in `D:\project\SDSC6002-SkinSmith`.

## What currently runs

The real-model baseline completes this chain:

```text
DesignSpec + fixed seed
  -> four procedural texture candidates
  -> periodic seam measurement and repair
  -> official AK-47 OBJ/UV application
  -> left, right, and top software renders
  -> 2D texture metrics + multi-view render metrics
  -> weighted ranking and automatic selection
  -> JSON log + CSV summary + images
```

This is the deterministic technical baseline. It proves the constraints, rendering,
evaluation, ranking, and evidence pipeline; SD-Turbo and the weapon-space Route-B path
have since been accepted separately.

## Commands

Use the configured environment from the repository root:

```powershell
& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v
& '.\.venv\Scripts\python.exe' scripts\plan_style.py "blue-and-white porcelain theme" --style blue_white_porcelain --count 4
& '.\.venv\Scripts\python.exe' scripts\plan_design_routes.py "Design an AK-47 skin named Wild Lotus"
& '.\.venv\Scripts\python.exe' scripts\smoke_test.py
& '.\.venv\Scripts\python.exe' scripts\real_model_smoke_test.py
& '.\.venv\Scripts\python.exe' scripts\weapon_space_route_b_smoke.py
```

Expected deterministic-baseline results:

- 78 tests pass, including Agent runtime/checkpoint, role-local retry evidence preservation, real A/B/C execution orchestration, generated-role soft-alpha extraction, asset-contract matching, official UV-sheet hash binding, and deployment UV-addressing coverage;
- all four style packs validate, and one porcelain brief expands into four distinct art directions;
- the wild-lotus route bundle proves A designs a tileable template, B designs a weapon-level composition from semantic square assets, and C is B plus bounded feedback;
- a fake creative backend verifies that an uncached landscape-painting prompt can compile a new validated ThemePack whose component story exactly matches the target weapon; this validates the interface, not real language-model creativity;
- an unknown theme without a real creative backend fails explicitly instead of falling back to hard-coded keywords;
- provider-neutral OpenAI and Gemini theme adapters build JSON-Schema requests, normalize complete seven-component stories, reject missing local keys before network access, and keep keys out of traces;
- OpenAI and Gemini image adapters decode provider-native base64 images, and `ApiTextureGenerator` connects either provider to the existing texture-candidate interface;
- the locked Nano Banana 2 smoke plan expands one route bundle into exactly one Route-A template job and four Route-B semantic jobs (hero, secondary, connector, background), while preserving the mapped-preview acceptance boundary;
- a preserved uncached chip-circuit brief compiles through the recorded Codex-agent backend into the `Silicon Vein` ThemePack and writes `runs/theme_compilation_chip_circuit/route_design_bundle.json`;
- a real Gemini API call compiled an uncached dark-marble/gold-vein brief with `gemini-3.1-flash-lite`; the result covers all seven AK components, passes ThemePack validation, records no API key, and writes `runs/theme_compilation_marble/`;
- a second live Gemini run compiles both layers for the same class of brief: `abyssal_vein_marble` ThemePack plus `abyssal_vein_marble_v1` geological/material StylePack. The style has exact seven-component roles, four distinct directions, the Theme palette, zero botanical/porcelain legacy terms, and zero API-key matches in preserved files under `runs/theme_compilation_marble_dynamic_style/`;
- Paid Tier accepted the locked five-image Nano Banana smoke: one Route-A source plus Route-B hero, secondary, connector, and background. Per-job checkpoints safely reused two completed B assets after TLS interruption; all five jobs and redacted traces are recorded under `runs/nano_banana_marble_dynamic_style/`, with zero API-key matches;
- the mapped Route-A result records repaired square seam `0.018168`, asset seam `0.116078`, multi-view `0.617104`, and total `0.684366`;
- the dynamically compiled Route-B weapon-space plan records corrected asset seam `0.006756`, multi-view `0.741879`, and total `0.775921`; versus A, multi-view improves `0.124775` and total improves `0.091555`;
- the role-local refinement regenerates only hero and connector, reuses the exact Round-0 secondary/background hashes, and records corrected asset seam `0.006540`, multi-view `0.725273`, and total `0.763492` under `runs/nano_banana_marble_dynamic_style_refined/`; visual review finds no mapped ghost weapon or exposed rectangular source boundary;
- candidate-direction locking and role-priority prompts are covered by regression tests; the `tectonic_cluster` run preserves a failed role-drift round and a targeted three-role retry, with zero API-key matches;
- correcting the image-space/canonical-coordinate split moves the cluster hero from the magazine back to the receiver and raises multi-view from `0.348902` to `0.536669` without a new image call;
- the selected single-fissure candidate records 512 asset seam `0.007113`, multi-view `0.735170`, and total `0.782189`; its formal 2048 RGB TGA records 8 px asset seam `0.003943` and multi-view `0.749259`;
- that new-geometry TGA remains valid for its bound OBJ but is no longer treated as the CS Workbench deployment artifact;
- the attempted `config/assets/ak47_workbench_official.json` legacy adapter and its
  16 px result are preserved as rejected deployment-diagnosis evidence;
- the later Viper/wireframe calibration proves that the new HD
  `weapon_rif_ak47.obj` mesh-derived UV is the Workbench-confirmed UV in the same
  orientation, so `config/assets/ak47_cs2.json` is again the formal/default AK path;
- the calibrated marble 2048 TGA and its left/right/top Workbench screenshots pass
  under this HD contract; evidence is under
  `runs/nano_banana_marble_dynamic_style_refined/route_b_showcase_2048_hd_calibrated/`.
- 2D smoke test selects `candidate_02` from 4 candidates;
- real-model test selects `candidate_02` from 4 candidates;
- real-model outputs appear under `runs/real_model_smoke/`;
- `agent_log.json` contains every metric and decision input;
- `run_summary.csv` contains the final ranking.

## Uncached live Agent CLI acceptance

The reusable Agent has passed a real uncached-theme acceptance under
`runs/agent_live_astrolabe/`:

- live Gemini Theme/Style compilation produced four distinct directions:
  `Radial Orrery`, `Star-Chart Flow`, `Verdigris Timepiece`, and `Orbital Rings`;
- the selected `Radial Orrery` direction executed one real Route-A generation plus
  four Route-B semantic roles, then preserved and selectively revised role failures;
- the image-call budget was explicitly extended from 8 to 12 after a checkpointed
  failure, while actual use remained 9 calls;
- revisions 01 and 02 used the retired legacy Workbench adapter and are rejected as
  final evidence; revision 04 remaps both A and B with zero new image calls under
  `cs2_ak47_new_geometry`, mesh SHA-256 `dae29ee5...4065654f`;
- HD Route A records asset seam `0.111407`, multi-view `0.829641`, and total
  `0.793197`, so it fails the real asset-seam hard gate;
- HD Route B selects 12 px and records asset seam `0.000187`, multi-view
  `0.794076`, total `0.792397`, and all hard constraints pass;
- Route C adds no image call and rolls back because its best score change is
  `-0.029224`, below the required `+0.01`;
- the final 2048 RGB Route-B TGA hash is
  `a03336d7473393357b182d647c02432df1812c362f16bca0b9817e85e3c1eff7`;
  decoded PNG/TGA pixels are identical;
- visual review passes receiver hierarchy, left/right/top orientation, quiet muzzle,
  and removal of rectangular semantic-source boundaries.

The machine-readable decision is
`runs/agent_live_astrolabe/execution/revisions/revision_04/final_visual_acceptance.json`;
the Chinese handoff is `runs/agent_live_astrolabe/AGENT_ACCEPTANCE_ZH.md`.

## True Route-B weapon-space acceptance

The 512 technical smoke implements the corrected Route-B definition:

```text
coherent left/right/top weapon-space design
  -> mesh-derived UV position/normal maps
  -> fragmented flat UV storage
  -> AK-47 3D reconstruction
  -> asset seam measurement and correction
```

Verified evidence:

- valid UV-map coverage: `70.6577%`;
- overlap pixels: `0.3666%` (small stacked/overlap areas);
- raw asset seam: `0.094424`;
- corrected asset seam: `0.005303`, passing the `0.01` hard threshold;
- corrected multi-view score: `0.548435`;
- visual status: `pass_true_route_b_technical_path_not_final_art`.

The flat UV output is expected to look fragmented. Visual coherence is verified on
the reconstructed weapon, where the receiver focal motif and longitudinal flow are
restored. The current procedural motif is a geometry/composition-path placeholder,
not the final showcase. Evidence is preserved under
`runs/weapon_space_route_b_smoke/`, including
`route_b_weapon_space_concept.png`, `weapon_space_log.json`, and
`visual_validation.json`.

The next low-cost smoke added two controlled capabilities without invoking a new
generation run:

- normal-weighted side/top projection blending (`p = 4.0`) replaces a hard chart switch;
- a preserved SD-Turbo image is copied, hashed, and blended at 12% opacity on the
  continuous weapon-space canvases rather than pasted into UV coordinates.

The projection-only control records corrected asset seam `0.005242` and multi-view
`0.546672`. With the restrained material layer, corrected asset seam is `0.006003`
and multi-view is `0.576644`. The content-layer path therefore passes the seam hard
gate and improves the matched multi-view score by `0.029972`. Evidence is in
`runs/weapon_space_projection_blend_smoke/` and `runs/weapon_space_content_smoke/`.

## Diffusion backend acceptance

The local generation backend has also passed the real-model acceptance chain:

- model: `stabilityai/sd-turbo`;
- pinned revision: `b261bac6fd2cf515557d5d0707481eafa0485ec2`;
- Diffusers: `0.39.0`;
- Accelerate: `1.14.0`;
- resolution: 512 × 512;
- inference steps: 2;
- prompt length: 74 of 77 CLIP tokens;
- observed peak allocated VRAM: approximately 3.03 GB;
- four-candidate generation, repair, rendering, evaluation, and ranking: approximately 28 seconds after caching;
- latest selected result: `candidate_02`.

Run it offline after the one-time model download:

```powershell
$env:HF_HOME = "$PWD\third_party\huggingface"
$env:HF_HUB_OFFLINE = "1"
& '.\.venv\Scripts\python.exe' scripts\diffusion_real_model_test.py
```

Evidence is written to `runs/diffusion_real_model/`. Every candidate records its
prompt, seed, model revision, prompt token count, peak VRAM, texture metrics,
multi-view metrics, and final rank.

## Scoring interpretation

The 2D texture score combines:

- seamless-boundary score: 40%;
- texture contrast: 25%;
- target saturation: 20%;
- edge/detail coverage: 15%.

The multi-view score combines the mean render contrast, saturation, visible detail,
and luminance consistency across left, right, and top views. With real geometry, the
final score is:

```text
final = 0.65 * texture_score + 0.35 * multi_view_score
```

In the verified run, `candidate_03` had the highest multi-view score, while
`candidate_02` had the strongest balanced final score. This confirms that the 3D
evaluation contributes to ranking rather than merely generating decorative images.

## Reproducibility evidence

Two consecutive real-model runs checked all 24 generated candidate and preview
files using SHA-256. The number of hash differences was zero. Runtime fields in the
JSON log naturally vary and are not part of the image-hash comparison.

## CS2 Workbench path validation

The retained `candidate_02_seamless.png` was imported manually into the CS2
Creative Workshop and inspected from the left, top, and right. The texture covers
the AK-47 without missing or transparent areas, and no obvious within-island seam
is visible at screenshot scale. The import and mapping path therefore passes.

The same check fails the texture as final artwork: blue-white and purple regions
change abruptly between UV islands, stripe detail is too dense, and the result has
no weapon-aware focal composition. These screenshots are path evidence only. The
formal experiment must select a stronger candidate before the final presentation.
Machine-readable evidence is in `runs/diffusion_refinement/workbench_validation.json`.

## Garden human-choice and engine validation

The current presentation case is the complete `garden` run under
`runs/agent_garden_demo_v1/`:

- Checkpoint 1 confirmed `Midnight Serenity`;
- Checkpoint 2 selected `Spectral Movement` from four textual directions;
- Checkpoint 3 retained four source-plus-mapped-view cards;
- `artwork_03` had the highest automatic preview total (`0.895454`), while the
  user selected `artwork_02`, `Ornamental Tapestry` (`0.829271`);
- formal Route B selected edge width 4, asset seam `0.001246`, multi-view
  `0.811677`, and total `0.817374`;
- Route C changed the score by `-0.016233` and was correctly rolled back;
- the final 2048 TGA SHA-256 is
  `8615e42473d86719a6ebb1dc2f2fa239381f635ab9c648475c94430fe28f4bb0`.

The score-versus-choice result is intentional evidence that deployment metrics
and aesthetic preference have different roles. Automatic scores screen
feasibility and support recommendation; they do not replace human selection.

Fixed Workshop left/right/top captures, the Item Editor settings, and two in-game
views verify base-colour placement, coverage, readability, and the export/import
path. Publication-safe copies and hashes are under
`experiments/public/garden_workflow_v1/engine_validation/`. The screenshots do
not support a claim of Agent-generated PBR channels; CS2 lighting and reflectance
remain engine effects.

## Known limits

- SD-Turbo is an accepted first generation backend, not a claim that it is the best possible model.
- OpenAI/Gemini adapters pass offline tests; live Gemini Theme, Style, and Nano Banana
  image calls are now accepted. OpenAI remains an uncalled optional comparison.
- The first five generated Nano Banana squares remain preserved as Round-0 evidence;
  their Route-B hero and connector contain forbidden weapon/mockup fragments.
- The separate marble refinement run corrects those two roles. Its hero still carries
  a source-level caveat because of the substantial irregular stone mass, but the
  selected design has been re-baked through the calibrated new-HD OBJ/UV contract and
  accepted in Workbench.
- The first live marble ThemePack selected an unsuitable cached botanical StylePack.
  Dynamic style compilation fixed that structural mismatch. The paid images, HD
  mapping, three-view review, and Workbench reimport are complete.
- The renderer now uses barycentric per-pixel UV interpolation, bilinear texture
  sampling, and a z-buffer. It remains a simple orthographic, flat-lit research
  preview rather than a photorealistic substitute for CS2 Workbench. Legacy flat
  centroid sampling is retained only for ablation.
- The current evaluation measures technical visibility, consistency, and CLIP
  text-image alignment, but it does not provide a learned aesthetic-preference score.
- No Steam Workshop publication is performed or promised.
- The SD-Turbo pipeline has no active safety checker. It is restricted to local,
  original abstract research prompts and requires manual output review; do not expose
  it as an unfiltered public service.
- The project uses its independent `.venv`; do not run it from the shared Anaconda base.

## Component-relationship Route-B verification

The fixed four-role placement route now has an explicit graph-based successor while
retaining the old path for preserved themes:

- fixture: `config/design_themes/celestial_dragon.json`;
- preserved plan: `runs/composition_graph_dragon/route_design_bundle.json`;
- composition groups: `lacquer_field`, `dragon_body_run`,
  `dragon_head_coil`, `magazine_claw`, and `cloud_flow`;
- generated job names are unique per group, including two independent hero groups;
- compiled layers include one wide dragon-body side layer across
  stock/receiver/handguard, a separate top consumer, one magazine-only claw layer,
  a front/muzzle head layer, and shared cloud/background layers;
- explicit muzzle focus sets the compiled quiet strength to `0.0`;
- legacy ThemePacks still compile to the previous four files and seven layers;
- explicit graph groups use procedural generation scope guides and are hard-clipped
  to exact mesh-derived component/surface UV regions;
- old saved graph bundles recover missing scope metadata from the composition graph;
- `python -m unittest discover -s tests` passes 91 tests;
- `python -m compileall -q src scripts tests` passes.

Live dragon evidence is under
`runs/agent_dragon_composition_dynamic_style/execution/revisions/revision_01/`:

- two scope-guided hero regeneration calls were made; total image calls are 9/12;
- Route B uses `mesh_semantic_uv_region_conditioned`;
- selected edge width: `4`;
- asset seam: `0.0012590479`;
- multi-view score: `0.7751282979`;
- total score: `0.7913328678`;
- all numeric hard constraints pass.

Visual acceptance remains rejected. The body source contains a complete dragon
instead of torso/tail only, and the head source contains claw/blade decoration on a
framed slab instead of a dragon head plus short neck. Exact UV-region fitting is
therefore verified. This run is frozen as negative evidence; source-part semantic
review is no longer the default Agent gate.

## Default master-artwork Route-B verification

- preserved plan: `runs/master_artwork_dragon/route_design_bundle.json`;
- composition strategy: `master_artwork`;
- Route-B generated source count: `1`;
- generated source id: `celestial_dragon_v1_master_artwork`;
- the same opaque source binds to full left/right and top weapon-space layers;
- validation checks resolution, tonal/colour variation, and local gradient density,
  without requiring dragon-head/body/claw recognition;
- old serialized four-role and graph bundles retain their original execution paths;
- Route-B execution records `continuous_master_artwork_obj_uv_bake`;
- `python -m unittest discover -s tests` passes 91 tests;
- `python -m compileall -q src scripts tests` passes.

Real Gemini acceptance is preserved under `runs/agent_dragon_master_artwork/`:

- selected direction: `Classic Gold Ink`;
- one Route-A source and four preserved Route-B master-artwork attempts used five
  total image calls;
- the local-density gate rejects excessive dead zones, and the narrow multimodal
  forbidden-content gate rejects weapons/mockups/text/logos/panels without checking
  whether dragon anatomy lands on named components;
- attempt 03 was rejected as a framed-panel composition; attempt 04 passed with
  `detail_density = 0.306265`, `low_detail_patch_ratio = 0.0`, and minimum local
  detail density `0.151305`;
- final composition mode: `continuous_master_artwork_obj_uv_bake`;
- selected edge width: `4`;
- asset seam: `0.000305723`;
- multi-view: `0.792136`;
- total score: `0.787674`;
- multi-view retention: `0.995283`;
- all hard constraints pass;
- visual review passes the source and AK left/right/top mapping with no weapon
  fragments, framed panels, or rectangular source boundaries.

Accepted TGA:
`runs/agent_dragon_master_artwork/execution/revisions/revision_02/route_b/selected__route-b__custom-paint-job.tga`.
