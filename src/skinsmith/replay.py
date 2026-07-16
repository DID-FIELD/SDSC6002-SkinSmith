from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


RESULT_FILENAME = "agent_run_result.json"
READABILITY_RELATIVE_PATH = Path("execution/mapped_element_readability.json")


def resolve_project_path(project_root: Path, value: str | Path) -> Path:
    """Resolve a persisted project-relative path without allowing repository escape."""
    project_root = Path(project_root).resolve()
    raw = str(value).replace("\\", "/")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise ValueError(f"persisted path escapes the project root: {value}") from error
    return resolved


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class ReplayRun:
    project_root: Path
    run_dir: Path
    result: Mapping[str, Any]
    readability: Mapping[str, Any] | None

    @property
    def phase(self) -> str:
        return str(self.result.get("phase", "unknown"))

    @property
    def selected_direction_id(self) -> str | None:
        contract = self.result.get("design_contract")
        if not isinstance(contract, Mapping):
            return None
        direction = contract.get("selected_direction")
        return (
            str(direction.get("direction_id"))
            if isinstance(direction, Mapping) and direction.get("direction_id")
            else None
        )

    @property
    def selected_artwork_id(self) -> str | None:
        value = self.result.get("selected_artwork_id")
        return str(value) if value else None

    @property
    def budget(self) -> Mapping[str, Any]:
        request = self.result.get("request", {})
        return request.get("budget", {}) if isinstance(request, Mapping) else {}

    @property
    def usage(self) -> Mapping[str, int]:
        checkpoint_path = self.run_dir / "checkpoint.json"
        if not checkpoint_path.exists():
            return {}
        checkpoint = _load_json(checkpoint_path)
        state = checkpoint.get("state", checkpoint)
        return {
            "image_calls_used": int(state.get("image_calls_used", 0)),
            "role_retries_used": int(state.get("role_retries_used", 0)),
            "refinement_rounds_used": int(
                state.get("refinement_rounds_used", 0)
            ),
        }

    def path(self, value: str | Path) -> Path:
        return resolve_project_path(self.project_root, value)


def load_replay_run(project_root: Path, run_dir: Path) -> ReplayRun:
    project_root = Path(project_root).resolve()
    run_dir = resolve_project_path(project_root, run_dir)
    result_path = run_dir / RESULT_FILENAME
    if result_path.is_file():
        result = _load_json(result_path)
    else:
        checkpoint_path = run_dir / "checkpoint.json"
        if not checkpoint_path.is_file():
            raise FileNotFoundError(
                f"Agent result or checkpoint not found under: {run_dir}"
            )
        checkpoint = _load_json(checkpoint_path)
        state = checkpoint.get("state", {})
        phase = str(state.get("phase", "unknown"))
        result = {
            "run_id": state.get("run_id"),
            "status": phase,
            "phase": phase,
            "request": state.get("request", {}),
            "theme_expansion": state.get("theme_expansion"),
            "directions": state.get("candidates", []),
            "design_contract": state.get("design_contract"),
            "artwork_candidates": state.get("artwork_candidates", []),
            "selected_artwork_id": state.get("selected_artwork_id"),
            "artifacts": {},
            "metrics": {},
            "decision": {},
            "events": checkpoint.get("events", []),
            "checkpoint_path": str(checkpoint_path),
            "stop_reason": state.get("stop_reason"),
        }
    readability_path = run_dir / READABILITY_RELATIVE_PATH
    return ReplayRun(
        project_root=project_root,
        run_dir=run_dir,
        result=result,
        readability=(
            _load_json(readability_path) if readability_path.is_file() else None
        ),
    )


def discover_replay_runs(project_root: Path) -> tuple[Path, ...]:
    project_root = Path(project_root).resolve()
    runs_root = project_root / "runs"
    if not runs_root.exists():
        return ()
    return tuple(
        sorted(
            (
                path
                for path in runs_root.iterdir()
                if path.is_dir()
                and (
                    (path / RESULT_FILENAME).is_file()
                    or (path / "checkpoint.json").is_file()
                )
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    )
