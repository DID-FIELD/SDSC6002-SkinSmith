# SkinSmith Next-Session Handoff

> Updated: 2026-07-20
> Canonical context: `CODEX_CONTEXT.md`  
> Accepted benchmark run: `runs/agent_dragon_multicandidate_v1/`
> Rejected iteration: `runs/agent_flower_demo_v1/` and `runs/agent_flower_ornamental_v2/`
> Current presentation case: `runs/agent_garden_demo_v1/`

## Current status

The garden presentation case is now complete through Workshop and in-game
validation while YUAN Ye continues to wait for supervisor feedback. Do not
restart implementation or expand the technical scope unless feedback requires it.

The complete Agent workflow is implemented:

```text
Select registered weapon + enter one theme keyword
  -> expand and confirm ThemePack
  -> generate and select one textual art direction
  -> generate 3-4 landscape master artworks
  -> map every artwork to weapon left/right/top previews
  -> human selects one indivisible source-and-views candidate
  -> reuse the exact selected source for formal 2048 UV baking
  -> Route B/C evaluation and rollback
  -> PNG/TGA export
```

AK-47 is the accepted full target. M4A4 remains transfer evidence only.

The fresh `garden` case completed the same three-checkpoint workflow on
2026-07-20. It expanded to `Midnight Serenity`, locked `Spectral Movement`,
human-selected `artwork_02`, selected Route B after Route-C rollback, and exported
the exact selected source at 2048. It is now the narrative spine of the rebuilt
presentation; retain the dragon run as stronger benchmark evidence.

Garden TGA for Workbench:

`runs/agent_garden_demo_v1/execution/route_b/selected__route-b__custom-paint-job.tga`

Fixed left/right/top Workshop captures, one Item Editor settings screenshot, and
two in-game first-person views are now preserved in the run and in
`experiments/public/garden_workflow_v1/engine_validation/`.

Checkpoint 3 demonstrates the reason for human choice: `artwork_03` had the
highest automatic preview total (`0.8955`), while the user selected `artwork_02`
(`0.8293`). The metric screens feasibility and supports recommendations; it does
not replace aesthetic judgment.

Publication-safe experiment evidence is tracked under `experiments/public/` for
both the rejected flower iteration and the current garden workflow. It contains
inspectable checkpoints, candidates, selected final assets, and sanitized
provider metadata without API keys. The 2.43 GB raw `runs/` workspace remains
local and ignored.

## Current garden presentation result

- Direction: `Spectral Movement`
- Direction ID: `candidate_02_direction_koi_flow`
- Human-selected artwork: `artwork_02` (`Ornamental Tapestry`)
- Preview auto-top candidate: `artwork_03` (`0.8954536359951683`)
- Human-selected preview total: `0.8292713047937368`
- Selected route: Route B
- Edge width: 4
- Formal asset seam: `0.001245730606220989`
- Formal multi-view: `0.8116765168562788`
- Formal total: `0.8173740781485412`
- Route C change: `-0.016233440019044476`, correctly rolled back
- Final TGA SHA-256: `8615e42473d86719a6ebb1dc2f2fa239381f635ab9c648475c94430fe28f4bb0`
- Engine status: fixed Workshop views, settings panel, and two in-game views
  preserved and publication-safe

## Locked dragon benchmark result

- Direction: `Treasured Relic`
- Direction ID: `candidate_04_d4_mythic_relic`
- Human-selected artwork: `artwork_04`
- Final phase: `completed`
- Image calls: 6
- Role retries: 1
- Refinement rounds: 1
- Selected route: Route B
- Edge width: 4
- Asset seam: `0.0007776109029832148`
- Multi-view: `0.8166198880536247`
- Total: `0.8291228922780649`
- Route C change: `-0.02195902089447299`, correctly rolled back

Source:

`runs/agent_dragon_multicandidate_v1/artwork_candidates/artwork_04/source/route_b_master_artwork.png`

Source SHA-256:

`0299f43512b9a946eeedc0a58c418424c7bddfad8e0c9dd54610a4c13f63750a`

Final outputs:

- PNG: `runs/agent_dragon_multicandidate_v1/execution/route_b/route_b_selected.png`
- TGA: `runs/agent_dragon_multicandidate_v1/execution/route_b/selected__route-b__custom-paint-job.tga`
- Multi-view: `runs/agent_dragon_multicandidate_v1/execution/route_b/route_b_width_4_multiview.png`
- TGA SHA-256: `82d18671e50cf59501c901ad86916a04637464883e79d5375b4cb37f96bc2aac`

PNG and TGA are 2048 x 2048 RGB and decode to identical pixels.

## Recommendation-only readability

Report:

`runs/agent_dragon_multicandidate_v1/execution/mapped_element_readability.json`

- Source fulfillment: `0.938562091503268`
- Left: `0.6016339869281045`
- Right: `0.6016339869281045`
- Top: `0.3993464052287582`
- Recommendation: `0.6656372549019607`
- Visible elements above threshold: 8 of 16

These scores explain and recommend. Human selection remains authoritative.

## Next work

Academic Phase 1 is complete and preserved in:

