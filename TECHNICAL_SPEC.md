# SkinSmith Technical Specification

> Status: locked implementation contract  
> Updated: 2026-07-16  
> Canonical continuity: `CODEX_CONTEXT.md`

## 1. Objective

SkinSmith is a constraint-aware generative Agent for game weapon skin design.
Counter-Strike 2 is the case study. The system must transform a compact user theme
into a human-selected, UV-valid, multi-view-evaluated texture and preserve complete
reproducibility evidence.

## 2. User interaction contract

The client exposes three required human checkpoints.

### Checkpoint 1: Theme confirmation

Input:

- registered weapon;
- one short theme keyword, for example `dragon`;
- optional broad style family.

The ThemeCompiler expands the keyword into a validated ThemePack containing:

- theme identity, concept, and narrative;
- hero, secondary, connector, and background elements;
- related symbols and environmental elements;
- material and atmospheric cues;
- palette;
- component story;
- evaluation criteria;
- reference and rights policy.

The Agent enters `awaiting_theme`. Direction planning cannot begin before explicit
confirmation.

### Checkpoint 2: Direction selection

After theme confirmation, the StyleCompiler synthesizes a theme- and weapon-specific
StylePack. The Agent proposes three or four materially different textual directions.

The Agent enters `awaiting_direction`. Image generation cannot begin before the user
selects one direction.

### Checkpoint 3: Artwork selection

The selected direction produces three or four landscape master artworks. Every
artwork is:

1. validated as a source image;
2. mapped at low cost through the selected weapon's OBJ/UV contract;
3. rendered from left, right, and top views;
4. presented as one indivisible source-and-views candidate card.

The Agent enters `awaiting_artwork`. Formal export cannot begin before the user
selects one artwork.

Automatic review is recommendation-only. Human selection is authoritative.

## 3. Agent state machine

```text
created
  -> planning
  -> awaiting_theme
  -> planning
  -> awaiting_direction
  -> awaiting_artwork
  -> ready_to_execute
  -> executing
  -> completed
```

Any stage may enter `failed`. Checkpoints preserve the request, ThemePack expansion,
directions, selected contract, artwork candidates, budgets, events, retries,
refinement use, and stop reason.

Backward compatibility is retained for older tools that do not register an
`expand_theme` operation.

## 4. Core data contracts

### AgentRunRequest

- `brief`: short keyword or free brief;
- `asset_id`: registered target adapter;
- `style_family`: optional broad preference;
- `candidate_budget`: 3 or 4;
- `direction_choice`: optional;
- budget limits for image calls, retries, and refinement rounds.

### ThemePack

- identity and matching terms;
- concept and narrative;
- palette;
- 3-14 validated elements;
- component story for every target component;
- optional composition groups;
- evaluation criteria;
- rights-safe reference policy.

Live unknown-theme generation uses the default single-master workflow and does not
require optional composition groups. Hand-authored research themes may still define
them.

### StylePack

- visual vocabulary;
- motifs and material cues;
- palette;
- composition principles;
- prohibited content;
- Route A and Route B policies;
- exact component roles;
- three or four candidate directions;
- evaluation criteria and fallback motif.

### ArtworkCandidate

- candidate ID and variation;
- original source path;
- exact prompt;
- left, right, and top preview paths;
- source validation;
- pre-mapping metrics.

### DesignContract

Locks:

- original user brief;
- asset ID;
- selected direction;
- palette and visual language;
- constraints;
- lock timestamp.

The selected concept must not change silently after this point.

## 5. Asset contract

Every target uses a versioned adapter that binds:

- asset ID and display name;
- mesh path, version, and SHA-256;
- authoritative UV source and address mode;
- canonical longitudinal and up axes;
- texture size;
- camera views;
- semantic regions and component anchors;
- paintable range;
- export format.

### Accepted AK-47

