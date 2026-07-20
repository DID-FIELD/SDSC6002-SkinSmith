# Public experiment evidence

This directory contains publication-safe evidence exported from the local
`runs/` workspace. The raw workspace remains local because it currently contains
about 2.43 GB of repeated intermediate textures, geometry arrays, provider image
payloads, and failed attempts that are unsuitable for ordinary Git distribution.

The public package retains the evidence needed to inspect the Agent workflow:

- checkpoint state and event history;
- compiled theme, style, directions, and design contract;
- all four source-plus-mapped candidate comparisons;
- source validation and generation logs;
- sanitized API request/response traces with provider, model, endpoint, prompts,
  usage, retries, decisions, and response metadata;
- the selected 2048 PNG/TGA and fixed left/right/top previews;
- SHA-256 and byte size for every packaged file.

Actual API keys, authorization values, Valve assets, large geometry caches, and
long embedded binary response fields are not published. Long trace values are
replaced by their original length and SHA-256, so their identity remains
auditable without redistributing the payload.

Rebuild the package with:

```powershell
.\.venv\Scripts\python.exe scripts\build_public_experiment_package.py
.\.venv\Scripts\python.exe scripts\build_public_garden_package.py
```

Current packages:

- `flower_workflow_v1/`: rejected flower alternatives and the cleaner ornamental
  branch, preserved as iteration and recovery evidence;
- `garden_workflow_v1/`: the current `garden` presentation case, including all
  three checkpoints, four mapped candidates, and the selected formal export.
