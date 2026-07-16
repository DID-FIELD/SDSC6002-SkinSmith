from __future__ import annotations

import csv
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from .asset_spec import AssetSpec
from .component_feedback import (
    ComponentDiagnosis,
    diagnose_component_detail,
    measure_component_views,
    render_component_visibility,
)
from .evaluation import evaluate_candidate
from .generator import ProceduralTextureGenerator, TextureGenerator
from .game_asset_adapter import GameAssetAdapter
from .obj_renderer import ObjMultiViewRenderer, load_obj
from .refinement import decide_refinement
from .route_b_composition import ROLE_LAYER_IDS, compile_weapon_design_plan
from .seamless import make_seamless, seam_error
from .selection import Constraint, Objective, constraint_first_pareto_select
from .spec import DesignSpec
from .uv_asset import asset_uv_seam_error, build_uv_seam_pairs
from .uv_compositor import apply_uv_edge_safety
from .weapon_space import (
    CanonicalWeaponFrame,
    bake_uv_geometry_maps,
    bake_weapon_space_texture,
    render_weapon_space_canvases,
)


class ABCAblationRunner:
    """Run fair A/B/C experiments from one shared candidate source pool."""

    def __init__(
        self,
        project_root: Path,
        generator: TextureGenerator | None = None,
        route_bundle_path: Path | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.generator = generator or ProceduralTextureGenerator()
        self.route_config = json.loads(
            (self.project_root / "config" / "route_b.json").read_text(encoding="utf-8")
        )
        self.refinement_config = self.route_config["route_c_local_refinement"]
        self.asset_adapter = GameAssetAdapter.load(
            self.project_root / self.route_config["asset_spec"], self.project_root
        )
        self.asset_adapter.verify()
        self.asset_spec = self.asset_adapter.spec
        self.renderer = self.asset_adapter.renderer()
        self.mesh = self.asset_adapter.load_mesh()
        self.seam_pairs = build_uv_seam_pairs(self.mesh)
        bundle_path = route_bundle_path or (
            self.project_root
            / "runs"
            / "theme_compilation_marble_dynamic_style"
            / "route_design_bundle.json"
        )
        self.route_bundle_path = Path(bundle_path)
        self.route_bundle = json.loads(self.route_bundle_path.read_text(encoding="utf-8"))
        self.weapon_plan = compile_weapon_design_plan(self.route_bundle)
        self.canonical_frame = self.asset_adapter.canonical_frame(self.mesh)
        self.uv_maps = self.asset_adapter.bake_geometry_maps(
            self.mesh, self.asset_spec.texture_size
        )
        mask_dir = self.project_root / "runs" / "route_b_asset_prep"
        region_names = [region.name for region in self.asset_spec.semantic_regions] + [
            self.asset_spec.default_region.name
        ]
        self.masks = {
            name: Image.open(mask_dir / f"mask_{name}.png").convert("L")
            for name in region_names
        }
        self.detail_targets = {
            name: float(value)
            for name, value in self.refinement_config["detail_targets"].items()
        }

    def run(self, spec: DesignSpec, output_dir: Path) -> dict[str, Any]:
        started = time.perf_counter()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        source_dir = output_dir / "shared_sources"
        source_dir.mkdir(exist_ok=True)
        visibility = render_component_visibility(
            self.renderer,
            {name: self.masks[name] for name in self.detail_targets},
            output_dir / "component_visibility",
        )
        base_color = tuple(int(value) for value in self.weapon_plan.palette[0])

        route_a: list[dict] = []
        route_b: list[dict] = []
        shared_sources: list[dict] = []
        for index in range(spec.candidate_count):
            candidate_id = f"candidate_{index + 1:02d}"
            seed = spec.seed + index
            source = self.generator.generate(spec, seed).convert("RGB")
            source_path = source_dir / f"{candidate_id}.png"
            source.save(source_path)
            source_digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
            shared_sources.append(
                {
                    "candidate_id": candidate_id,
                    "seed": seed,
                    "path": str(source_path),
                    "sha256": source_digest,
                }
            )

            route_a_texture = make_seamless(source).resize(
                (self.asset_spec.texture_size, self.asset_spec.texture_size),
                Image.Resampling.LANCZOS,
            )
            route_a.append(
                self._evaluate(
                    "A",
                    candidate_id,
                    seed,
                    source_path,
                    route_a_texture,
                    output_dir / "route_a" / candidate_id,
                    visibility,
                )
            )

            role_sources, role_records = self._generate_route_b_sources(
                spec, seed, output_dir / "route_b" / candidate_id / "semantic_sources"
            )
            layer_images = {
                layer_id: role_sources[role].copy()
                for role, layer_ids in ROLE_LAYER_IDS.items()
                for layer_id in layer_ids
            }
            canvases = render_weapon_space_canvases(self.weapon_plan, layer_images)
            before_correction = bake_weapon_space_texture(
                self.uv_maps,
                canvases,
                base_color,
                projection_blend_power=self.weapon_plan.projection_blend_power,
            )
            corrected, edge_map = apply_uv_edge_safety(
                before_correction,
                {"uv_coverage": Image.fromarray(self.uv_maps.valid_mask.astype(np.uint8) * 255)},
                base_color=base_color,
                edge_safe_pixels=int(self.route_config["selected_edge_safe_pixels"]),
            )
            route_b_record = self._evaluate(
                "B",
                candidate_id,
                seed,
                source_path,
                corrected,
                output_dir / "route_b" / candidate_id,
                visibility,
            )
            route_b_record["semantic_sources"] = role_records
            route_b_record["weapon_space_plan_id"] = self.weapon_plan.plan_id
            route_b_record["uv_geometry_map_statistics"] = self.uv_maps.statistics()
            route_b_record["before_asset_seam"] = asset_uv_seam_error(
                before_correction, self.mesh, self.seam_pairs
            )
            route_b_record["before_asset_seam_texture"] = str(
                output_dir / "route_b" / candidate_id / "texture_before_asset_seam.png"
            )
            before_correction.save(
                route_b_record["before_asset_seam_texture"]
            )
            edge_map.save(output_dir / "route_b" / candidate_id / "uv_edge_safety_map.png")
            for surface, canvas in canvases.items():
                canvas.save(output_dir / "route_b" / candidate_id / f"weapon_space_{surface}.png")
            route_b.append(route_b_record)

        route_a.sort(key=lambda item: item["standard_score"]["total_score"], reverse=True)
        route_a_selected = route_a[0]["candidate_id"]
        route_b_metrics = {
            item["candidate_id"]: {
                "asset_seam_error": item["asset_seam"]["total_error"],
                "multi_view_score": item["standard_score"]["multi_view"]["total_score"],
                "agent_score": item["agent_score"],
            }
            for item in route_b
        }
        route_b_selection = constraint_first_pareto_select(
            route_b_metrics,
            (
                Constraint(
                    "asset_seam_error",
                    maximum=float(self.refinement_config["asset_seam_error_maximum"]),
                ),
            ),
            (
                Objective("agent_score", maximize=True),
                Objective("asset_seam_error", maximize=False),
            ),
        )
        route_b_selected = next(
            item for item in route_b if item["candidate_id"] == route_b_selection.selected_id
        )
        route_c_runs: list[dict[str, Any]] = []
        route_c_outcomes: list[dict[str, Any]] = []
        for route_b_record in route_b:
            candidate_id = route_b_record["candidate_id"]
            route_c_run = self._run_route_c(
                spec,
                route_b_record,
                visibility,
                base_color,
                output_dir / "route_c" / candidate_id,
            )
            route_c_runs.append(route_c_run)
            outcome = dict(route_c_run["selected_record"])
            outcome["candidate_id"] = candidate_id
            outcome["route_c_selected_round"] = route_c_run["refinement_decision"][
                "selected_round"
            ]
            route_c_outcomes.append(outcome)
        route_c_metrics = {
            item["candidate_id"]: {
                "asset_seam_error": item["asset_seam"]["total_error"],
                "multi_view_score": item["standard_score"]["multi_view"]["total_score"],
                "agent_score": item["agent_score"],
            }
            for item in route_c_outcomes
        }
        route_c_selection = constraint_first_pareto_select(
            route_c_metrics,
            (
                Constraint(
                    "asset_seam_error",
                    maximum=float(self.refinement_config["asset_seam_error_maximum"]),
                ),
            ),
            (
                Objective("agent_score", maximize=True),
                Objective("asset_seam_error", maximize=False),
            ),
        )
        route_c_selected = next(
            item
            for item in route_c_outcomes
            if item["candidate_id"] == route_c_selection.selected_id
        )

        paired = paired_route_summary(route_a, route_b, bootstrap_seed=spec.seed)
        paired_c = paired_route_summary(
            route_b, route_c_outcomes, bootstrap_seed=spec.seed + 1
        )
        selected_ids = {
            "A": route_a_selected,
            "B": route_b_selected["candidate_id"],
            "C": route_c_selected["candidate_id"],
        }
        route_c = {
            "method": "Each B Round 0 receives the same bounded two-candidate render-conditioned local action and rollback gate",
            "selection": route_c_selection.to_dict(),
            "selected_id": route_c_selected["candidate_id"],
            "selected_round": route_c_selected["route_c_selected_round"],
            "per_candidate": route_c_runs,
            "outcomes": route_c_outcomes,
            "paired_c_minus_b": paired_c,
        }
        result = {
            "stage": "abc_ablation_true_weapon_space",
            "status": "pass",
            "design_spec": spec.to_dict(),
            "fairness_controls": {
                "shared_theme": spec.theme_name,
                "shared_palette": list(spec.palette),
                "shared_base_seed": spec.seed,
                "shared_candidate_count": spec.candidate_count,
                "shared_generation_resolution": spec.size,
                "shared_output_resolution": self.asset_spec.texture_size,
                "shared_asset_id": self.asset_spec.asset_id,
                "shared_mesh_sha256": self.asset_spec.mesh_sha256,
                "shared_camera_views": list(self.asset_spec.camera_views),
                "semantic_model_used": False,
                "diffusion_used": not isinstance(self.generator, ProceduralTextureGenerator),
                "route_specific_generation_logic": {
                    "A": "one dense crop-tolerant pattern source per candidate",
                    "B": "four distinct semantic role sources per candidate followed by continuous weapon-space composition",
                },
                "same_source_image_required": False,
            },
            "generator": self.generator.metadata(),
            "shared_sources": shared_sources,
            "route_a": {
                "method": "generic periodic square texture + Custom Paint",
                "selection": "maximum historical texture/multi-view weighted score",
                "selected_id": route_a_selected,
                "candidates": route_a,
            },
            "route_b": {
                "method": "four semantic sources + continuous weapon-space composition + position/normal-map UV bake + 8 px asset seam correction",
                "route_bundle": str(self.route_bundle_path),
                "weapon_space_plan": self.weapon_plan.to_dict(),
                "selection": route_b_selection.to_dict(),
                "selected_id": route_b_selected["candidate_id"],
                "candidates": route_b,
            },
            "route_c": route_c,
            "paired_b_minus_a": paired,
            "selected_ids": selected_ids,
            "runtime_seconds": time.perf_counter() - started,
        }
        (output_dir / "ablation_log.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self._write_summary(
            output_dir / "ablation_summary.csv",
            route_a,
            route_b,
            route_c,
            selected_ids,
        )
        return result

    def _evaluate(
        self,
        route: str,
        candidate_id: str,
        seed: int,
        source_path: Path,
        texture: Image.Image,
        candidate_dir: Path,
        visibility: Mapping[str, list[Path]],
    ) -> dict[str, Any]:
        candidate_dir.mkdir(parents=True, exist_ok=True)
        texture_path = candidate_dir / "texture.png"
        texture.save(texture_path)
        previews = self.renderer.render(texture, candidate_dir, f"route_{route.lower()}_{candidate_id}")
        standard = evaluate_candidate(candidate_id, texture, previews)
        per_view, components, balance = measure_component_views(
            previews, visibility, self.detail_targets
        )
        asset_seam = asset_uv_seam_error(texture, self.mesh, self.seam_pairs)
        agent_score = _agent_score(
            standard.texture_score,
            standard.multi_view.total_score,
            balance,
            self.refinement_config["agent_score_weights"],
        )
        return {
            "route": route,
            "candidate_id": candidate_id,
            "seed": seed,
            "shared_source": str(source_path),
            "texture": str(texture_path),
            "previews": [str(path) for path in previews],
            "periodic_seam_error": seam_error(texture),
            "asset_seam": asset_seam,
            "standard_score": asdict(standard),
            "component_detail_balance": balance,
            "agent_score": agent_score,
            "component_metrics": [record.to_dict() for record in components],
            "component_view_metrics": [record.to_dict() for record in per_view],
        }

    def _generate_route_b_sources(
        self,
        spec: DesignSpec,
        candidate_seed: int,
        output_dir: Path,
    ) -> tuple[dict[str, Image.Image], list[dict[str, Any]]]:
        """Generate distinct role inputs without treating B as a remapped A tile."""

        output_dir.mkdir(parents=True, exist_ok=True)
        role_motifs = {
            "hero": spec.motif,
            "secondary": "waves",
            "connector": "circuits",
            "background": "diagonal",
        }
        role_offsets = {"hero": 101, "secondary": 211, "connector": 307, "background": 401}
        images: dict[str, Image.Image] = {}
        records: list[dict[str, Any]] = []
        for role in ("hero", "secondary", "connector", "background"):
            role_seed = candidate_seed * 1000 + role_offsets[role]
            role_spec = DesignSpec(
                theme_name=spec.theme_name,
                description=f"{spec.description}; semantic Route-B role: {role}",
                palette=spec.palette,
                motif=role_motifs[role],
                size=spec.size,
                candidate_count=1,
                seed=role_seed,
                prompt_motif=spec.prompt_motif,
            )
            image = self.generator.generate(role_spec, role_seed).convert("RGB")
            path = output_dir / f"route_b_{role}.png"
            image.save(path)
            images[role] = image
            records.append(
                {
                    "role": role,
                    "seed": role_seed,
                    "motif": role_motifs[role],
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        return images, records

    def _run_route_c(
        self,
        spec: DesignSpec,
        round_0: dict[str, Any],
        visibility: Mapping[str, list[Path]],
        base_color: tuple[int, int, int],
        output_dir: Path,
    ) -> dict[str, Any]:
        diagnosis = diagnose_component_detail(
            [
                _component_record_from_dict(record)
                for record in round_0["component_metrics"]
            ]
        )
        if diagnosis.target_component is None:
            diagnosis = _fallback_diagnosis(round_0["component_metrics"])
        round_0_texture = Image.open(round_0["texture"]).convert("RGB")
        _, protected_edge_factor = apply_uv_edge_safety(
            round_0_texture,
            {"uv_coverage": Image.fromarray(self.uv_maps.valid_mask.astype(np.uint8) * 255)},
            base_color=base_color,
            edge_safe_pixels=int(self.route_config["selected_edge_safe_pixels"]),
        )
        candidates: list[dict] = []
        metrics: dict[str, dict[str, float]] = {}
        for index, intensity in enumerate(
            self.refinement_config["candidate_intensities"], start=1
        ):
            candidate_id = f"round_1_candidate_{index:02d}"
            texture = _apply_component_detail_correction(
                round_0_texture,
                self.masks[diagnosis.target_component],
                int(intensity),
                float(self.route_config["transition_sigma"]),
                protected_edge_factor,
            )
            record = self._evaluate(
                "C",
                candidate_id,
                spec.seed + 1000 + index - 1,
                Path(round_0["texture"]),
                texture,
                output_dir / candidate_id,
                visibility,
            )
            record.update(
                {
                    "intensity": int(intensity),
                    "action": diagnosis.action,
                    "target_component": diagnosis.target_component,
                    "correction": {
                        "gaussian_blur_radius": float(1.5 * int(intensity)),
                        "contrast_factor": float(1.0 - 0.08 * int(intensity)),
                        "mask_feather_sigma": float(self.route_config["transition_sigma"]),
                    },
                    "locality": _locality_metrics(
                        Image.open(round_0["texture"]).convert("RGB"),
                        texture,
                        self.masks[diagnosis.target_component],
                        int(self.route_config["transition_sigma"]),
                    ),
                }
            )
            candidates.append(record)
            metrics[candidate_id] = {
                "asset_seam_error": record["asset_seam"]["total_error"],
                "multi_view_score": record["standard_score"]["multi_view"]["total_score"],
                "agent_score": record["agent_score"],
            }
        minimum_multiview = (
            round_0["standard_score"]["multi_view"]["total_score"]
            * float(self.refinement_config["minimum_multiview_retention"])
        )
        selection = constraint_first_pareto_select(
            metrics,
            (
                Constraint(
                    "asset_seam_error",
                    maximum=float(self.refinement_config["asset_seam_error_maximum"]),
                ),
                Constraint("multi_view_score", minimum=minimum_multiview),
            ),
            (
                Objective("agent_score", maximize=True),
                Objective("asset_seam_error", maximize=False),
            ),
        )
        best = next(item for item in candidates if item["candidate_id"] == selection.selected_id)
        decision = decide_refinement(
            round_0["agent_score"],
            best["agent_score"],
            float(self.refinement_config["minimum_agent_score_improvement"]),
        )
        selected = best if decision.accepted else round_0
        selected_id = best["candidate_id"] if decision.accepted else round_0["candidate_id"]
        selected_texture = Image.open(selected["texture"]).convert("RGB")
        output_dir.mkdir(parents=True, exist_ok=True)
        selected_texture.save(output_dir / "selected_texture.png")
        selected_texture.save(
            output_dir / "selected_texture__route-c__custom-paint-job.tga"
        )
        return {
            "method": "B Round 0 reused + one render-conditioned local action + rollback",
            "round_0_reused_candidate_id": round_0["candidate_id"],
            "round_0_agent_score": round_0["agent_score"],
            "diagnosis": diagnosis.to_dict(),
            "round_1_candidate_count": len(candidates),
            "round_1_candidates": candidates,
            "round_1_selection": selection.to_dict(),
            "refinement_decision": decision.to_dict(),
            "selected": {
                "round": decision.selected_round,
                "candidate_id": selected_id,
                "texture": str(output_dir / "selected_texture.png"),
            },
            "selected_record": selected,
        }

    @staticmethod
    def _write_summary(
        path: Path,
        route_a: list[dict],
        route_b: list[dict],
        route_c: dict,
        selected_ids: Mapping[str, str],
    ) -> None:
        rows: list[dict] = []
        for route, records in (("A", route_a), ("B", route_b)):
            for record in records:
                rows.append(_summary_row(route, 0, record, selected_ids[route]))
        for outcome in route_c["outcomes"]:
            rows.append(
                _summary_row(
                    "C",
                    int(outcome["route_c_selected_round"]),
                    outcome,
                    selected_ids["C"],
                )
            )
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def paired_route_summary(
    route_a: list[dict],
    route_b: list[dict],
    *,
    bootstrap_seed: int,
    bootstrap_samples: int = 10000,
) -> dict[str, dict[str, Any]]:
    a_by_id = {record["candidate_id"]: record for record in route_a}
    b_by_id = {record["candidate_id"]: record for record in route_b}
    if set(a_by_id) != set(b_by_id):
        raise ValueError("Paired A/B summaries require identical candidate ids")
    extractors = {
        "asset_seam_improvement": lambda a, b: a["asset_seam"]["total_error"]
        - b["asset_seam"]["total_error"],
        "multi_view_improvement": lambda a, b: b["standard_score"]["multi_view"]["total_score"]
        - a["standard_score"]["multi_view"]["total_score"],
        "component_balance_improvement": lambda a, b: b["component_detail_balance"]
        - a["component_detail_balance"],
        "agent_score_improvement": lambda a, b: b["agent_score"] - a["agent_score"],
    }
    rng = np.random.default_rng(bootstrap_seed)
    result: dict[str, dict[str, Any]] = {}
    ordered_ids = sorted(a_by_id)
    for metric, extractor in extractors.items():
        values = np.asarray(
            [extractor(a_by_id[candidate_id], b_by_id[candidate_id]) for candidate_id in ordered_ids],
            dtype=np.float64,
        )
        indices = rng.integers(0, len(values), size=(bootstrap_samples, len(values)))
        bootstrap_means = values[indices].mean(axis=1)
        result[metric] = {
            "paired_values": values.tolist(),
            "mean": float(values.mean()),
            "median": float(np.median(values)),
            "std": float(values.std()),
            "win_rate": float(np.mean(values > 0)),
            "bootstrap_95_ci_mean": [
                float(np.quantile(bootstrap_means, 0.025)),
                float(np.quantile(bootstrap_means, 0.975)),
            ],
            "bootstrap_samples": bootstrap_samples,
        }
    return result


def _agent_score(
    texture_score: float,
    multi_view_score: float,
    component_balance: float,
    weights: Mapping[str, float],
) -> float:
    return float(
        float(weights["texture_score"]) * texture_score
        + float(weights["multi_view_score"]) * multi_view_score
        + float(weights["component_detail_balance"]) * component_balance
    )


def _component_record_from_dict(data: Mapping[str, Any]):
    from .component_feedback import ComponentAggregateMetrics

    return ComponentAggregateMetrics(**data)


def _fallback_diagnosis(records: list[dict]) -> ComponentDiagnosis:
    target = max(records, key=lambda item: (item["detail_density"], item["component"]))
    return ComponentDiagnosis(
        action="reduce_component_detail",
        target_component=str(target["component"]),
        relative_excess=float(target["relative_excess"]),
        reason="No component exceeded target; bounded fallback selected the highest rendered detail density",
    )


def _locality_metrics(
    before: Image.Image,
    after: Image.Image,
    target_mask: Image.Image,
    transition_pixels: int,
) -> dict[str, float | int]:
    before_array = np.asarray(before.convert("RGB"), dtype=np.int16)
    after_array = np.asarray(after.convert("RGB"), dtype=np.int16)
    changed = np.max(np.abs(before_array - after_array), axis=2) > 1
    mask = np.asarray(target_mask.convert("L"), dtype=np.uint8) > 127
    radius = max(1, transition_pixels * 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    allowed = cv2.dilate(mask.astype(np.uint8), kernel) > 0
    changed_count = int(np.count_nonzero(changed))
    outside_count = int(np.count_nonzero(changed & ~allowed))
    return {
        "changed_pixel_count": changed_count,
        "changed_pixel_fraction": changed_count / changed.size,
        "changed_outside_target_halo_count": outside_count,
        "changed_outside_target_halo_fraction_of_changes": outside_count / max(changed_count, 1),
        "target_halo_radius_pixels": radius,
    }


def _apply_component_detail_correction(
    texture: Image.Image,
    target_mask: Image.Image,
    intensity: int,
    transition_sigma: float,
    protected_edge_factor: Image.Image | None = None,
) -> Image.Image:
    """Apply one bounded render-conditioned correction inside a component halo."""

    if intensity not in {1, 2}:
        raise ValueError("Route-C correction intensity must be 1 or 2")
    source = texture.convert("RGB")
    softened = source.filter(ImageFilter.GaussianBlur(radius=1.5 * intensity))
    softened = ImageEnhance.Contrast(softened).enhance(1.0 - 0.08 * intensity)
    mask = target_mask.convert("L")
    if mask.size != source.size:
        mask = mask.resize(source.size, Image.Resampling.NEAREST)
    hard_mask = np.asarray(mask, dtype=np.uint8) > 127
    radius = max(1, int(round(transition_sigma * 3.0)))
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1)
    )
    allowed = cv2.dilate(hard_mask.astype(np.uint8), kernel) > 0
    feathered = np.asarray(
        mask.filter(ImageFilter.GaussianBlur(radius=max(0.0, transition_sigma))),
        dtype=np.float32,
    ) / 255.0
    feathered[~allowed] = 0.0
    if protected_edge_factor is not None:
        edge_factor = np.asarray(
            protected_edge_factor.convert("L").resize(source.size, Image.Resampling.NEAREST),
            dtype=np.float32,
        ) / 255.0
        feathered *= edge_factor
    corrected = (
        np.asarray(source, dtype=np.float32) * (1.0 - feathered[..., None])
        + np.asarray(softened, dtype=np.float32) * feathered[..., None]
    )
    return Image.fromarray(np.clip(corrected, 0, 255).astype(np.uint8), mode="RGB")


def _summary_row(route: str, round_number: int, record: dict, selected_id: str) -> dict:
    return {
        "route": route,
        "round": round_number,
        "candidate_id": record["candidate_id"],
        "seed": record["seed"],
        "asset_seam_error": record["asset_seam"]["total_error"],
        "periodic_seam_error": record["periodic_seam_error"],
        "texture_score": record["standard_score"]["texture_score"],
        "multi_view_score": record["standard_score"]["multi_view"]["total_score"],
        "component_detail_balance": record["component_detail_balance"],
        "agent_score": record["agent_score"],
        "selected": record["candidate_id"] == selected_id,
    }


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