- asset ID: `cs2_ak47_new_geometry`;
- spec: `config/assets/ak47_cs2.json`;
- creative profile: `config/assets/ak47_weapon_space_anchors.json`;
- texture: 2048 x 2048 RGB;
- export: 24-bit TGA, Custom Paint Job;
- views: left, right, top.

### M4A4

M4A4 is bound through `config/assets/m4a4_cs2.json` and demonstrates core adapter
transfer. It is not yet enabled as an AK-equivalent formal client target because its
locked joint seam/retention constraint did not fully pass.

### Prohibited asset mixing

- Never combine the legacy AK-47 UV sheet with the new CS2 geometry.
- Never apply an AK-47 TGA to another weapon.
- Never assume a global V flip without deployment evidence.

## 6. Route A

Route A is the pattern-first baseline.

Requirements:

- square source;
- dense multi-scale elements;
- crop tolerance;
- periodic boundary repair;
- Custom Paint Job mapping;
- real asset-seam measurement;
- left/right/top evaluation.

The periodic repair uses frequency-domain periodic-plus-smooth decomposition.
Direct mirrored border blending is rejected because it produces visible frames.

## 7. Route B

Route B is the required final-showcase route.

### Source

Generate one complete landscape master artwork per candidate.

The source must:

- be dense and edge-to-edge;
- contain multiple medium and small thematic clusters;
- remain useful under crop and UV fragmentation;
- avoid large dead regions;
- avoid one dominant full-width subject;
- avoid weapons, weapon parts, mock-ups, UV layouts, text, logos, watermarks,
  borders, framed panels, and presentation boards.

Subject-part placement on named components is not a source acceptance requirement.

### Weapon-space composition

The master artwork is fitted to continuous left, right, and top canvases in a
mesh-derived canonical frame.

Projection blending uses surface normals to combine side and top canvases without a
hard chart switch.

### UV bake

For every valid UV pixel:

1. identify the containing OBJ triangle;
2. interpolate canonical 3D position and normal barycentrically;
3. sample the continuous weapon-space canvases;
4. write the resulting RGB value into the authoritative square atlas.

The output atlas is expected to look fragmented in 2D.

### Seam handling

The asset seam graph is derived from welded geometric topology. UV edges
corresponding to the same 3D edge are sampled and compared.

Locked AK-47 hard threshold:

`asset_seam <= 0.01`

An edge-safety sweep evaluates fixed candidate widths. Selection uses hard
constraints, Pareto dominance, and deterministic objective order.

## 8. Route C

Route C reuses the accepted Route B Round 0.

Rules:

- exactly one diagnosis;
- exactly two correction candidates;
- no new source image unless explicitly required by a separate revision workflow;
- changes limited to the target component plus transition halo;
- zero changed pixels outside the allowed halo;
- all Route B hard constraints remain active;
- acceptance requires at least `+0.01` locked-score improvement.

If the gate fails, the final result is Route B Round 0.

## 9. Rendering

`ObjMultiViewRenderer` provides:

- textured OBJ loading;
- fan triangulation for polygon faces;
- barycentric per-pixel UV interpolation;
- bilinear texture sampling;
- z-buffering;
- orthographic left, right, and top cameras;
- deterministic flat lighting.

The renderer is an evaluation instrument, not a photorealistic replacement for
CS2 Workbench.

## 10. Evaluation

### Texture metrics

- square-border seam;
- contrast;
- saturation;
- detail;
- paintable coverage.

### Asset metrics

- true asset-seam color error;
- true asset-seam gradient error;
- combined asset-seam error.

### Multi-view metrics

- foreground coverage;
- contrast;
- saturation;
- detail;
- view consistency;
- combined multi-view score.

### Mapped readability

The reviewer compares planned elements with:

1. original source;
2. left weapon view;
3. right weapon view;
4. top weapon view.

Recommendation weighting:

```text
0.25 * source fulfillment
+ 0.50 * left readability
+ 0.15 * right readability
+ 0.10 * top readability
```

This score is explanatory and cannot override human selection.

## 11. Selection policy

Primary policy:

