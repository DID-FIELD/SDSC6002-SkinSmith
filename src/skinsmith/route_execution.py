from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from .agent_runtime import (
    AgentEventType,
    AgentToolContext,
    ArtworkCandidate,
    DesignContract,
)
from .evaluation import evaluate_candidate
from .game_asset_adapter import GameAssetAdapter
from .preview import TiledPreviewRenderer
from .refinement import decide_refinement
from .route_asset_generation import RouteImageJob, plan_route_image_jobs
from .route_b_composition import (
    compile_weapon_design_plan,
    has_master_artwork,
    load_generated_role_images,
)
from .seamless import make_seamless, seam_error
from .selection import (
    Constraint,
    Objective,
    constraint_first_pareto_select,
)
from .source_validation import SourceAssetValidator, SourceValidation
from .uv_asset import asset_uv_seam_error, build_uv_seam_pairs
from .uv_compositor import apply_uv_edge_safety
from .uv_region_composition import (
    compose_groups_in_uv_regions,
    has_explicit_composition_graph,
)
from .weapon_space import (
    bake_weapon_space_texture,
    geometry_map_diagnostics,
    render_weapon_space_canvases,
)


class ImageGenerationBackend(Protocol):
    @property
    def backend_id(self) -> str:
        ...

    def generate_image(self, prompt: str) -> Image.Image:
        ...


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_scope_guide(job: RouteImageJob, size: int = 1024) -> Image.Image | None:
    if job.composition_mode is None or job.composition_mode == "background":
        return None
    guide = Image.new("RGB", (size, size), (8, 10, 12))
    draw = ImageDraw.Draw(guide)
    fill = (224, 226, 220)
    if job.composition_mode == "spanning":
        draw.rounded_rectangle(
            (round(size * 0.04), round(size * 0.29), round(size * 0.96), round(size * 0.71)),
            radius=round(size * 0.18),
            fill=fill,
        )
        count = max(2, len(job.target_components))
        for index in range(1, count):
            x = round(size * (0.04 + 0.92 * index / count))
            draw.line(
                (x, round(size * 0.31), x, round(size * 0.69)),
                fill=(120, 126, 126),
                width=max(2, size // 256),
            )
    elif job.composition_mode == "grouped":
        count = max(2, len(job.target_components))
        slot_width = size * 0.82 / count
        for index in range(count):
            left = size * 0.09 + index * slot_width
            draw.rounded_rectangle(
                (
                    round(left),
                    round(size * 0.31),
                    round(left + slot_width * 0.72),
                    round(size * 0.69),
                ),
                radius=round(size * 0.10),
                fill=fill,
            )
    else:
        draw.rounded_rectangle(
            (round(size * 0.22), round(size * 0.22), round(size * 0.78), round(size * 0.78)),
            radius=round(size * 0.16),
            fill=fill,
        )
    return guide


def _apply_source_scope(image: Image.Image, guide: Image.Image) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8).copy()
    resized_guide = guide.resize(image.size, Image.Resampling.NEAREST)
    guide_rgb = np.asarray(resized_guide.convert("RGB"), dtype=np.uint8)
    allowed = guide_rgb.mean(axis=2) > 64.0
    rgb[~allowed] = np.array((8, 10, 12), dtype=np.uint8)
    return Image.fromarray(rgb, mode="RGB")


