# SkinSmith

SkinSmith is a constraint-aware generative Agent for game weapon skin design. It
turns a short theme keyword into multiple art directions and mapped weapon
concepts, keeps the user in control at three explicit checkpoints, and evaluates
the selected design after it has been baked to the target asset.

The project was developed for the City University of Hong Kong SDSC6002 Research
Project. Counter-Strike 2 is used as the main case study, but the research focus is
the reusable image-processing Agent, not the game itself.

## Project goal

A visually attractive rectangular image is not automatically a usable weapon
texture. UV atlases split, rotate, and repack the visible surface, so important
motifs may disappear, seams may become visible, and a design that works from one
view may fail from another.

SkinSmith addresses this gap by evaluating the reconstructed asset rather than the
source image alone. The system combines:

- theme and art-direction planning;
- human selection at three checkpoints;
- continuous weapon-space composition;
- OBJ/UV-driven texture baking;
- fixed left, right, and top rendering;
- asset-seam and multi-view evaluation;
- hard feasibility gates and Pareto-style selection;
- one bounded refinement attempt with rollback.

## Human-Agent workflow

```text
Select a registered weapon and enter one keyword
  -> Checkpoint 1: confirm the expanded visual world
  -> Checkpoint 2: select one of 3-4 textual art directions
  -> generate 3-4 artwork candidates
  -> map every candidate to left/right/top weapon views
  -> Checkpoint 3: select one source-and-mapped-view card
  -> reuse the exact selected source for formal execution
  -> bake, render, evaluate, refine once if justified, and export
```

For example, the keyword `dragon` is expanded into subjects, symbols, materials,
palette, atmosphere, supporting details, and prohibited content. The Agent then
proposes materially different directions instead of treating the keyword as a
complete prompt.

Model review can recommend a candidate, but it does not replace the user's
decision. Formal execution cannot begin until the user selects the mapped artwork.

## Design routes

SkinSmith evaluates three related routes:

- **Route A - pattern-first baseline:** creates a dense, crop-tolerant, tileable
  texture without a weapon-level composition plan.
- **Route B - weapon-space composition:** arranges the design in a continuous
  canonical weapon frame before baking it into the fragmented UV atlas.
- **Route C - bounded correction:** diagnoses one mapped weakness, applies a local
  correction, and accepts it only if constraints and the minimum improvement rule
  pass; otherwise it rolls back to Route B.

The AK-47 adapter is the complete end-to-end case. The M4A4 adapter demonstrates
transfer of the Agent contract, but it is not presented as an equivalent completed
production target.

## Verified findings

The formal paired experiment contains four shared candidates. Compared with the
pattern-first baseline, weapon-space Route B:

- reduced mean asset-seam error from `0.26997` to `0.00063` (`99.77%`);
- increased mean multi-view score from `0.76898` to `0.82911`;
- improved both measures for all four paired candidates.

In the accepted live three-checkpoint run, the user selected:

- theme keyword: `dragon`;
- art direction: `Treasured Relic`;
- artwork: `artwork_04`;
- final route: Route B;
- asset-seam error: `0.0007776109029832148`;
- multi-view score: `0.8166198880536247`;
- total score: `0.8291228922780649`.

The Route C correction reduced the score by `0.02195902089447299`, so the Agent
correctly rejected it and retained Route B. This rollback is part of the intended
behavior rather than a failed execution.

## Repository structure

```text
config/                 Asset, model, theme, style, and route configuration
src/skinsmith/          Agent runtime, generation, UV, rendering, and evaluation
scripts/                Planning, experiment, diagnostics, and replay entry points
tests/                  Unit and integration tests
experiments/public/     Sanitized workflow evidence, outputs, and API metadata
assets/showcase/        Project-owned example artwork
streamlit_app.py        Thin interactive client over the same Agent runtime
```

Raw `runs/`, `third_party/`, local environments, model weights, Valve assets, and
temporary rendering files are intentionally excluded from GitHub. A compact
publication-safe experiment package is available under `experiments/public/`.
It includes checkpoints, events, planning records, candidate comparisons, final
PNG/TGA outputs, metrics, hashes, and sanitized provider traces. API keys and
long embedded binary response values are not published.

## Requirements

- Windows and PowerShell are used by the documented commands.
- Python 3.13 is the verified local version.
- A project-local virtual environment is recommended.
- The deterministic procedural path does not require an image API.
- Provider-backed generation requires a developer API key supplied through an
  environment variable.
- Real AK-47 or M4A4 mapping requires locally obtained, authorized geometry. See
  `ASSET_SETUP.md`; Valve geometry and UV files are not redistributed here.

Install the Python dependencies:

```powershell
python -m venv .venv
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
```

## Quick start

Run the automated test suite:

```powershell
& '.\.venv\Scripts\python.exe' -m unittest discover -s tests -v
```

Run the deterministic smoke test:

```powershell
& '.\.venv\Scripts\python.exe' scripts\smoke_test.py
```

Start the Streamlit client:

```powershell
& '.\.venv\Scripts\python.exe' -m streamlit run streamlit_app.py
```

The client exposes weapon selection, one-keyword theme expansion, direction
selection, mapped-artwork selection, progress and retry state, final evaluation,
rollback, and PNG/TGA export. Preserved-run replay is available only when the
corresponding local `runs/` evidence is present.

## Optional provider-backed generation

Credentials are read from environment variables and are never intended to be
stored in configuration, logs, or commits. For Gemini-backed generation:

```powershell
$env:GEMINI_API_KEY = "<set-locally>"
& '.\.venv\Scripts\python.exe' scripts\run_skinsmith_agent.py dragon
```

Provider and model defaults are defined in `config/creative_api.json`. OpenAI and
Gemini adapters share the same validated planning and generation interfaces.

## Scope and limitations

- SkinSmith is an academic prototype, not a commercial authoring platform.
- The verified output is a base-color / Custom Paint Job texture. The current
  system does not generate normal, roughness, metallic, height, displacement, or
  a complete PBR material set.
- The current renderer is a controlled software evaluator, not a photorealistic
  replacement for the game engine.
- CS2 Workbench lighting and reflectance are engine effects and are not claimed as
  model-generated surface detail.
- Automated semantic readability is recommendation-only.
- AK-47 is the complete case; M4A4 provides bounded transfer evidence.
- The system does not claim that one UV layout or texture transfers directly
  across weapons.
- Steam Workshop publication is outside the project scope.

The next technical priorities are aligned multi-channel material generation,
cross-channel and engine-side validation, automated fixed-view Workbench capture,
additional asset adapters, stronger perceptual measures, and a user study of the
three checkpoints. The immediate evidence task is to capture the selected garden
TGA in fixed left, right, and top Workbench views plus the import settings, then
use that complete workflow as the presentation case.

## Responsible use and licensing

The repository does not redistribute Valve models, UV sheets, game files, model
weights, or API credentials. Generated examples use original prompts and require
manual rights review before external use. Counter-Strike 2 is referenced only as
an academic case study; this project is not affiliated with or endorsed by Valve.

See `LEGAL_NOTICE.md`, `ASSET_SETUP.md`, and the repository `LICENSE` before reuse.
