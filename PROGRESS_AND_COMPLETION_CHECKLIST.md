# SkinSmith Progress and Completion Checklist

> Updated: 2026-07-20
> Canonical evidence and history: `CODEX_CONTEXT.md`

## Completed

### Asset and UV pipeline

- [x] Locked the new CS2 HD AK-47 OBJ and its mesh-derived UV contract.
- [x] Confirmed local render orientation against CS2 Workbench.
- [x] Versioned the AK-47 adapter in `config/assets/ak47_cs2.json`.
- [x] Retired the legacy UV and default V-flip assumptions.
- [x] Added an M4A4 GameAssetAdapter transfer case.

### Generation, mapping, and evaluation

- [x] Route A tileable-pattern baseline.
- [x] Route B continuous weapon-space design and OBJ-driven UV bake.
- [x] Left, right, and top software renders.
- [x] Square-border and real asset-seam metrics.
- [x] Constraint-first/Pareto candidate selection.
- [x] One bounded Route C correction with acceptance or rollback.
- [x] Exact-fit 2048 RGB PNG/TGA export and hash logging.
- [x] Formal A/B/C experiment and report-ready ablation tables.

### Reusable Agent

- [x] Weapon selection plus one-keyword theme input.
- [x] `ThemeCompiler` expansion into subjects, symbols, environment, materials,
  connectors, atmosphere, palette, and prohibited content.
- [x] `awaiting_theme` confirmation checkpoint.
- [x] Three or four theme-specific textual art directions.
- [x] `awaiting_direction` selection checkpoint.
- [x] Three or four dense landscape master-artwork candidates.
- [x] Low-cost OBJ/UV mapping for every candidate.
- [x] One indivisible source + left + right + top candidate card.
- [x] Recommendation-only mapped-element readability review.
- [x] `awaiting_artwork` human selection checkpoint.
- [x] Exact reuse of the selected source for formal execution.
- [x] State, events, memory, tools, budgets, retries, checkpoints, and recovery.
- [x] Shared CLI/Python/Streamlit orchestration.

### Accepted evidence

- [x] Procedural and SD-Turbo generation paths.
- [x] Live Gemini ThemePack and StylePack compilation.
- [x] Live uncached marble, astrolabe, and deep-sea-ruins planning.
- [x] Live multi-candidate dragon run with formal 2048 export.
- [x] Human-selected `artwork_04` from `runs/agent_dragon_multicandidate_v1/`.
- [x] Route B asset seam `0.0007776109029832148`.
- [x] Route B multi-view score `0.8166198880536247`.
- [x] Route B total score `0.8291228922780649`.
- [x] Route C rollback after a score change of `-0.02195902089447299`.
- [x] 100 automated tests passing.

### English submission readiness

- [x] Source code, comments, tests, configuration, and Streamlit UI copy are English.
- [x] Submission-facing documentation uses English content and filenames.
- [x] References to retired `_ZH.md` filenames are removed.
- [x] Formal `runs/` evidence is preserved unchanged for hash and replay integrity.

## Client status

- [x] Thin Streamlit client over the same Agent CLI/API.
- [x] AK-47 full end-to-end target enabled.
- [x] M4A4 shown honestly as transfer evidence, not as an equivalent formal target.
- [x] Theme, direction, and artwork checkpoints.
- [x] Events, progress, errors, budgets, retries, and recovery state.
- [x] Preserved-run replay.
- [x] Final PNG/TGA downloads.

## Remaining academic deliverables

- [x] Phase 1 research framing, 34-source literature base, related-work synthesis,
  and rubric-to-evidence matrix.
- [x] Complete English report manuscript in an Overleaf-ready LaTeX project.
- [x] Local pdfLaTeX/BibTeX compilation and 33-page visual QA draft.
- [x] Regenerated Overleaf ZIP independently compiles to the same 33-page PDF.
- [x] Five-member cover metadata, registered-topic traceability, scoped-project
  explanation, and detailed group contribution statement.
- [x] Report citation, evidence-path, placeholder, and production-marker audit.
- [ ] Final report PDF.
- [x] Revised A0 landscape poster PowerPoint, verified at 1188.993 x 840.978 mm,
  with project-backed claims, corrected charts, member metadata, PDF, and Office render.
- [ ] Rebuild the supervisor presentation around the complete flower workflow
  after flower Workbench screenshots arrive; retain English speaker notes on
  every slide and repeat PDF/Office-rendered QA.
- [x] Poster and presentation evidence audit for every reported number and figure.
- [ ] Final reproducibility, disclosure, and visual QA.

## GitHub publication

- [x] Define the publication exclusions and release-safety checklist.
- [x] Scan the non-ignored publication candidate for common credential formats.
- [x] Confirm that `runs/`, Valve assets, model caches, local environments, and
  PowerPoint QA files are ignored.
- [x] Create the reviewed initial Git commit.
- [x] Push the reviewed publication set to
  `https://github.com/DID-FIELD/SDSC6002-SkinSmith`.
- [x] Verify the remote branch and repository contents after the push.

## Awaiting external review

- [ ] Receive supervisor feedback.
- [x] Receive and consolidate contribution feedback from all group members.
- [x] Confirm the five-member contribution statement.
- [ ] Classify and document every requested revision.
- [ ] Apply approved report revisions.
- [x] Apply the requested presentation rebuild and evidence-backed A0 poster revision.
- [ ] Send the final A0 poster PPTX to the supervisor and `ds.go@cityu.edu.hk`
  by 12:00 noon on 2026-08-02.
- [ ] Arrange the poster presentation with the supervisor before the deadline.
- [ ] Freeze the final report PDF and submission artifacts.

## Completion conditions

- [x] A real three-checkpoint Agent can progress from one keyword to a
  human-selected formal texture.
- [x] Streamlit uses the same Agent orchestration and is not a static mock-up.
- [x] Prompts, model identifiers, calls, validation, sources, views, UV outputs,
  metrics, decisions, and hashes are preserved in formal runs.
- [x] Report, poster, and presentation claims are traceable to formal evidence.
- [ ] AI use, copyright boundaries, failed cases, and renderer limitations are
  disclosed clearly.
- [ ] Portability claims remain limited to adapter-based transfer.
- [x] Report and project documentation distinguish base-colour texture output from
  normal, roughness, metallic, height, displacement, and full PBR material output.
- [ ] Capture the flower TGA in fixed Workbench left/right/top views and preserve
  one settings-panel screenshot for the complete presentation flow.

## Frozen boundaries

- Do not revisit AK-47 UV orientation without contradictory evidence.
- Do not return to the legacy Workbench UV.
- Do not restore per-component generation as the default workflow.
- Do not add a third weapon before the academic deliverables are stable.
- Do not represent a single generated image as completion of the Agent.
