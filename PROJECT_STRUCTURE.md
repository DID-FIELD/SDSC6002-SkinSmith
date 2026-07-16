# SkinSmith Project Structure

SkinSmith separates reusable algorithms, creative knowledge, deployment adapters,
reproducible entry points, and preserved evidence.

## Top-level layout

```text
SkinSmith/
  config/                 versioned knowledge and asset contracts
  src/skinsmith/          reusable Python package
  scripts/                reproducible CLI and experiment entry points
  tests/                  built-in unittest suite
  assets/                 project-owned visual assets
  runs/                   preserved local experiment evidence
  third_party/            ignored external assets and model caches
  streamlit_app.py        thin client over the Agent CLI
```

## `src/skinsmith`

### Agent and planning

- `agent_runtime.py`  
  State machine, events, memory, tools, budgets, three human checkpoints,
  persistence, resume, revision, and standardized results.

- `agent_tools.py`  
  Theme expansion and creative planning tools.

- `design_routes.py`  
  AssetCreativeProfile, ThemePack, ThemeCompiler, Route A/B/C design contracts,
  and optional composition graphs.

- `style_planner.py`  
  StylePack loading, dynamic style synthesis, and art-direction planning.

- `api_backends.py`  
  OpenAI and Gemini structured-planning, image-generation, semantic-review, and
  mapped-readability adapters with redacted traces.

### Asset and UV processing

- `asset_spec.py`  
  Versioned mesh, UV, camera, semantic-region, and export binding.

- `game_asset_adapter.py`  
  Cross-weapon adapter abstraction and canonical axes.

- `uv_asset.py`  
  UV islands, welded topology, seam graph, paintable masks, and diagnostics.

- `weapon_space.py`  
  Canonical weapon frame, per-UV-pixel position/normal maps, continuous canvases,
  projection blending, and UV baking.

- `uv_compositor.py`  
  Component-aware composition and UV-edge safety correction.

- `route_b_composition.py` and `uv_region_composition.py`  
  Optional explicit composition-graph and UV-region research paths.

### Rendering, evaluation, and selection

- `obj_renderer.py`  
  OBJ loading, polygon triangulation, barycentric UV rendering, z-buffering, and
  left/right/top views.

- `evaluation.py`  
  Texture and multi-view metrics.

- `mapped_readability.py`  
  Recommendation-only comparison of planned elements with the source and mapped
  views.

- `selection.py`  
  Hard constraints, feasible filtering, Pareto dominance, and weighted baseline.

- `component_feedback.py` and `refinement.py`  
  Local diagnosis, bounded correction, locality checks, and rollback.

### Execution

- `route_asset_generation.py`  
  Provider-neutral image-job planning.

- `route_execution.py`  
  Candidate generation, source validation, low-cost mapping, formal execution,
  Route C, and export.

- `pipeline.py` and `ablation.py`  
  Baseline orchestration and formal experimental runners.

- `replay.py`  
  Safe loading of completed and checkpoint-only preserved runs.

## `config`

### Assets

- `assets/ak47_cs2.json`: accepted AK-47 full adapter.
- `assets/ak47_weapon_space_anchors.json`: creative profile and anchors.
- `assets/m4a4_cs2.json`: M4A4 transfer adapter.
- `assets/ak47_workbench_official.json`: retired legacy diagnosis adapter.

### Creative knowledge

- `design_themes/*.json`: validated ThemePacks.
- `styles/*.json`: validated StylePacks.
- `creative_api.json`: provider and model configuration.
- `route_b.json`: locked Route B thresholds and operating points.
- `workbench_finish_profiles.json`: route-aware finish profiles and suffixes.

## `scripts`

Important entry points:

- `run_skinsmith_agent.py`: canonical Agent CLI.
- `smoke_test.py`: deterministic baseline.
- `real_model_smoke_test.py`: real AK geometry baseline.
- `diffusion_real_model_test.py`: local SD-Turbo chain.
- `plan_design_routes.py`: planning-only route bundle.
- `generate_route_assets.py`: provider-backed source generation.
- `abc_ablation_formal.py`: formal A/B/C experiment.
- `build_report_ablation_tables.py`: report-ready evidence extraction.
- `make_known_good_uv_calibration.py`: deterministic Workbench calibration.

## `runs`

`runs/` is research evidence, not source code. Formal runs preserve:

- prompts and model identifiers;
- source images and hashes;
- validation traces;
- mapped previews;
- UV textures;
- metrics and decisions;
- events, checkpoints, budgets, retries, and runtime.

Do not rewrite or delete formal runs during repository cleanup.

## Dependency boundaries

- `src` must not depend on Streamlit.
- Streamlit must call the Agent orchestration rather than duplicate it.
- Asset contracts belong in `config`, not in algorithm code.
- Scripts may assemble tools, but reusable algorithms belong in `src`.
- External Valve assets and model weights remain ignored under `third_party`.
