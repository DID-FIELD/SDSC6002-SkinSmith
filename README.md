# SkinSmith

SkinSmith is an academic prototype for constraint-aware generation of transferable
game weapon finishes. Counter-Strike 2 is used only as a case study. The project does
not publish items to the Steam Workshop and is not affiliated with Valve.

Project documents:

- `report/overleaf/`: complete Overleaf-ready report source, figures, BibTeX, and
  machine-readable table data;
- `report/build/SkinSmith_Report_Draft.pdf`: locally compiled report draft for
  visual review;
- `RESEARCH_FRAMING.md`: locked title, research questions, contribution boundaries, and evidence mapping;
- `LITERATURE_REVIEW.md`: nine-theme related-work synthesis and closest-work comparison;
- `references.bib`: verified 34-source BibTeX database;
- `RUBRIC_EVIDENCE_MATRIX.md`: SDSC6002 assessment, CILO, milestone, and evidence mapping;
- `TECHNICAL_SPEC.md`: locked technical route, formulas, models, parameters, refinement policy, and experiments;
- `TECHNICAL_CONTRIBUTIONS.md`: contribution analysis and report/PPT/poster-ready technical narrative;
- `PROJECT_OVERVIEW.md`: current phase, final scope, and technical rationale for the team;
- `PROJECT_STRUCTURE.md`: layered architecture, directory responsibilities, data flow, and run-entry map;
- `WORKBENCH_VIEWING_GUIDE.md`: local A/B/C Workbench finish-style and TGA filename source of truth;
- `PROGRESS_AND_COMPLETION_CHECKLIST.md`: current completion status, two portability dimensions, remaining work, and next-session checklist;
- `VERIFICATION.md`: exact verified chain, commands, evidence, and limitations;
- `CODEX_CONTEXT.md`: authoritative progress and requirement context for future Codex sessions.

## Locked MVP

The two-week MVP implements this loop:

1. Compile any brief into validated `ThemePack` and `StylePack` objects: reuse
   compatible cached examples when they match, otherwise call injectable creative
   reasoning backends with the target weapon's `AssetCreativeProfile` to define both
   what to depict and how to depict it.
2. Route A uses `PatternDesigner` to create a dense, crop-tolerant, tileable square template.
3. Route B uses `WeaponThemeDesigner` to generate one square source per explicit
   composition group. Groups may span several components, repeat as coordinated
   units, remain component-specific, or provide the shared background. They are
   composed in continuous weapon space and baked into the UV atlas. Older themes
   without a graph retain the four-role compatibility path.
4. Render candidate previews through a swappable asset adapter and renderer.
5. Score texture, UV, multi-view, and semantic constraints.
6. Apply one bounded corrective action, accept only measured improvement, and save a full decision log.

The deterministic smoke-test uses a procedural generator and a tiled 2D preview.
The real-model smoke-test applies the same generated texture to the official local
AK-47 OBJ and renders left, right, and top views. SD-Turbo is accepted, and the
current Route-B smoke also verifies weapon-space design -> fragmented UV bake -> 3D reconstruction.

To inspect the new general art-direction layer without running image generation:

```powershell
& '.\.venv\Scripts\python.exe' scripts\plan_style.py `
  "Design an elegant but contemporary blue-and-white porcelain AK-47 skin" `
  --count 4
```

The built-in style library currently contains blue-and-white porcelain, original
cartoon mascots, and retro-futurist neon. These are examples behind one schema, not
three hard-coded project modes.

The theme library is a cache, not a whitelist. `ThemeCompiler` accepts a real
`ThemeSynthesisBackend` for previously unseen prompts such as landscape painting,
relief, marble, electronics, or chip circuitry. Without that backend the system
fails explicitly; it does not pretend that keyword rules provide open-ended creation.

Provider-neutral API adapters are implemented in `src/skinsmith/api_backends.py`:

