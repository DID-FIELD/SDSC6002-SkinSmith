from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments" / "public" / "flower_workflow_v1"
FLOW_RUN = ROOT / "runs" / "agent_flower_demo_v1"
SELECTED_RUN = ROOT / "runs" / "agent_flower_ornamental_v2"
PACKAGE_NAME = "SkinSmith public flower workflow evidence"

SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"sk-[0-9A-Za-z_-]{20,}"),
)
SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "access_token",
    "refresh_token",
    "client_secret",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sanitize(value: Any, key: str = "") -> Any:
    if key.casefold() in SENSITIVE_KEYS:
        return "<redacted>"
    if isinstance(value, dict):
        return {name: sanitize(item, str(name)) for name, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        cleaned = value
        for pattern in SECRET_PATTERNS:
            cleaned = pattern.sub("<redacted-secret>", cleaned)
        if len(cleaned) > 20_000:
            digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
            return f"<omitted-long-value length={len(cleaned)} sha256={digest}>"
        return cleaned
    return value


def copy_binary(source: Path, relative: Path, manifest: list[dict[str, Any]]) -> None:
    destination = OUTPUT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    manifest.append(
        {
            "path": relative.as_posix(),
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "source": source.relative_to(ROOT).as_posix(),
            "sanitized": False,
        }
    )


def copy_json(source: Path, relative: Path, manifest: list[dict[str, Any]]) -> None:
    destination = OUTPUT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(source.read_text(encoding="utf-8"))
    destination.write_text(
        json.dumps(sanitize(data), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest.append(
        {
            "path": relative.as_posix(),
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "source": source.relative_to(ROOT).as_posix(),
            "sanitized": True,
        }
    )


def copy_jsonl(source: Path, relative: Path, manifest: list[dict[str, Any]]) -> None:
    destination = OUTPUT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.dumps(sanitize(json.loads(line)), ensure_ascii=False))
    destination.write_text("\n".join(rows) + "\n", encoding="utf-8")
    manifest.append(
        {
            "path": relative.as_posix(),
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "source": source.relative_to(ROOT).as_posix(),
            "sanitized": True,
        }
    )


def main() -> None:
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty package: {OUTPUT}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []

    for name in (
        "checkpoint.json",
        "events.jsonl",
        "memory_snapshot.json",
        "agent_run_result.json",
    ):
        source = FLOW_RUN / name
        if not source.is_file():
            continue
        relative = Path("workflow") / name
        if source.suffix == ".jsonl":
            copy_jsonl(source, relative, manifest)
        else:
            copy_json(source, relative, manifest)

    for source in sorted((FLOW_RUN / "planning").glob("*.json")):
        copy_json(source, Path("workflow/planning") / source.name, manifest)

    for index in range(1, 5):
        candidate = f"artwork_{index:02d}"
        base = FLOW_RUN / "artwork_candidates" / candidate
        copy_binary(
            base / "source" / "route_b_master_artwork.png",
            Path("workflow/candidates") / candidate / "source.png",
            manifest,
        )
        copy_binary(
            base / "mapped_preview" / "route_b_width_1_multiview.png",
            Path("workflow/candidates") / candidate / "multiview.png",
            manifest,
        )
        copy_json(
            base / "source" / "generation_log.json",
            Path("workflow/candidates") / candidate / "generation_log.json",
            manifest,
        )
        copy_json(
            base / "source" / "route_b_master_artwork_validation.json",
            Path("workflow/candidates") / candidate / "source_validation.json",
            manifest,
        )

    trace_sources = sorted(FLOW_RUN.rglob("*trace.json"))
    for source in trace_sources:
        relative = Path("api_traces") / source.relative_to(FLOW_RUN)
        copy_json(source, relative, manifest)

    for name in (
        "checkpoint.json",
        "events.jsonl",
        "memory_snapshot.json",
        "agent_run_result.json",
    ):
        source = SELECTED_RUN / name
        relative = Path("selected_ornamental") / name
        if source.suffix == ".jsonl":
            copy_jsonl(source, relative, manifest)
        else:
            copy_json(source, relative, manifest)

    copy_json(
        SELECTED_RUN / "execution" / "execution_manifest.json",
        Path("selected_ornamental/execution_manifest.json"),
        manifest,
    )
    route_b = SELECTED_RUN / "execution" / "route_b"
    for name in (
        "route_b_log.json",
        "route_b_selected.png",
        "route_b_width_4_left.png",
        "route_b_width_4_right.png",
        "route_b_width_4_top.png",
        "route_b_width_4_multiview.png",
        "selected__route-b__custom-paint-job.tga",
    ):
        source = route_b / name
        relative = Path("selected_ornamental/final") / name
        if source.suffix == ".json":
            copy_json(source, relative, manifest)
        else:
            copy_binary(source, relative, manifest)

    package = {
        "package": PACKAGE_NAME,
        "source_runs": list(
            dict.fromkeys(
                (
                    FLOW_RUN.relative_to(ROOT).as_posix(),
                    SELECTED_RUN.relative_to(ROOT).as_posix(),
                )
            )
        ),
        "secret_policy": (
            "API keys and authorization values are excluded. Provider, model, "
            "endpoint, prompts, usage, retries, decisions, and response metadata "
            "are retained. Long embedded values are replaced by length and SHA-256."
        ),
        "raw_runs_local_bytes": sum(
            path.stat().st_size
            for run in (FLOW_RUN, SELECTED_RUN)
            for path in run.rglob("*")
            if path.is_file()
        ),
        "files": sorted(manifest, key=lambda item: item["path"]),
    }
    manifest_path = OUTPUT / "manifest.json"
    manifest_path.write_text(
        json.dumps(package, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "files": len(manifest),
                "bytes": sum(item["bytes"] for item in manifest),
                "manifest_sha256": sha256(manifest_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