```text
hard constraints
  -> feasible pool
  -> Pareto front
  -> deterministic objective order
```

Weighted ranking is retained only as an ablation baseline.

The edge-width evidence demonstrates that a 50/50 weighted aggregate can select an
asset-seam violator.

## 12. Generation backends

### Procedural

The deterministic procedural generator remains the reproducibility baseline.

### Local diffusion

- model: `stabilityai/sd-turbo`;
- pinned revision: `b261bac6fd2cf515557d5d0707481eafa0485ec2`;
- 512 x 512;
- two inference steps;
- guidance scale 0;
- overlength prompts fail instead of truncating.

### Gemini

Configured models:

- structured planning and review: `gemini-3.1-flash-lite`;
- image generation: `gemini-3.1-flash-image`;
- image family: Nano Banana 2;
- default image size: 1K;
- landscape master artwork: 16:9.

The working structured API contract uses:

- endpoint `/v1beta/interactions`;
- header `Api-Revision: 2026-05-20`;
- object-form `response_format`.

API keys are read from local environment variables and never written to traces.

## 13. Formal experiment design

### Main comparison

- A: tileable square pattern and Custom Paint Job.
- B: weapon-space master artwork, OBJ-driven UV bake, and seam correction.
- C: B plus one bounded local correction and rollback gate.

Shared controls:

- theme and palette;
- backend and model revision;
- base seeds;
- candidate count;
- resolution;
- target asset;
- cameras;
- metrics.

Route-specific generation logic is intentionally different.

### Sub-ablations

1. Route B before versus after asset-seam correction using identical candidates.
2. Weighted ranking versus constraint-first/Pareto using an identical pool.

### Statistics

Report:

- paired mean;
- median;
- standard deviation;
- win rate;
- bootstrap 95% confidence interval.

Do not combine the formal A/B/C pool with the earlier edge-width technical sweep.

## 14. Accepted formal result

Run:

`runs/agent_dragon_multicandidate_v1/`

- selected direction: `Treasured Relic`;
- selected artwork: `artwork_04`;
- selected edge width: 4;
- asset seam: `0.0007776109029832148`;
- multi-view: `0.8166198880536247`;
- total: `0.8291228922780649`;
- Route C change: `-0.02195902089447299`;
- final route: B;
- final PNG and TGA pixels: identical.

## 15. Logging and reproducibility

Formal runs preserve:

- request and all generated prompts;
- model and provider identifiers;
- API traces with secrets removed;
- source images and SHA-256 hashes;
- source validation;
- mapped previews;
- UV outputs;
- texture, seam, multi-view, and readability metrics;
- decisions and rollback reasons;
- budgets, retries, and runtime;
- checkpoints and event timeline.

Formal runs must not be deleted or rewritten.

## 16. Client

`streamlit_app.py` is a thin client over `scripts/run_skinsmith_agent.py`.

It must not duplicate:

- planning;
- image generation;
- source validation;
- UV baking;
- rendering;
- scoring;
- refinement;
- export.

Replay supports both completed `agent_run_result.json` records and in-progress
checkpoint-only runs.

## 17. Workbench

Formal A/B/C outputs use `Custom Paint Job`.

Optional:

- Route A showcase: Hydrographic or Spray-Paint;
- Route C+ showcase: Gunsmith.

Optional finishes are excluded from formal A/B/C statistics.

See `WORKBENCH_VIEWING_GUIDE.md`.

## 18. Safety and legal boundaries

- Use original prompts and themes.
- Do not use logos, brands, teams, copied skins, or copyrighted characters.
- Disclose AI and model use.
- Do not commit or redistribute Valve assets.
- Do not publish to Steam Workshop as part of the course deliverable.
- Do not expose an unfiltered public image-generation service.

## 19. Verification

Run:

```powershell
& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v
& '.\.venv\Scripts\python.exe' -m compileall -q src scripts streamlit_app.py tests
```

Current baseline:

- 100 tests pass;
- compileall passes;
- Streamlit headless startup passes.