- OpenAI Responses structured output or Gemini Interactions structured output can compile new `ThemePack` and `StylePack` objects;
- OpenAI GPT Image or Gemini native image generation can feed the existing texture pipeline;
- provider, model, request, response, and validation evidence are saved, but API keys are never logged;
- `ApiTextureGenerator` adapts either image provider to the existing Route-A candidate loop.

The selected production image backend is Nano Banana 2 through Gemini API:
`gemini-3.1-flash-image`, 1K, square. Live theme compilation uses
`gemini-3.1-flash-lite` after `gemini-3.5-flash` returned sustained high-demand
errors. The locked provider/model/budget gate is in `config/creative_api.json`;
OpenAI remains an optional backend comparison only.

ChatGPT Plus and the Gemini consumer subscription are not treated as project API
credentials. Configure a developer key locally through an environment variable;
never paste it into a prompt, JSON file, commit, or run log. A live Gemini theme
compile, for example, is:

```powershell
$env:GEMINI_API_KEY = "<set-locally>"
& '.\.venv\Scripts\python.exe' scripts\plan_design_routes.py `
  "Design an AK-47 skin based on dark marble faults and warm gold veins" `
  --theme-provider gemini `
  --output runs\theme_compilation_marble\route_design_bundle.json
```

Use `--theme-provider openai` to switch providers. `--theme-model` and
`--api-key-env` are explicit overrides, so model selection is configuration rather
than hard-coded project logic. Candidate count should expand only after the first
paid five-image smoke completes mapped A/B previews successfully.

The live marble test now compiles both layers dynamically. Its first pass exposed
the incorrect cached botanical style; the corrected pass generated the geological
material style `abyssal_vein_marble_v1`, with exact seven-component coverage and
four candidate directions. Redacted evidence is preserved under
`runs/theme_compilation_marble_dynamic_style/`. No paid image was generated in this
text-only acceptance.

After Gemini Paid Tier is enabled, internal A/B source assets can be generated with:

```powershell
& '.\.venv\Scripts\python.exe' scripts\generate_route_assets.py `
  runs\theme_compilation_chip_circuit\route_design_bundle.json `
  --output runs\nano_banana_chip_circuit
```

This command intentionally does not mark square images as accepted. They must still
pass the UV-mapping and AK-47 left/right/top preview stages.

Paid Tier is now active and the locked five-image marble smoke has completed: one
Route-A template plus hero/secondary/connector/background Route-B assets. The
resumable checkpoint prevented duplicate calls across transient TLS failures. Both
routes were mapped to the real AK-47 and rendered from left/right/top; evidence is
under `runs/nano_banana_marble_dynamic_style/`. That preserved Round 0 passes the
`0.01` asset-seam gate and outperforms Route A automatically, but its hero/connector
contain forbidden weapon-mockup fragments. A separate role-local refinement under
`runs/nano_banana_marble_dynamic_style_refined/` regenerates only those two paid
assets, reuses secondary/background, and remaps the same plan. Its corrected asset
seam is `0.006540`, multi-view score is `0.725273`, and total score is `0.763492`;
the AK preview no longer exposes a ghost weapon or rectangular source boundary. This
is an accepted 512 refinement candidate.

Candidate expansion is now direction-aware: `generate_route_assets.py --direction`
locks one validated StylePack alternative into distinct A/B prompts, while `--role`
still supports failure-local retries. A `tectonic_cluster` alternative exposed and
then verified a coordinate bug: canonical longitudinal/up anchors and top-left image
layer coordinates must be converted separately. After that fix, the retained
single-fissure candidate was selected at 512 (`asset seam 0.007113`, multi-view
`0.735170`, total `0.782189`) and baked to a formal 2048 RGB TGA with an 8 px safety
band (`asset seam 0.003943`, multi-view `0.749259`). The remaining gate is visual
confirmation in CS2 Workbench, not another image-generation call.

The first Workbench import then exposed an asset-contract mismatch rather than a
generation failure: the atlas was correct for the bound new-CS2 geometry OBJ, but
that UV was not accepted as the deployment layout for the tested Workbench path.
`config/assets/ak47_workbench_official.json` now binds Valve's matching official
Workbench AK-47 OBJ and UV sheet by hash and paints only faces inside its official
0-1 atlas. The re-baked 2048 candidate records asset seam `0.004429` and retains
`96.16%` of raw multi-view score. It is pending one Workbench reimport.

For Workbench inspection, formal A/B/C all use `Custom Paint Job`; this keeps the
finish style fixed while the design route changes. Route A may additionally be shown
with `Hydrographic` or `Spray-Paint`, but that pattern-native preview is showcase-only.
Optional C+ uses `Gunsmith` and is excluded from ablation statistics. The complete
local lookup and filename suffixes are locked in `WORKBENCH_VIEWING_GUIDE.md` and
`config/workbench_finish_profiles.json`; routine work should use those files instead
of re-reading the Valve website.

To inspect the corrected, genuinely different A/B/C design logic using the `Wild Lotus`
example without spending a generation run:

```powershell
& '.\.venv\Scripts\python.exe' scripts\plan_design_routes.py `
  "Design an AK-47 skin called Wild Lotus, inspired by a night pond" `
  --output runs\design_planning_wild_lotus\route_design_bundle.json