class RouteExecutionTool:
    """Execute a locked Agent design through real Route A and Route B modules."""

    def __init__(
        self,
        project_root: Path,
        image_backend: ImageGenerationBackend,
        *,
        asset_spec_path: Path,
        source_validator: SourceAssetValidator | None = None,
        bake_size: int = 512,
        edge_widths: tuple[int, ...] | None = None,
        asset_seam_maximum: float = 0.01,
        minimum_multiview_retention: float = 0.95,
        export_tga: bool = False,
        enable_refinement: bool = True,
        minimum_refinement_improvement: float = 0.01,
        candidate_preview_size: int = 256,
    ) -> None:
        self.project_root = Path(project_root)
        self.image_backend = image_backend
        self.asset_spec_path = Path(asset_spec_path)
        self.source_validator = source_validator or SourceAssetValidator()
        self.bake_size = int(bake_size)
        if self.bake_size < 64:
            raise ValueError("bake_size must be at least 64")
        if edge_widths is None:
            scale = self.bake_size / 2048.0
            edge_widths = tuple(
                sorted({0, *(max(1, round(width * scale)) for width in (4, 8, 12, 16, 24))})
            )
        if not edge_widths or min(edge_widths) < 0:
            raise ValueError("edge_widths must contain non-negative values")
        self.edge_widths = tuple(dict.fromkeys(int(value) for value in edge_widths))
        self.asset_seam_maximum = float(asset_seam_maximum)
        self.minimum_multiview_retention = float(minimum_multiview_retention)
        self.export_tga = bool(export_tga)
        self.enable_refinement = bool(enable_refinement)
        self.minimum_refinement_improvement = float(minimum_refinement_improvement)
        self.candidate_preview_size = int(candidate_preview_size)
        if self.candidate_preview_size < 64:
            raise ValueError("candidate_preview_size must be at least 64")
        if self.minimum_refinement_improvement <= 0:
            raise ValueError("minimum_refinement_improvement must be positive")

    def __call__(
        self,
        context: AgentToolContext,
        payload: DesignContract | dict[str, Any],
    ) -> dict[str, Any]:
        if isinstance(payload, DesignContract):
            contract = payload
            artwork_candidate = None
        elif isinstance(payload, dict):
            contract = payload.get("contract")
            artwork_candidate = payload.get("artwork_candidate")
            if not isinstance(contract, DesignContract):
                raise TypeError("execute_design payload requires a DesignContract")
            if not isinstance(artwork_candidate, ArtworkCandidate):
                raise TypeError(
                    "execute_design payload requires a selected ArtworkCandidate"
                )
        else:
            raise TypeError("execute_design requires a DesignContract or selection payload")
        self._verify_contract_asset(contract)
        started = time.perf_counter()
        execution_dir = context.output_dir / "execution"
        source_dir = execution_dir / "generated_sources"
        route_a_dir = execution_dir / "route_a"
        route_b_dir = execution_dir / "route_b"
        source_dir.mkdir(parents=True, exist_ok=True)
        route_a_dir.mkdir(parents=True, exist_ok=True)
        route_b_dir.mkdir(parents=True, exist_ok=True)

        bundle_path = context.output_dir / "planning" / "route_design_bundle.json"
        if not bundle_path.is_file():
            raise FileNotFoundError(
                "planning/route_design_bundle.json is required before execution"
            )
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        candidate_direction = self._candidate_direction(contract)
        jobs = plan_route_image_jobs(
            bundle,
            route="all",
            route_a_candidates=1,
            candidate_direction=candidate_direction,
        )
        selected_artwork_record: dict[str, Any] | None = None
        if artwork_candidate is None:
            generated_records, validations = self._generate_and_validate_sources(
                context,
                jobs,
                source_dir,
            )
        else:
            master_jobs = tuple(
                job
                for job in jobs
                if job.route == "B" and job.semantic_role == "master_artwork"
            )
            if len(master_jobs) != 1:
                raise ValueError(
                    "selected artwork execution requires exactly one master-artwork job"
                )
            non_master_jobs = tuple(job for job in jobs if job not in master_jobs)
            generated_records, validations = self._generate_and_validate_sources(
                context,
                non_master_jobs,
                source_dir,
            )
            selected_source = Path(artwork_candidate.source_path)
            if not selected_source.is_file():
                raise FileNotFoundError(
                    f"selected artwork source is missing: {selected_source}"
                )
            selected_image = Image.open(selected_source).convert("RGB")
            validation = self.source_validator.validate(
                "master_artwork",
                master_jobs[0].prompt,
                selected_image,
            )
            if not validation.passed:
                raise ValueError(
                    "selected artwork no longer passes its source contract: "
                    f"{validation.reasons}"
                )
            canonical = source_dir / master_jobs[0].output_name
            selected_image.save(canonical)
            validations["master_artwork"] = validation
            selected_artwork_record = {
                "candidate_id": artwork_candidate.candidate_id,
                "title": artwork_candidate.title,
                "variation": artwork_candidate.variation,
                "source": str(selected_source),
                "source_sha256": _sha256(selected_source),
                "canonical_output": str(canonical),
                "canonical_sha256": _sha256(canonical),
                "preview_paths": list(artwork_candidate.preview_paths),
                "preview_metrics": dict(artwork_candidate.metrics),
                "validation": validation.to_dict(),
                "mode": "human_selected_pre_mapped_master_artwork",
            }
            generated_records.append(selected_artwork_record)
        route_a = self._execute_route_a(
            context,
            source_dir / "route_a_candidate_01.png",
            route_a_dir,
        )
        route_b = self._execute_route_b(
            context,
            bundle,
            source_dir,
            route_b_dir,
        )
        if self.enable_refinement and route_b["constraints_passed"]:
            route_c = self._execute_route_c(
                context,
                bundle,
                source_dir,
                execution_dir / "route_c",
                route_b,
            )
        else:
            route_c = {
                "status": "not_run",
                "accepted": False,
                "reason": (
                    "Route B failed hard constraints"
                    if not route_b["constraints_passed"]
                    else "Route C is disabled"
                ),
            }
        if not route_b["constraints_passed"]:
            selected_route = "A"
            selected = route_a
        elif route_c.get("accepted"):
            selected_route = "C"
            selected = route_c
        else:
            selected_route = "B"
            selected = route_b
        decision = {
            "selected_route": selected_route,
            "reason": (
                "Route C passed hard constraints and improved the locked score by at least 0.01."
                if selected_route == "C"
                else (
                    "Route B passed hard constraints and Route C was disabled or rolled back."
                    if selected_route == "B"
                    else "Route B failed a hard technical gate; Route A is retained as the safe fallback."
                )
            ),
            "route_c": route_c.get("decision", route_c),
        }
        manifest = {
            "status": "complete_route_a_b_c",
            "backend_id": self.image_backend.backend_id,
            "design_contract": asdict(contract),
            "selected_artwork": selected_artwork_record,
            "bundle_path": str(bundle_path),
            "bundle_sha256": _sha256(bundle_path),
            "generated_sources": generated_records,
            "source_validations": {
                role: value.to_dict() for role, value in validations.items()
            },
            "route_a": route_a,
            "route_b": route_b,
            "route_c": route_c,
            "decision": decision,
            "runtime_seconds": time.perf_counter() - started,
        }
        manifest_path = execution_dir / "execution_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        context.memory.remember(
            f"{context.state.run_id}.route_execution",
            {
                "selected_route": selected_route,
                "route_a_total": route_a["score"]["total_score"],
                "route_b_total": route_b["score"]["total_score"],
                "route_b_constraints_passed": route_b["constraints_passed"],
            },
            [str(manifest_path)],
        )
        context.memory.save(context.output_dir / "memory_snapshot.json")
        context.emit(
            AgentEventType.ARTIFACT,
            f"Route A/B execution completed; selected Route {selected_route}.",
            tool="execute_design",
            data={"execution_manifest": str(manifest_path)},
        )
        return {
            "artifacts": {
                "execution_manifest": str(manifest_path),
                "selected_route": selected_route,
                "selected_texture_png": selected["texture_png"],
                "selected_texture_tga": selected.get("texture_tga"),
                "selected_previews": selected["previews"],
                "route_a": route_a["artifacts"],
                "route_b": route_b["artifacts"],
                "route_c": route_c.get("artifacts", {}),
            },
            "metrics": {
                "route_a": route_a["metrics"],
                "route_b": route_b["metrics"],
                "route_c": route_c.get("metrics", {}),
            },
            "decision": decision,
        }

    def generate_artwork_candidates(
        self,
        context: AgentToolContext,
        contract: DesignContract,
    ) -> tuple[ArtworkCandidate, ...]:
        """Generate distinct landscape master artworks and cheaply map every option."""

        self._verify_contract_asset(contract)
        bundle_path = context.output_dir / "planning" / "route_design_bundle.json"
        if not bundle_path.is_file():
            raise FileNotFoundError(
                "planning/route_design_bundle.json is required before artwork generation"
            )
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        jobs = plan_route_image_jobs(
            bundle,
            route="b",
            candidate_direction=self._candidate_direction(contract),
        )
        master_jobs = tuple(
            job for job in jobs if job.semantic_role == "master_artwork"
        )
        if len(master_jobs) != 1:
            raise ValueError(
                "artwork candidate generation requires exactly one master-artwork job"
            )
        base_job = master_jobs[0]
        variations = (
            (
                "Narrative Panorama",
                "environment-led panorama with several separated story clusters, small figures "
                "or creatures, symbolic objects, layered foreground/midground/background, and "
                "rhythmic atmospheric connections",
            ),
            (
                "Ornamental Tapestry",
                "symbol-led tapestry with repeated medium motifs, treasure-like details, patterned "
                "borders dissolved into the field, material ornament, and dense micro-symbols",
            ),
            (
                "Atmospheric World",
                "landscape-led world with mountains, water or terrain, architecture or natural "
                "structures, mist layers, celestial effects, and many small thematic discoveries",
            ),
            (
                "Kinetic Myth",
                "motion-led composition using several partial subject glimpses, directional clouds "
                "or energy, waves, sparks, fragments, and compact secondary events without a single "
                "full-width hero",
            ),
        )
        count = context.state.request.candidate_budget
        candidates_root = context.output_dir / "artwork_candidates"
        candidates_root.mkdir(parents=True, exist_ok=True)
        preview_tool = RouteExecutionTool(
            self.project_root,
            self.image_backend,
            asset_spec_path=self.asset_spec_path,
            source_validator=self.source_validator,
            bake_size=self.candidate_preview_size,
            edge_widths=(0, 1),
            asset_seam_maximum=self.asset_seam_maximum,
            minimum_multiview_retention=0.0,
            export_tga=False,
            enable_refinement=False,
            candidate_preview_size=self.candidate_preview_size,
        )
        results: list[ArtworkCandidate] = []
        for index, (title, variation) in enumerate(variations[:count], start=1):
            candidate_id = f"artwork_{index:02d}"
            candidate_dir = candidates_root / candidate_id
            source_dir = candidate_dir / "source"
            preview_dir = candidate_dir / "mapped_preview"
            source_dir.mkdir(parents=True, exist_ok=True)
            prompt = (
                f"{base_job.prompt}\nCANDIDATE VARIATION {index}: {variation}. "
                "Create a materially different composition from the other candidates while "
                "preserving the locked direction and palette. Include at least ten visually "
                "distinct clusters distributed across the landscape canvas. Keep the main "
                "theme readable through repeated medium/small appearances and related elements, "
                "not one giant central subject."
            )
            job = RouteImageJob(
                job_id=f"{base_job.job_id}__{candidate_id}",
                route=base_job.route,
                semantic_role=base_job.semantic_role,
                prompt=prompt,
                output_name=base_job.output_name,
                composition_group_id=base_job.composition_group_id,
                composition_mode=base_job.composition_mode,
                target_components=base_job.target_components,
            )
            _, validations = self._generate_and_validate_sources(
                context,
                (job,),
                source_dir,
            )
            source_path = source_dir / base_job.output_name
            preview = preview_tool._execute_route_b(
                context,
                bundle,
                source_dir,
                preview_dir,
            )
            candidate = ArtworkCandidate(
                candidate_id=candidate_id,
                title=title,
                variation=variation,
                source_path=str(source_path),
                prompt=prompt,
                preview_paths=tuple(preview["previews"]),
                validation=validations["master_artwork"].to_dict(),
                metrics={
                    **preview["metrics"],
                    "preview_bake_size": self.candidate_preview_size,
                },
            )
            results.append(candidate)
            (candidate_dir / "candidate_manifest.json").write_text(
                json.dumps(asdict(candidate), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        context.emit(
            AgentEventType.ARTIFACT,
            "Saved original artwork and mapped AK previews for every candidate.",
            tool="generate_artwork_candidates",
            data={
                "candidate_root": str(candidates_root),
                "candidate_ids": [item.candidate_id for item in results],
            },
        )
        return tuple(results)

    def retry_roles(
        self,
        context: AgentToolContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        contract = payload.get("contract")
        if not isinstance(contract, DesignContract):
            raise TypeError("retry_roles payload requires a DesignContract")
        self._verify_contract_asset(contract)
        roles = tuple(str(role) for role in payload.get("roles", ()))
        allowed = {
            "hero",
            "secondary",
            "connector",
            "background",
            "master_artwork",
        }
        if not roles or not set(roles) <= allowed:
            raise ValueError(
                "retry roles must use hero, secondary, connector, background, or master_artwork"
            )
        reasons = {
            str(key): str(value)
            for key, value in dict(payload.get("review_reasons", {})).items()
        }
        reuse_latest_roles = {
            str(role) for role in payload.get("reuse_latest_roles", ())
        }
        if not reuse_latest_roles <= set(roles):
            raise ValueError("reuse_latest_roles must be included in retry roles")
        bundle_path = context.output_dir / "planning" / "route_design_bundle.json"
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        all_jobs = plan_route_image_jobs(
            bundle,
            route="b",
            candidate_direction=self._candidate_direction(contract),
        )
        jobs = tuple(
            RouteImageJob(
                job_id=job.job_id,
                route=job.route,
                semantic_role=job.semantic_role,
                prompt=(
                    f"{job.prompt}\nPOST-MAPPING REVIEW CORRECTION: "
                    f"{reasons.get(
                        job.composition_group_id or '',
                        reasons.get(
                            job.semantic_role,
                            'the semantic role drifted from its locked contract',
                        ),
                    )}. "
                    "Correct only this rejected role and preserve the selected art direction. "
                    + (
                        "CONNECTOR ABSOLUTE FORM CONTRACT: output only thin floating orbital arcs, "
                        "constellation paths, or sparse patina filaments. ZERO gears, cogwheels, rods, "
                        "arms, linkages, instrument parts, mechanical assemblies, complete objects, "
                        "central devices, or solid masses."
                        if job.semantic_role == "connector"
                        else ""
                    )
                ),
                output_name=job.output_name,
                composition_group_id=job.composition_group_id,
                composition_mode=job.composition_mode,
                target_components=job.target_components,
            )
            for job in all_jobs
            if job.semantic_role in roles
        )
        source_dir = context.output_dir / "execution" / "generated_sources"
        reused_records: list[dict[str, Any]] = []
        for role in sorted(reuse_latest_roles):
            role_jobs = tuple(job for job in jobs if job.semantic_role == role)
            for job in role_jobs:
                output_name = Path(job.output_name)
                pattern = f"{output_name.stem}__attempt-*{output_name.suffix}"
                attempts = sorted(source_dir.glob(pattern))
                if not attempts:
                    raise FileNotFoundError(
                        f"no preserved attempt exists for {output_name.stem}"
                    )
                latest = attempts[-1]
                image = Image.open(latest).convert("RGB")
                validation = self.source_validator.validate(
                    role,
                    f"reuse preserved {output_name.stem} attempt",
                    image,
                )
                if not validation.passed:
                    raise ValueError(
                        f"latest preserved {output_name.stem} attempt still fails: "
                        f"{validation.reasons}"
                    )
                canonical = source_dir / job.output_name
                image.save(canonical)
                reused_records.append(
                    {
                        "semantic_role": role,
                        "composition_group_id": job.composition_group_id,
                        "source": str(latest),
                        "canonical_output": str(canonical),
                        "sha256": _sha256(canonical),
                        "validation": validation.to_dict(),
                        "mode": "reused_preserved_attempt_without_image_call",
                    }
                )
        jobs = tuple(job for job in jobs if job.semantic_role not in reuse_latest_roles)
        generated_records, validations = self._generate_and_validate_sources(
            context,
            jobs,
            source_dir,
        )
        revisions_root = context.output_dir / "execution" / "revisions"
        revision_index = len(
            [path for path in revisions_root.glob("revision_*") if path.is_dir()]
        ) + 1
        revision_dir = revisions_root / f"revision_{revision_index:02d}"
        revised_a = self._execute_route_a(
            context,
            source_dir / "route_a_candidate_01.png",
            revision_dir / "route_a",
        )
        revised_b = self._execute_route_b(
            context,
            bundle,
            source_dir,
            revision_dir / "route_b",
        )
        selected_route = "B" if revised_b["constraints_passed"] else "A"
        selected = revised_b if selected_route == "B" else revised_a
        decision = {
            "selected_route": selected_route,
            "reason": (
                "Existing Route A and the targeted Route-B roles were remapped under the "
                "locked asset contract; revised Route B passed hard constraints."
                if selected_route == "B"
                else "The revised Route B failed a hard gate; the remapped Route A is the fallback."
            ),
            "route_c": {
                "status": "not_rerun_after_post_mapping_semantic_revision",
                "previous_cycle": self._previous_route_c_decision(context.output_dir),
            },
        }
        revision_manifest = {
            "status": "complete_role_local_revision",
            "revision_index": revision_index,
            "retry_roles": roles,
            "review_reasons": reasons,
            "generated_records": generated_records,
            "reused_records": reused_records,
            "validations": {
                role: validation.to_dict()
                for role, validation in validations.items()
            },
            "route_a": revised_a,
            "route_b": revised_b,
            "decision": decision,
        }
        revision_manifest_path = revision_dir / "revision_manifest.json"
        revision_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        revision_manifest_path.write_text(
            json.dumps(revision_manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        context.memory.remember(
            f"{context.state.run_id}.revision_{revision_index:02d}",
            {
                "retry_roles": roles,
                "selected_route": selected_route,
                "route_b_constraints_passed": revised_b["constraints_passed"],
            },
            [str(revision_manifest_path)],
        )
        context.memory.save(context.output_dir / "memory_snapshot.json")
        context.emit(
            AgentEventType.ARTIFACT,
            f"Preserved role-local revision {revision_index:02d}.",
            tool="retry_roles",
            data={"revision_manifest": str(revision_manifest_path)},
        )
        return {
            "artifacts": {
                "revision_manifest": str(revision_manifest_path),
                "selected_route": selected_route,
                "selected_texture_png": selected["texture_png"],
                "selected_texture_tga": selected.get("texture_tga"),
                "selected_previews": selected["previews"],
                "route_a": revised_a["artifacts"],
                "route_b": revised_b["artifacts"],
            },
            "metrics": {
                "route_a": revised_a["metrics"],
                "route_b": revised_b["metrics"],
            },
            "decision": decision,
        }

    def _generate_and_validate_sources(
        self,
        context: AgentToolContext,
        jobs: tuple[RouteImageJob, ...],
        output_dir: Path,
    ) -> tuple[list[dict[str, Any]], dict[str, SourceValidation]]:
        log_path = output_dir / "generation_log.json"
        if log_path.is_file():
            previous_log = json.loads(log_path.read_text(encoding="utf-8"))
            records = list(previous_log.get("records", ()))
            validations_data = dict(previous_log.get("validations", {}))
        else:
            records = []
            validations_data = {}
        new_records: list[dict[str, Any]] = []
        validations: dict[str, SourceValidation] = {}
        for job in jobs:
            output_name = Path(job.output_name)
            canonical_path = output_dir / job.output_name
            validation_key = output_name.stem.removeprefix("route_b_")
            preserved_validation = validations_data.get(validation_key)
            if (
                canonical_path.is_file()
                and isinstance(preserved_validation, dict)
                and preserved_validation.get("passed") is True
            ):
                validation = SourceValidation(
                    role=str(preserved_validation["role"]),
                    passed=True,
                    technical_passed=bool(
                        preserved_validation.get("technical_passed", True)
                    ),
                    semantic_status=str(
                        preserved_validation.get("semantic_status", "")
                    ),
                    reasons=tuple(preserved_validation.get("reasons", ())),
                    metrics=dict(preserved_validation.get("metrics", {})),
                )
                validations[validation_key] = validation
                context.emit(
                    AgentEventType.OBSERVATION,
                    f"Reused preserved passing Route-B {job.semantic_role} source.",
                    tool="source_validator",
                    data={
                        "output": str(canonical_path),
                        "validation": validation.to_dict(),
                    },
                )
                continue
            guide = _source_scope_guide(job)
            guide_path: Path | None = None
            if guide is not None:
                guide_dir = output_dir / "source_scope_guides"
                guide_dir.mkdir(parents=True, exist_ok=True)
                guide_path = guide_dir / f"{output_name.stem}_scope.png"
                guide.save(guide_path)
            attempt = len(
                list(output_dir.glob(f"{output_name.stem}__attempt-*{output_name.suffix}"))
            )
            prompt = job.prompt
            while True:
                attempt += 1
                context.consume_image_call()
                context.emit(
                    AgentEventType.TOOL_CALL,
                    f"Generate Route {job.route} source {job.semantic_role}, attempt {attempt}.",
                    tool=self.image_backend.backend_id,
                    data={"job_id": job.job_id, "attempt": attempt},
                )
                if guide is not None:
                    scoped_prompt = (
                        f"{prompt}\nGENERATION SCOPE: Keep the complete requested subject "
                        "inside one centered wide horizontal band occupying approximately "
                        "90% of the canvas width and 40% of its height. Preserve a left-to-"
                        "right direction for spanning groups. Every pixel outside the subject "
                        "must be a perfectly uniform removable near-black background. Do not "
                        "draw any boundary, capsule, panel, plate, frame, material sample, or "
                        "scope-guide shape."
                    )
                    raw_image = self.image_backend.generate_image(scoped_prompt).convert("RGB")
                    raw_dir = output_dir / "raw_generated_sources"
                    raw_dir.mkdir(parents=True, exist_ok=True)
                    raw_path = raw_dir / (
                        f"{output_name.stem}__raw-attempt-{attempt:02d}{output_name.suffix}"
                    )
                    raw_image.save(raw_path)
                    image = _apply_source_scope(raw_image, guide)
                else:
                    raw_path = None
                    image = self.image_backend.generate_image(prompt).convert("RGB")
                attempt_path = output_dir / (
                    f"{output_name.stem}__attempt-{attempt:02d}{output_name.suffix}"
                )
                image.save(attempt_path)
                record = {
                    "job_id": job.job_id,
                    "route": job.route,
                    "semantic_role": job.semantic_role,
                    "composition_group_id": job.composition_group_id,
                    "attempt": attempt,
                    "prompt": prompt,
                    "output": str(attempt_path),
                    "sha256": _sha256(attempt_path),
                    "canonical_output": str(canonical_path),
                }
                if guide_path is not None:
                    record["source_scope_guide"] = str(guide_path)
                    record["source_scope_guide_sha256"] = _sha256(guide_path)
                    record["scope_application"] = "post_generation_hard_mask"
                if raw_path is not None:
                    record["raw_output"] = str(raw_path)
                    record["raw_output_sha256"] = _sha256(raw_path)
                trace = getattr(self.image_backend, "last_trace", None)
                if trace is not None and hasattr(trace, "to_dict"):
                    trace_path = output_dir / f"{job.job_id}__attempt-{attempt:02d}_trace.json"
                    trace_path.write_text(
                        json.dumps(trace.to_dict(), indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    record["trace"] = str(trace_path)
                records.append(record)
                new_records.append(record)
                if job.route == "A":
                    image.save(canonical_path)
                    break
                validation = self.source_validator.validate(
                    job.semantic_role,
                    prompt,
                    image,
                )
                semantic_reviewer = self.source_validator.semantic_reviewer
                semantic_trace = getattr(semantic_reviewer, "last_trace", None)
                if semantic_trace is not None and hasattr(semantic_trace, "to_dict"):
                    semantic_trace_path = output_dir / (
                        f"{job.job_id}__attempt-{attempt:02d}_semantic_review_trace.json"
                    )
                    semantic_trace_path.write_text(
                        json.dumps(
                            semantic_trace.to_dict(),
                            indent=2,
                            ensure_ascii=False,
                        ),
                        encoding="utf-8",
                    )
                    record["semantic_review_trace"] = str(semantic_trace_path)
                validations[validation_key] = validation
                validations_data[validation_key] = validation.to_dict()
                validation_path = output_dir / f"{output_name.stem}_validation.json"
                validation_path.write_text(
                    json.dumps(validation.to_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                context.emit(
                    AgentEventType.OBSERVATION,
                    (
                        f"Route-B {job.semantic_role} source passed its gate."
                        if validation.passed
                        else f"Route-B {job.semantic_role} source failed its gate."
                    ),
                    tool="source_validator",
                    data=validation.to_dict(),
                )
                if validation.passed:
                    image.save(canonical_path)
                    break
                context.consume_role_retry()
                prompt = (
                    f"{job.prompt}\nRETRY CORRECTION: Fix only these source-gate failures: "
                    f"{'; '.join(validation.reasons)}. Preserve the locked art direction and "
                    f"the {job.semantic_role} semantic role."
                )
        generation_log = {
            "backend_id": self.image_backend.backend_id,
            "records": records,
            "validations": validations_data,
        }
        log_path.write_text(
            json.dumps(generation_log, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return new_records, validations

    def _execute_route_a(
        self,
        context: AgentToolContext,
        source_path: Path,
        output_dir: Path,
    ) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        adapter = self._adapter()
        verified_hashes = adapter.verify()
        mesh = adapter.load_mesh()
        seam_pairs = build_uv_seam_pairs(mesh)
        source = Image.open(source_path).convert("RGB")
        repaired = make_seamless(source)
        raw_path = output_dir / "route_a_raw.png"
        texture_path = output_dir / "route_a_seamless.png"
        source.save(raw_path)
        repaired.save(texture_path)
        TiledPreviewRenderer().render(repaired, output_dir, "route_a_seamless")
        previews = adapter.renderer().render(
            repaired,
            output_dir,
            "route_a_seamless_ak47",
        )
        score = evaluate_candidate("route_a", repaired, previews)
        asset_seam = asset_uv_seam_error(
            repaired,
            mesh,
            seam_pairs,
            uv_address_mode=adapter.spec.uv_address_mode,
        )
        texture_tga = self._export_tga(
            repaired,
            output_dir,
            "route_a",
            adapter,
        )
        result = {
            "texture_png": str(texture_path),
            "texture_tga": texture_tga,
            "previews": [str(path) for path in previews],
            "score": score.to_dict(),
            "metrics": {
                "square_seam_raw": seam_error(source),
                "square_seam_repaired": seam_error(repaired),
                "asset_seam": asset_seam,
                "multi_view_score": score.multi_view.total_score,
                "total_score": score.total_score,
            },
            "artifacts": {
                "source": str(source_path),
                "texture_png": str(texture_path),
                "texture_tga": texture_tga,
                "previews": [str(path) for path in previews],
            },
            "asset_verification": verified_hashes,
            "asset_contract": adapter.to_log_dict(),
        }
        (output_dir / "route_a_log.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        context.emit(
            AgentEventType.OBSERVATION,
            "Route A was repaired, mapped to the official asset, and evaluated.",
            tool="route_a_executor",
            data=result["metrics"],
        )
        return result

    def _execute_route_c(
        self,
        context: AgentToolContext,
        bundle: dict[str, Any],
        source_dir: Path,
        output_dir: Path,
        route_b: dict[str, Any],
    ) -> dict[str, Any]:
        context.consume_refinement_round()
        output_dir.mkdir(parents=True, exist_ok=True)
        adapter = self._adapter()
        adapter.verify()
        mesh = adapter.load_mesh()
        maps = adapter.bake_geometry_maps(mesh, self.bake_size)
        seam_pairs = build_uv_seam_pairs(mesh)
        plan = compile_weapon_design_plan(bundle)
        content_images, _ = load_generated_role_images(source_dir, bundle)
        round_0_canvases = render_weapon_space_canvases(plan, content_images)
        coverage = Image.fromarray(
            maps.valid_mask.astype(np.uint8) * 255,
            mode="L",
        )
        selected_width = int(route_b["metrics"]["selected_edge_width"])
        renderer = adapter.renderer()
        round_0_score = float(route_b["score"]["total_score"])
        round_0_multiview = float(route_b["metrics"]["multi_view_score"])
        records: dict[str, dict[str, Any]] = {}
        selection_metrics: dict[str, dict[str, float]] = {}
        candidate_images: dict[str, Image.Image] = {}
        candidate_previews: dict[str, list[Path]] = {}
        for intensity in (1, 2):
            candidate_id = f"route_c_intensity_{intensity}"
            canvases: dict[str, Image.Image] = {}
            locality: dict[str, Any] = {}
            for surface, canvas in round_0_canvases.items():
                center = (
                    (plan.focal_center[0], 1.0 - plan.focal_center[1])
                    if surface in {"left", "right"}
                    else (plan.focal_center[0], 0.5)
                )
                corrected_canvas, local = _apply_weapon_space_local_correction(
                    canvas,
                    center=center,
                    radius=plan.focal_radius,
                    intensity=intensity,
                )
                canvases[surface] = corrected_canvas
                locality[surface] = local
                corrected_canvas.save(
                    output_dir / f"{candidate_id}_weapon_space_{surface}.png"
                )
            raw = bake_weapon_space_texture(
                maps,
                canvases,
                plan.palette[0],
                projection_blend_power=plan.projection_blend_power,
            )
            corrected, edge_map = apply_uv_edge_safety(
                raw,
                {"official_uv_coverage": coverage},
                base_color=plan.palette[0],
                edge_safe_pixels=selected_width,
            )
            texture_path = output_dir / f"{candidate_id}.png"
            corrected.save(texture_path)
            edge_map.save(output_dir / f"{candidate_id}_edge_map.png")
            previews = renderer.render(corrected, output_dir, candidate_id)
            score = evaluate_candidate(candidate_id, corrected, previews)
            seam = asset_uv_seam_error(
                corrected,
                mesh,
                seam_pairs,
                uv_address_mode=adapter.spec.uv_address_mode,
            )
            retention = (
                score.multi_view.total_score / round_0_multiview
                if round_0_multiview > 1e-12
                else 0.0
            )
            selection_metrics[candidate_id] = {
                "asset_seam_error": float(seam["total_error"]),
                "multi_view_score": float(score.multi_view.total_score),
                "multi_view_retention": float(retention),
                "total_score": float(score.total_score),
            }
            records[candidate_id] = {
                "intensity": intensity,
                "texture_png": str(texture_path),
                "previews": [str(path) for path in previews],
                "score": score.to_dict(),
                "asset_seam": seam,
                "multi_view_retention": retention,
                "locality": locality,
            }
            candidate_images[candidate_id] = corrected
            candidate_previews[candidate_id] = previews
        selection = constraint_first_pareto_select(
            selection_metrics,
            constraints=(
                Constraint(
                    "asset_seam_error",
                    maximum=self.asset_seam_maximum,
                ),
                Constraint(
                    "multi_view_retention",
                    minimum=self.minimum_multiview_retention,
                ),
            ),
            objectives=(
                Objective("total_score", maximize=True),
                Objective("asset_seam_error", maximize=False),
            ),
        )
        best_id = selection.selected_id
        best = records[best_id]
        score_decision = decide_refinement(
            round_0_score,
            float(best["score"]["total_score"]),
            self.minimum_refinement_improvement,
        )
        constraints_passed = best_id in selection.feasible_ids
        accepted = constraints_passed and score_decision.accepted
        if accepted:
            selected_image = candidate_images[best_id]
            selected_previews = candidate_previews[best_id]
            selected_score = best["score"]
            selected_seam = best["asset_seam"]
        else:
            selected_image = Image.open(route_b["texture_png"]).convert("RGB")
            selected_previews = [Path(path) for path in route_b["previews"]]
            selected_score = route_b["score"]
            selected_seam = route_b["metrics"]["asset_seam"]
        selected_path = output_dir / "route_c_selected.png"
        selected_image.save(selected_path)
        selected_tga = self._export_tga(
            selected_image,
            output_dir,
            "route_c",
            adapter,
        )
        decision = {
            **score_decision.to_dict(),
            "accepted": accepted,
            "constraints_passed": constraints_passed,
            "selected_candidate": best_id,
            "reason": (
                score_decision.reason
                if constraints_passed
                else "Round 1 failed the asset-seam or multiview-retention hard gate"
            ),
        }
        result = {
            "status": "accepted" if accepted else "rolled_back",
            "accepted": accepted,
            "texture_png": str(selected_path),
            "texture_tga": selected_tga,
            "previews": [str(path) for path in selected_previews],
            "score": selected_score,
            "metrics": {
                "asset_seam": selected_seam,
                "multi_view_score": selected_score["multi_view"]["total_score"],
                "total_score": selected_score["total_score"],
                "accepted": accepted,
            },
            "artifacts": {
                "texture_png": str(selected_path),
                "texture_tga": selected_tga,
                "previews": [str(path) for path in selected_previews],
            },
            "diagnosis": {
                "action": "reduce_receiver_focal_detail_in_weapon_space",
                "target": "receiver_focal_region",
                "reason": "bounded correction reuses the locked receiver focal zone without a new image call",
            },
            "candidates": records,
            "selection": selection.to_dict(),
            "decision": decision,
        }
        (output_dir / "route_c_log.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        context.emit(
            AgentEventType.DECISION,
            "Route C accepted its local correction." if accepted else "Route C rolled back to Route B.",
            tool="route_c_executor",
            data=decision,
        )
        return result

    def _execute_route_b(
        self,
        context: AgentToolContext,
        bundle: dict[str, Any],
        source_dir: Path,
        output_dir: Path,
    ) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        adapter = self._adapter()
        verified_hashes = adapter.verify()
        mesh = adapter.load_mesh()
        maps = adapter.bake_geometry_maps(mesh, self.bake_size)
        plan = compile_weapon_design_plan(bundle)
        content_images, provenance = load_generated_role_images(source_dir, bundle)
        canvases = render_weapon_space_canvases(plan, content_images)
        if has_explicit_composition_graph(bundle):
            raw = compose_groups_in_uv_regions(
                bundle,
                mesh,
                maps,
                adapter.spec,
                content_images,
                base_color=plan.palette[0],
                diagnostic_dir=output_dir / "uv_group_regions",
            )
            composition_mode = "mesh_semantic_uv_region_conditioned"
        else:
            raw = bake_weapon_space_texture(
                maps,
                canvases,
                plan.palette[0],
                projection_blend_power=plan.projection_blend_power,
            )
            composition_mode = (
                "continuous_master_artwork_obj_uv_bake"
                if has_master_artwork(bundle)
                else "continuous_weapon_space_legacy_role_fallback"
            )
        for name, image in canvases.items():
            image.save(output_dir / f"weapon_space_{name}.png")
        for name, image in geometry_map_diagnostics(maps).items():
            image.save(output_dir / f"{name}.png")
        raw_path = output_dir / "uv_baked_raw.png"
        raw.save(raw_path)
        renderer = adapter.renderer()
        seam_pairs = build_uv_seam_pairs(mesh)
        raw_previews = renderer.render(raw, output_dir, "route_b_width_0")
        raw_score = evaluate_candidate("route_b_width_0", raw, raw_previews)
        raw_seam = asset_uv_seam_error(
            raw,
            mesh,
            seam_pairs,
            uv_address_mode=adapter.spec.uv_address_mode,
        )
        coverage = Image.fromarray(
            maps.valid_mask.astype(np.uint8) * 255,
            mode="L",
        )
        candidates: dict[str, dict[str, float]] = {}
        records: dict[str, dict[str, Any]] = {}
        width_images: dict[str, Image.Image] = {}
        width_previews: dict[str, list[Path]] = {}
        for width in self.edge_widths:
            candidate_id = f"width_{width}"
            if width == 0:
                corrected = raw
                previews = raw_previews
                score = raw_score
                seam = raw_seam
            else:
                corrected, edge_map = apply_uv_edge_safety(
                    raw,
                    {"official_uv_coverage": coverage},
                    base_color=plan.palette[0],
                    edge_safe_pixels=width,
                )
                edge_map.save(output_dir / f"{candidate_id}_edge_map.png")
                previews = renderer.render(corrected, output_dir, f"route_b_{candidate_id}")
                score = evaluate_candidate(candidate_id, corrected, previews)
                seam = asset_uv_seam_error(
                    corrected,
                    mesh,
                    seam_pairs,
                    uv_address_mode=adapter.spec.uv_address_mode,
                )
            texture_path = output_dir / f"{candidate_id}.png"
            corrected.save(texture_path)
            retention = (
                score.multi_view.total_score / raw_score.multi_view.total_score
                if raw_score.multi_view.total_score > 1e-12
                else 0.0
            )
            candidates[candidate_id] = {
                "asset_seam_error": float(seam["total_error"]),
                "multi_view_score": float(score.multi_view.total_score),
                "multi_view_retention": float(retention),
            }
            records[candidate_id] = {
                "width": width,
                "texture_png": str(texture_path),
                "previews": [str(path) for path in previews],
                "asset_seam": seam,
                "score": score.to_dict(),
                "multi_view_retention": retention,
            }
            width_images[candidate_id] = corrected
            width_previews[candidate_id] = previews
        selection = constraint_first_pareto_select(
            candidates,
            constraints=(
                Constraint(
                    "asset_seam_error",
                    maximum=self.asset_seam_maximum,
                ),
                Constraint(
                    "multi_view_retention",
                    minimum=self.minimum_multiview_retention,
                ),
            ),
            objectives=(
                Objective("multi_view_score", maximize=True),
                Objective("asset_seam_error", maximize=False),
            ),
        )
        selected_id = selection.selected_id
        selected_record = records[selected_id]
        selected_image = width_images[selected_id]
        selected_path = output_dir / "route_b_selected.png"
        selected_image.save(selected_path)
        selected_tga = self._export_tga(
            selected_image,
            output_dir,
            "route_b",
            adapter,
        )
        constraints_passed = selected_id in selection.feasible_ids
        result = {
            "texture_png": str(selected_path),
            "texture_tga": selected_tga,
            "previews": [str(path) for path in width_previews[selected_id]],
            "score": selected_record["score"],
            "constraints_passed": constraints_passed,
            "metrics": {
                "selected_edge_width": selected_record["width"],
                "asset_seam": selected_record["asset_seam"],
                "multi_view_score": selected_record["score"]["multi_view"]["total_score"],
                "multi_view_retention": selected_record["multi_view_retention"],
                "total_score": selected_record["score"]["total_score"],
                "constraints_passed": constraints_passed,
            },
            "artifacts": {
                "raw_texture": str(raw_path),
                "texture_png": str(selected_path),
                "texture_tga": selected_tga,
                "previews": [str(path) for path in width_previews[selected_id]],
                "weapon_space_canvases": {
                    name: str(output_dir / f"weapon_space_{name}.png")
                    for name in canvases
                },
            },
            "asset_verification": verified_hashes,
            "asset_contract": adapter.to_log_dict(),
            "geometry_maps": maps.statistics(),
            "content_provenance": provenance,
            "composition_mode": composition_mode,
            "edge_candidates": records,
            "selection": selection.to_dict(),
        }
        (output_dir / "route_b_log.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        context.emit(
            AgentEventType.OBSERVATION,
            "Route B was composed in weapon space, baked to official UV, swept, and selected.",
            tool="route_b_executor",
            data=result["metrics"],
        )
        return result

    def _adapter(self) -> GameAssetAdapter:
        path = self.asset_spec_path
        if not path.is_absolute():
            path = self.project_root / path
        return GameAssetAdapter.load(path, self.project_root)

    def _verify_contract_asset(self, contract: DesignContract) -> None:
        adapter = self._adapter()
        if contract.asset_id != adapter.spec.asset_id:
            raise ValueError(
                "design contract asset does not match execution AssetSpec: "
                f"{contract.asset_id!r} != {adapter.spec.asset_id!r}"
            )

    @staticmethod
    def _previous_route_c_decision(output_dir: Path) -> dict[str, Any] | None:
        manifest_path = output_dir / "execution" / "execution_manifest.json"
        if not manifest_path.is_file():
            return None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return manifest.get("route_c", {}).get("decision")

    @staticmethod
    def _candidate_direction(contract: DesignContract) -> dict[str, Any]:
        direction = contract.selected_direction
        return {
            "direction_id": direction.direction_id,
            "title": direction.title,
            "concept": direction.concept,
            "motifs": list(direction.motifs or (direction.concept,)),
            "world_elements": list(direction.world_elements),
            "route_a_emphasis": direction.route_a_logic,
            "route_b_emphasis": direction.route_b_logic,
        }

    def _export_tga(
        self,
        image: Image.Image,
        output_dir: Path,
        route: str,
        adapter: GameAssetAdapter,
    ) -> str | None:
        if not self.export_tga:
            return None
        if self.bake_size != adapter.spec.texture_size and route in {"route_b", "route_c"}:
            raise ValueError(
                "formal Route-B TGA export requires bake_size to equal the asset texture size"
            )
        profiles = json.loads(
            (self.project_root / "config" / "workbench_finish_profiles.json").read_text(
                encoding="utf-8"
            )
        )
        profile_key = {
            "route_a": "A",
            "route_b": "B",
            "route_c": "C",
        }[route]
        suffix = profiles["routes"][profile_key]["filename_suffix"]
        target = image.convert("RGB")
        if target.size != (adapter.spec.texture_size, adapter.spec.texture_size):
            target = target.resize(
                (adapter.spec.texture_size, adapter.spec.texture_size),
                Image.Resampling.LANCZOS,
            )
        path = output_dir / f"selected{suffix}.tga"
        target.save(path)
        return str(path)


def _apply_weapon_space_local_correction(
    image: Image.Image,
    *,
    center: tuple[float, float],
    radius: tuple[float, float],
    intensity: int,
) -> tuple[Image.Image, dict[str, float | int]]:
    if intensity not in (1, 2):
        raise ValueError("Route-C intensity must be 1 or 2")
    source = image.convert("RGB")
    width, height = source.size
    mask = Image.new("L", source.size, 0)
    draw = ImageDraw.Draw(mask)
    cx = center[0] * width
    cy = center[1] * height
    rx = max(4.0, radius[0] * width * 1.35)
    ry = max(4.0, radius[1] * height * 1.35)
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(2.0, min(width, height) * 0.012)))
    softened = source.filter(ImageFilter.GaussianBlur(radius=1.5 * intensity))
    softened = ImageEnhance.Contrast(softened).enhance(1.0 - 0.08 * intensity)
    corrected = Image.composite(softened, source, mask)
    before = np.asarray(source, dtype=np.int16)
    after = np.asarray(corrected, dtype=np.int16)
    changed = np.max(np.abs(after - before), axis=2) > 1
    allowed = np.asarray(mask, dtype=np.uint8) > 0
    outside = int(np.count_nonzero(changed & ~allowed))
    changed_count = int(np.count_nonzero(changed))
    return corrected, {
        "changed_pixel_count": changed_count,
        "changed_pixel_fraction": changed_count / changed.size,
        "changed_outside_target_halo_count": outside,
        "changed_outside_target_halo_fraction_of_changes": outside
        / max(changed_count, 1),
    }
