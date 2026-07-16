# SkinSmith GitHub Release Safety Checklist

> Updated: 2026-07-17  
> Target repository: `https://github.com/DID-FIELD/SDSC6002-SkinSmith`

## Current status

- Git remote `origin` is configured as
  `https://github.com/DID-FIELD/SDSC6002-SkinSmith.git`.
- No GitHub push has occurred.
- The user explicitly authorized the initial GitHub upload on 2026-07-17.
- The remote `main` branch contains one existing `Initial commit` with `LICENSE`;
  the local project publication will preserve and merge that history.
- The current non-ignored publication candidate contains approximately 231 files
  and 25.82 MB. The largest candidate file is the 7.61 MB supervisor
  presentation.

## Secret audit

- Common OpenAI, Google, GitHub, AWS, Slack, and private-key formats were scanned
  across all non-ignored publication candidates.
- No candidate file matched a real credential format.
- Configuration and code contain environment-variable names such as
  `OPENAI_API_KEY` and `GEMINI_API_KEY`, but no credential values.
- API trace code records `api_key_recorded: false` and reads credentials only
  from the local environment.
- Three ignored historical trace files produced Google-key-shaped false positives
  inside very large model `signature` or image `data` strings. These were not
  credential fields. The entire `runs/` tree remains ignored and must not be
  force-added.

## Required exclusions

The following are excluded by `.gitignore` and must remain excluded:

- `.env`, `.env.*`, Streamlit secrets, private keys, and certificate-key files;
- `.venv/`, caches, editor metadata, and local Agent metadata;
- `runs/` experiment payloads and API traces;
- `third_party/` Valve geometry, official UV sheets, downloaded archives, and
  model caches;
- `models/` and common model-weight formats;
- `tmp/`, PowerPoint inspection files, and Office-render QA subdirectories.

Final PDF, PowerPoint, Overleaf ZIP, report source, poster source, code,
configuration, tests, and original project-owned showcase assets remain eligible
for publication.

## Pre-stage gate

Before `git add`:

1. Re-run the secret-format scan on non-ignored files.
2. Confirm `git status --short --ignored` still shows `runs/`, `third_party/`,
   `.venv/`, `tmp/`, and QA render directories as ignored.
3. Review every file under `assets/` and `report/overleaf/figures/` for provenance
   and publication rights.
4. Decide whether the review-draft PDF should be published or replaced by the
   approved final report PDF.
5. Confirm the five group members approve the contribution statement.

## Post-stage gate

After staging but before committing:

1. Inspect `git diff --cached --name-status`.
2. Re-run the secret scan against staged blobs.
3. Verify that no path begins with `runs/`, `third_party/`, `.venv/`, `tmp/`, or
   `models/`.
4. Verify that no Valve OBJ, UV sheet, VPK, model weight, local credential, or
   private trace is staged.
5. Run the relevant test and artifact checks.

## Publication rule

The user has now explicitly approved the reviewed initial publication. Continue
only if the staged-file audit passes. Stop rather than force-adding any ignored
path or credential-bearing file.