```

## Quick start

From this directory, using the project-local environment:

```powershell
& '.\.venv\Scripts\python.exe' scripts\smoke_test.py
```

Replay the accepted Agent run in the thin Streamlit client without making any new
model calls:

```powershell
& '.\.venv\Scripts\python.exe' -m streamlit run streamlit_app.py
```

The client defaults to `runs/agent_dragon_multicandidate_v1/` and presents the
selected text direction, indivisible source-plus-left/right/top artwork cards,
recommendation-only mapped-element readability, event/budget/retry state, rollback
decision, and final PNG/TGA downloads. New-task mode invokes the existing Agent CLI
for weapon selection, one-keyword ThemePack expansion and confirmation, direction
selection, mapped-artwork selection, checkpoint resume, and formal 2048/TGA export;
it does not duplicate the generation pipeline. AK-47 is the enabled full workflow;
M4A4 is currently labelled as transfer evidence rather than an equivalent formal
client target.

Outputs are written to `runs/smoke/`.

After following `ASSET_SETUP.md`, run the real-geometry path:

```powershell
& '.\.venv\Scripts\python.exe' scripts\real_model_smoke_test.py
```

Outputs are written to `runs/real_model_smoke/`.

After the SD-Turbo model has been cached locally, run the diffusion acceptance paths:

```powershell
$env:HF_HOME = "$PWD\third_party\huggingface"
$env:HF_HUB_OFFLINE = "1"
& '.\.venv\Scripts\python.exe' scripts\diffusion_smoke_test.py
& '.\.venv\Scripts\python.exe' scripts\diffusion_real_model_test.py
```

The pinned backend is `stabilityai/sd-turbo` revision
`b261bac6fd2cf515557d5d0707481eafa0485ec2`, using two inference steps at 512 px.
Model weights remain under ignored `third_party/` and must never be committed.

Every run writes:

- `agent_log.json`: full specification, per-view metrics, weights, ranking, and timing;
- `run_summary.csv`: compact candidate ranking for analysis and report tables;
- `candidates/`: raw and seamless textures;
- `previews/`: individual and combined weapon views.

With real geometry, the final score uses 65% texture-constraint score and 35%
multi-view render score. The deterministic baseline keeps a fixed seed so identical
code and inputs can be checked by file hashes.

## Publication boundary

- Code may be published after dependency and license review.
- Valve models, UV sheets, and game files must not be committed to this repository.
- Official UV sheets are optional adapter resources. A sheet may be used only
  with its matching model/version; otherwise the atlas is derived from the OBJ.
- Valve resource index: https://www.counter-strike.net/workshop/workshopresources
- Generated samples must use original prompts and pass manual IP review.
- Steam Workshop submission is explicitly outside the course deliverable.