- `RESEARCH_FRAMING.md`: locked title, problem, five research questions,
  contribution boundaries, and evidence mapping.
- `LITERATURE_REVIEW.md`: nine-theme synthesis, research gap, and closest-work
  comparison.
- `references.bib`: 34 unique primary sources; every literature-review citation
  resolves and every database entry is cited.
- `RUBRIC_EVIDENCE_MATRIX.md`: all seven assessment dimensions, five CILOs,
  milestones, evidence rules, and report production gates.

The academic poster and rebuilt presentation are available at:

- `report/build/SkinSmith_A0_Poster.pptx`
- `report/build/SkinSmith_A0_Poster.pdf`
- `report/build/SkinSmith_Supervisor_Presentation.pptx`
- `report/build/SkinSmith_Supervisor_Presentation.pdf`

The poster is a revised 1188.993 x 840.978 mm A0 landscape academic poster. Its
original layout is preserved, while candidate/view labels, Route-C evidence,
base-colour material scope, test count, checkpoint chronology, valid demo command,
member IDs, and supervisor metadata are corrected against the project evidence.
The PPTX is the primary submission artifact. It must be sent to the supervisor
and `ds.go@cityu.edu.hk` by 12:00 noon on 2026-08-02, and a poster presentation
must be arranged with the supervisor before then. The presentation contains 13
evidence-led slides built around the complete garden CP1/CP2/CP3 flow, the
score-versus-human-choice comparison, formal Route B/C evidence, actual CS2
Workshop settings and fixed views, and two in-game captures. Every slide contains
English speaker notes. The PPTX was rendered slide by slide, passed automated
overflow testing, and its PDF was exported through Microsoft PowerPoint.

The report and project documentation now state the material boundary explicitly:
SkinSmith generates and evaluates base-colour / Custom Paint Job textures, not
normal, roughness, metallic, height, displacement, or a complete PBR material.
Workbench lighting must not be presented as generated surface detail.

The Overleaf ZIP was regenerated from the tracked source and independently
compiled. It contains the revised Discussion and Conclusion and reproduces the
33-page report draft.

Resume the academic and publication work in this order:

1. Wait for and record the supervisor response supplied by YUAN Ye.
2. Classify each requested change as report, poster, presentation, code/demo, or
   out-of-scope request.
3. Resolve contradictions explicitly and preserve the locked technical evidence.
4. Apply approved supervisor feedback to `report/overleaf/`.
5. Freeze the approved report and export the final report PDF.
6. Re-check the rebuilt garden presentation only if supervisor feedback changes
   claims, figures, or scope.
7. Run the final cross-artifact consistency and visual QA after feedback.
8. Before 12:00 noon on 2026-08-02, send the final A0 PPTX to the supervisor and
   `ds.go@cityu.edu.hk`, and confirm the poster-presentation arrangement.

The completed import path, settings, filenames, hashes, and interpretation
boundary are recorded in `WORKBENCH_VIEWING_GUIDE.md` and the public
engine-validation manifest. Keep the garden captures separate from rejected
flower and diagnostic cases.

The revised cover lists all five English names and student IDs and identifies
YUAN Ye as project lead and integration owner. The registered topic remains as a
cover subtitle, while the Introduction, Discussion, and Appendix document the
supervisor-approved narrowing to SkinSmith.

The group has confirmed the five-member contribution statement. The detailed
contribution table remains in the report, while the provisional confirmation
paragraph after it has been removed.

## Non-negotiable boundaries

- Use `config/assets/ak47_cs2.json` for the accepted AK-47 contract.
- Do not switch to the legacy UV or assume a V flip.
- Do not restore per-component generation as the default.
- Do not add a third weapon before deliverables are complete.
- Do not delete formal runs, ignored Valve assets, or user files.
- Do not let automatic scores replace human selection.

## Verification baseline

- 100 tests pass.
- All 100 tests pass after adding resumable reuse of preserved passing Route-B
  sources.
- `compileall` passes.
- Streamlit headless startup passes.
- No new image call is required merely to continue the academic deliverables.
- The rebuilt 13-slide garden presentation passes automated overflow testing and
  contains non-empty English speaker notes on all 13 slides.
- Six publication-safe Workshop/in-game images are hashed under
  `experiments/public/garden_workflow_v1/engine_validation/`; no API credential,
  account identifier, chat overlay, or private notification is visible.
- GitHub publication completed successfully on 2026-07-17.
- Remote: `https://github.com/DID-FIELD/SDSC6002-SkinSmith`.
- Published merge commit: `ee628e1`; the pre-existing `LICENSE` history was
  preserved.
- Publication-status documentation was subsequently updated on remote `main` at
  commit `49e34ee`.
- Ignored evidence, credentials, Valve assets, model weights, and local
  environments were not uploaded.
- Follow `SECURITY_RELEASE_CHECKLIST.md` before staging or publishing.

## Feedback intake rule

When feedback arrives, preserve the exact wording and source of each comment.
Do not treat an informal suggestion as approval to alter formal evidence,
contribution ownership, research claims, or project scope. Record accepted,
rejected, and deferred changes in the continuity documents.
