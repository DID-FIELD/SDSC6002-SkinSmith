# CS2 Workbench Viewing Guide

This guide records the local viewing contract for SkinSmith evidence. Use it
instead of re-deriving settings from the Valve website during routine work.

## Formal A/B/C finish style

Formal Route A, Route B, and Route C outputs use:

`Custom Paint Job`

Keeping the finish style fixed ensures that the experiment changes the design
route rather than the Workbench material interpretation.

Formal filename suffixes:

- `__route-a__custom-paint-job`
- `__route-b__custom-paint-job`
- `__route-c__custom-paint-job`

## Optional showcase finishes

- Route A may also be previewed with `Hydrographic` or `Spray-Paint`.
- These previews are showcase-only and are excluded from A/B/C statistics.
- Optional Route C+ may use `Gunsmith`.
- Route C+ is also excluded from formal ablation statistics.

## Asset contract

Use the accepted new-CS2 HD AK-47 geometry and its matching UV:

`config/assets/ak47_cs2.json`

Do not use:

- `config/assets/ak47_workbench_official.json` as the default;
- the legacy AK-47 UV sheet with the new geometry;
- a default vertical flip;
- a TGA produced for another weapon.

The accepted export is a 2048 x 2048, 24-bit RGB TGA. PNG and TGA pixels must be
identical after decoding.

## Inspection order

1. Import the TGA as a Custom Paint Job.
2. Use stable lighting and camera settings.
3. Capture left, right, and top views.
4. Check for missing paint, transparent regions, wrong UV orientation, island
   mismatch, obvious seam lines, and unintended source-image boundaries.
5. Compare the Workbench views with the preserved software renders.
6. Record screenshot paths and hashes in the relevant run manifest.

## Interpretation boundary

The software renderer is suitable for repeatable technical comparison, but it is
not a photorealistic replacement for CS2 Workbench. Workbench screenshots are
final visual evidence; software renders remain the reproducible evaluation loop.

## Accepted references

- Known-good calibration:
  `runs/known_good_uv_calibration/`
- Accepted formal dragon output:
  `runs/agent_dragon_multicandidate_v1/execution/route_b/`
- Finish profile configuration:
  `config/workbench_finish_profiles.json`
