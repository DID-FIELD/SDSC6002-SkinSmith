from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.ablation import ABCAblationRunner  # noqa: E402
from skinsmith.spec import DesignSpec  # noqa: E402


def main() -> None:
    themes = json.loads((PROJECT_ROOT / "config" / "themes.json").read_text(encoding="utf-8"))
    theme_name = "neon_tide"
    theme = themes[theme_name]
    spec = DesignSpec(
        theme_name=theme_name,
        description=theme["description"],
        palette=tuple(theme["palette"]),
        motif=theme["motif"],
        size=512,
        candidate_count=4,
        seed=20260714,
    )
    output_dir = PROJECT_ROOT / "runs" / "abc_ablation_smoke"
    result = ABCAblationRunner(PROJECT_ROOT).run(spec, output_dir)
    print(json.dumps({
        "status": result["status"],
        "shared_sources": result["shared_sources"],
        "selected_ids": result["selected_ids"],
        "route_b_selection": result["route_b"]["selection"],
        "route_c_decision": result["route_c"]["refinement_decision"],
        "paired_b_minus_a": result["paired_b_minus_a"],
        "runtime_seconds": result["runtime_seconds"],
        "output_dir": str(output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()
