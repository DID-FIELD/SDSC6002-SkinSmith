# SkinSmith Next-Session Handoff

> Updated: 2026-07-17  
> Canonical context: `CODEX_CONTEXT.md`  
> Accepted formal run: `runs/agent_dragon_multicandidate_v1/`

## Current status

Session closed on 2026-07-17. The project is intentionally paused while YUAN Ye
waits for feedback from the supervisor and group members. Continue from the
feedback review; do not restart implementation or expand the technical scope.

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

## Locked formal result

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

The academic poster and presentation are now complete:

- `report/build/SkinSmith_A0_Poster.pptx`
- `report/build/SkinSmith_A0_Poster.pdf`
- `report/build/SkinSmith_Supervisor_Presentation.pptx`
- `report/build/SkinSmith_Supervisor_Presentation.pdf`

The poster is a true 1189.04 x 841.11 mm A0 landscape academic poster. The
presentation contains ten slides. Both were exported through Microsoft
PowerPoint and visually checked; the presentation also passed automated overflow
testing.

Resume the academic and publication work in this order:

1. Collect the supervisor and group-member responses supplied by YUAN Ye.
2. Classify each requested change as report, poster, presentation, code/demo,
   contribution record, or out-of-scope request.
3. Resolve contradictions explicitly and preserve the locked technical evidence.
4. Apply approved feedback to the report source under `report/overleaf/`.
5. Update the poster and presentation only where the approved report narrative or
   group record changes.
6. Freeze the approved report and export the final report PDF.
7. Run the final submission consistency and visual QA.
8. Optionally add one final Workbench screenshot of the accepted TGA.

The revised cover lists all five English names and student IDs and identifies
YUAN Ye as project lead and integration owner. The registered topic remains as a
cover subtitle, while the Introduction, Discussion, and Appendix document the
supervisor-approved narrowing to SkinSmith.

## Non-negotiable boundaries

- Use `config/assets/ak47_cs2.json` for the accepted AK-47 contract.
- Do not switch to the legacy UV or assume a V flip.
- Do not restore per-component generation as the default.
- Do not add a third weapon before deliverables are complete.
- Do not delete formal runs, ignored Valve assets, or user files.
- Do not let automatic scores replace human selection.

## Verification baseline

- 100 tests pass.
- `compileall` passes.
- Streamlit headless startup passes.
- No new image call is required merely to continue the academic deliverables.
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
