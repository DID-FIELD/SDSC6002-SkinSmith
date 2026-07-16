from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.api_backends import GeminiMappedReadabilityReviewer  # noqa: E402
from skinsmith.mapped_readability import (  # noqa: E402
    build_readability_report,
    design_elements_from_records,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score design-element readability on mapped left/right/top views."
    )
    parser.add_argument("run", type=Path, help="Completed SkinSmith Agent run")
    parser.add_argument(
        "--model",
        default="gemini-3.1-flash-lite",
        help="Gemini multimodal review model",
    )
    args = parser.parse_args()
    run = args.run
    checkpoint = json.loads((run / "checkpoint.json").read_text(encoding="utf-8"))
    state = checkpoint["state"]
    direction = state["design_contract"]["selected_direction"]
    manifest_path = run / "execution" / "execution_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    planning = json.loads(
        (run / "planning" / "planning_manifest.json").read_text(encoding="utf-8")
    )
    theme = json.loads(Path(planning["theme"]["path"]).read_text(encoding="utf-8"))
    elements = design_elements_from_records(
        theme.get("elements", ()),
        direction.get("motifs", ()),
        direction.get("world_elements", ()),
    )
    selected = manifest["selected_artwork"]
    source_path = Path(selected["source"])
    preview_paths = [Path(path) for path in manifest["route_b"]["previews"]]
    views = {
        name: Image.open(
            next(path for path in preview_paths if path.stem.endswith(f"_{name}"))
        ).convert("RGB")
        for name in ("left", "right", "top")
    }
    reviewer = GeminiMappedReadabilityReviewer(args.model)
    matches = reviewer(elements, Image.open(source_path).convert("RGB"), views)
    report = build_readability_report(elements, matches)
    report.update(
        {
            "run_id": state["run_id"],
            "selected_direction": direction["direction_id"],
            "selected_artwork": state["selected_artwork_id"],
            "selected_route": manifest["decision"]["selected_route"],
            "reviewer": reviewer.backend_id,
            "inputs": {
                "source": str(source_path),
                "source_sha256": _sha256(source_path),
                "views": {
                    name: {
                        "path": str(
                            next(
                                path
                                for path in preview_paths
                                if path.stem.endswith(f"_{name}")
                            )
                        ),
                        "sha256": _sha256(
                            next(
                                path
                                for path in preview_paths
                                if path.stem.endswith(f"_{name}")
                            )
                        ),
                    }
                    for name in ("left", "right", "top")
                },
            },
        }
    )
    output = run / "execution" / "mapped_element_readability.json"
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if reviewer.last_trace is not None:
        (run / "execution" / "mapped_element_readability_trace.json").write_text(
            json.dumps(
                reviewer.last_trace.to_dict(),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
