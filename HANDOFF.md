# SkinSmith Project Handoff

> Last updated: 2026-07-15 (Asia/Shanghai)
>
> Legacy handoff retained for history. Future Codex sessions must use `CODEX_CONTEXT.md` as the authoritative continuity file.
> For the exact 2026-07-16 stopping point and first next action, read `NEXT_SESSION_HANDOFF.md` immediately after `CODEX_CONTEXT.md`.

## 1. Project identity

- Course: SDSC6002 Research Project
- Topic: Topic 22 — Latent Vision / Image Generation
- Supervisor: Prof. Yu Yang
- Working title: **SkinSmith: A Constraint-Aware Generative Agent for Game Weapon Skin Design — A CS2 Case Study**
- Student: YUAN Ye, 60089337
- Team members: YUAN Ye, CHEN Yuhong, Ben Tangjie, Wang Zhengye, WANG Lihui
- Intended final project directory: `D:\project\SDSC6002-SkinSmith`
- Important boundary: do not inspect, modify, move, or delete any other project under `D:\project`.

## 2. Confirmed academic scope

Prof. Yu Yang advised that, because less than three weeks remained, the group should narrow the scope and focus on the technical development of an image-processing agent. It does not have to remain the original broad Latent Vision image-generation topic; a completed image-processing agent is sufficient for a Master's research project.

The selected system is an academic prototype that assists community weapon-skin development. It should demonstrate an agentic pipeline rather than merely produce attractive images:

1. Accept a design brief and style configuration.
2. Generate candidate weapon textures.
3. Repair or enforce seamless texture boundaries.
4. Preview the texture, ultimately on a real weapon UV/3D model from multiple views.
5. Measure visual/technical quality.
6. Rank candidates and automatically select the best one.
7. Save reproducible parameters, metrics, and an experiment log.

## 3. Publication and legal boundary

- Do **not** submit results to Steam Workshop as part of the course project.
- Treat the work as an academic prototype and optional public GitHub code repository.
- Clearly disclose AI assistance and model/tool usage.
- Do not use third-party logos, brands, anime characters, team marks, copyrighted artwork, or copied skin designs.
- Use original prompts, themes, patterns, and user-created assets.
- Do not claim copyright or ownership over Valve weapon models/assets.
- Do not commit or redistribute Valve model/material packages in Git; document how users obtain them from Valve instead.
- Any future Workshop submission requires a separate rights and Steam-terms review.

## 4. Deadline and deliverables

- Final deadline: **2 August 2026, 12:00 noon**.
- Submit to the supervisor and `ds.go@cityu.edu.hk`:
  - research project report in PDF;
  - A0 landscape poster in PowerPoint, 1189 × 841 mm.
- A poster presentation with the supervisor must be arranged before the deadline.
- The group decided to finish without requesting an extension.
- Target: complete the entire technical chain immediately, freeze development during the week of 13–19 July, then concentrate on experiments, report, poster, and presentation.

## 5. Current implementation status

The repository already contains a functioning baseline pipeline:

- procedural generation of four texture candidates;
- seamless-boundary repair;
- 2D tiled previews;
- quantitative evaluation;
- automatic best-candidate selection;
- JSON experiment logs;
- unit test for seamless repair;
- smoke-test outputs in `runs/smoke`.

The seam regression was corrected after visual inspection. Typical seam errors improved from approximately `0.14–0.22` to `0.007–0.009`. The current smoke run selects `candidate_02`.

Completed on 14 July after migration to the final workspace:

- official Valve geometry package downloaded locally and kept under ignored `third_party/`;
- AK-47 OBJ extracted and validated (21,548 UV coordinates, 26,133 triangle faces);
- lightweight OBJ/UV renderer implemented without new dependencies;
- real-model smoke chain renders left, right, top, and contact-sheet previews;
- multi-view contrast, saturation, detail, and consistency now affect selection;
- each run exports full JSON evidence and a compact ranking CSV;
- OBJ parser regression test added; all current tests pass.

Not yet complete:

- actual diffusion/image-generation backend;
- higher-fidelity CS2 Workbench rendering and material validation;
- semantic/style-consistency scoring;
- agent iteration based on evaluator feedback;
- systematic experiments across multiple styles;
- report, poster, and presentation.

## 6. Repository map

- `README.md` — setup and overview
- `PROJECT_PLAN.md` — research and implementation plan
- `LEGAL_NOTICE.md` — legal/release boundary
- `ASSET_SETUP.md` — external asset instructions
- `requirements.txt` — Python dependencies
- `config/themes.json` — theme definitions
- `src/skinsmith/spec.py` — data specifications
- `src/skinsmith/generator.py` — baseline texture generator
- `src/skinsmith/seamless.py` — seamless repair
- `src/skinsmith/evaluation.py` — quality metrics
- `src/skinsmith/preview.py` — preview generation
- `src/skinsmith/pipeline.py` — agent pipeline orchestration
- `scripts/smoke_test.py` — end-to-end baseline run
- `tests/test_seamless.py` — seam-repair test
- `runs/smoke` — current generated evidence
- `third_party/downloads` — local-only external downloads; do not commit assets

## 7. Local environment

- GPU: NVIDIA RTX 4060 Laptop GPU, 8 GB VRAM
- Driver observed: 595.79
- Python: `E:\annaconda\python.exe`, Python 3.13.9
- PyTorch: 2.9.1+cu128; CUDA available
- Available: Transformers, OpenCV, Pillow, NumPy, Streamlit
- Not observed at initial audit: Diffusers, Trimesh, Gradio
- CS2 installation: `E:\Steam\steamapps\common\Counter-Strike Global Offensive`
- Blender was not found during the initial audit.

Official Valve packages identified for manual download:

- Weapon model geometry: `https://media.steampowered.com/apps/csgo/images/workshop/workshop/cs2_weapon_model_geometry.zip`
- Workbench materials: `https://media.steampowered.com/apps/csgo/workshop/workbench_materials.zip?v=103`

Network-restricted shell attempts failed, so download these manually when needed. Keep them out of version control.

## 8. Immediate next actions

1. Add quantitative multi-view metrics and include them in candidate selection.
2. Connect an image-generation backend that fits 8 GB VRAM; retain procedural generation as a deterministic baseline.
3. Add evaluator feedback and one controlled regeneration/refinement loop.
4. Validate a selected result in CS2 Workbench without making Workshop submission a deliverable.
5. Freeze features, run a style/ablation experiment matrix, and preserve all configurations and outputs.
6. Convert the evidence into report sections and an A0 poster.

## 9. Research evidence to preserve

For every formal run, save:

- input brief and theme;
- generator/model name and version;
- prompt and negative prompt;
- seed and all generation parameters;
- texture resolution;
- candidate images and previews;
- seam, style, complexity, and multi-view metrics;
- selection decision and evaluator feedback;
- runtime and VRAM observations;
- failures and manual interventions.

The final report should compare at least a baseline and the complete agent, and should distinguish visual appeal from technical validity.

## 10. Session-start rule

On every future session:

1. Read this file first.
2. Inspect `git status` and the latest run log.
3. Do not redo completed setup unless the evidence is missing.
4. Update this document whenever scope, architecture, milestones, or blockers materially change.
