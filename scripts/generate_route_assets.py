from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.api_backends import (  # noqa: E402
    ApiBackendError,
    GeminiImageBackend,
    OpenAIImageBackend,
)
from skinsmith.route_asset_generation import plan_route_image_jobs  # noqa: E402
from skinsmith.style_planner import StylePack  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_log(path: Path, log: dict) -> None:
    path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    defaults = json.loads(
        (PROJECT_ROOT / "config" / "creative_api.json").read_text(encoding="utf-8")
    )
    parser = argparse.ArgumentParser(
        description="Generate internal Route-A/B source assets; mapped previews remain mandatory."
    )
    parser.add_argument("bundle", type=Path, help="RouteDesignBundle JSON")
    parser.add_argument("--route", choices=("a", "b", "all"), default="all")
    parser.add_argument(
        "--role",
        action="append",
        choices=("hero", "secondary", "connector", "background"),
        help="Generate only selected Route-B semantic roles; may be repeated",
    )
    parser.add_argument(
        "--provider",
        choices=("gemini", "openai"),
        default=defaults["image_provider"],
    )
    parser.add_argument("--model", help="Override the configured image model")
    parser.add_argument("--api-key-env", help="Override the configured key environment variable")
    parser.add_argument(
        "--route-a-candidates",
        type=int,
        default=int(defaults["initial_route_a_candidates"]),
    )
    parser.add_argument(
        "--direction",
        help="Lock generation to one candidate_directions.direction_id from the bundle StylePack",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "runs" / "api_route_assets",
    )
    args = parser.parse_args()

    bundle_path = args.bundle.resolve()
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    candidate_direction = None
    if args.direction:
        style_path = Path(str(bundle.get("style_pack_path", "")))
        if not style_path.is_absolute():
            style_path = PROJECT_ROOT / style_path
        if not style_path.is_file():
            raise ValueError("bundle style_pack_path is missing; cannot resolve --direction")
        style = StylePack.load(style_path)
        selected = next(
            (
                item
                for item in style.candidate_directions
                if item.direction_id == args.direction
            ),
            None,
        )
        if selected is None:
            available = ", ".join(item.direction_id for item in style.candidate_directions)
            raise ValueError(
                f"unknown --direction {args.direction!r}; available: {available}"
            )
        candidate_direction = asdict(selected)
    jobs = plan_route_image_jobs(
        bundle,
        route=args.route,
        route_a_candidates=args.route_a_candidates,
        candidate_direction=candidate_direction,
    )
    if args.role:
        selected_roles = set(args.role)
        jobs = tuple(
            job
            for job in jobs
            if job.route == "B" and job.semantic_role in selected_roles
        )
        if not jobs:
            raise ValueError("--role selected no Route-B generation jobs")
    if args.provider == "gemini":
        backend = GeminiImageBackend(
            args.model or defaults["image_model"],
            api_key_env=args.api_key_env or defaults["image_api_key_env"],
            image_size=defaults["image_size"],
            aspect_ratio=defaults["image_aspect_ratio"],
        )
    else:
        backend = OpenAIImageBackend(
            args.model or "gpt-image-2",
            api_key_env=args.api_key_env or "OPENAI_API_KEY",
            size="1536x1024",
            quality="medium",
        )

    args.output.mkdir(parents=True, exist_ok=True)
    bundle_sha256 = _sha256(bundle_path)
    log_path = args.output / "generation_log.json"
    if log_path.is_file():
        log = json.loads(log_path.read_text(encoding="utf-8"))
        if log.get("bundle_sha256") != bundle_sha256:
            raise RuntimeError(
                "output directory belongs to a different route bundle; choose a new --output"
            )
        if log.get("backend_id") != backend.backend_id:
            raise RuntimeError(
                "output directory belongs to a different image backend; choose a new --output"
            )
        if log.get("art_direction_id") != args.direction:
            raise RuntimeError(
                "output directory belongs to a different candidate direction; choose a new --output"
            )
        records = list(log.get("jobs", []))
    else:
        records = []
        log = {
            "bundle": str(bundle_path),
            "bundle_sha256": bundle_sha256,
            "provider": args.provider,
            "backend_id": backend.backend_id,
            "model_family": (
                defaults["image_model_family"] if args.provider == "gemini" else None
            ),
            "art_direction_id": args.direction,
            "art_direction": candidate_direction,
            "jobs": records,
            "acceptance_boundary": defaults["acceptance_boundary"],
        }
    records_by_id = {record["job_id"]: record for record in records}
    requested_ids = [job.job_id for job in jobs]
    log["status"] = "in_progress"
    log["last_requested_job_ids"] = requested_ids
    log["jobs"] = records
    _write_log(log_path, log)

    generated_count = 0
    reused_count = 0
    for job in jobs:
        existing = records_by_id.get(job.job_id)
        if existing is not None:
            existing_output = Path(existing["output"])
            existing_trace = Path(existing["trace"])
            if (
                existing_output.is_file()
                and existing_trace.is_file()
                and existing.get("output_sha256") == _sha256(existing_output)
            ):
                reused_count += 1
                continue
        try:
            image = backend.generate_image(job.prompt)
        except ApiBackendError as error:
            log["status"] = "blocked"
            log["last_error"] = {
                "job_id": job.job_id,
                "error_type": type(error).__name__,
                "message": str(error),
            }
            _write_log(log_path, log)
            raise
        output_path = args.output / job.output_name
        image.save(output_path)
        trace_path = args.output / f"{job.job_id}_api_trace.json"
        if backend.last_trace is None:
            raise RuntimeError("image backend did not expose an API trace")
        trace_path.write_text(
            json.dumps(backend.last_trace.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        record = {
            "job_id": job.job_id,
            "route": job.route,
            "semantic_role": job.semantic_role,
            "prompt": job.prompt,
            "output": str(output_path),
            "output_sha256": _sha256(output_path),
            "trace": str(trace_path),
        }
        if existing is None:
            records.append(record)
        else:
            records[records.index(existing)] = record
        records_by_id[job.job_id] = record
        generated_count += 1
        log["jobs"] = records
        log["completed_job_ids"] = [record["job_id"] for record in records]
        _write_log(log_path, log)

    log["status"] = "complete"
    log.pop("last_error", None)
    log["completed_job_ids"] = [record["job_id"] for record in records]
    _write_log(log_path, log)
    print(
        f"Generated {generated_count} and reused {reused_count} internal assets "
        f"with {backend.backend_id}"
        f"{f' for direction {args.direction}' if args.direction else ''}. "
        "They are not accepted until UV mapping and AK-47 left/right/top review."
    )


if __name__ == "__main__":
    main()
