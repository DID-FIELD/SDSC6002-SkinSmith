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
    bundle_path = (
        PROJECT_ROOT
        / "runs"
        / "theme_compilation_marble_dynamic_style"
        / "route_design_bundle.json"
    )
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    pattern = bundle["pattern"]
    spec = DesignSpec(
        theme_name=str(bundle["theme_name"]),
        description=str(pattern["generation_prompt"]),
        palette=tuple(str(value) for value in pattern["palette"]),
        motif="diagonal",
        prompt_motif="geological marble strata and branching gold mineral fissures",
        size=512,
        candidate_count=4,
        seed=20260716,
    )
    output_dir = PROJECT_ROOT / "runs" / "abc_ablation_true_weapon_space"
    result = ABCAblationRunner(
        PROJECT_ROOT,
        route_bundle_path=bundle_path,
    ).run(spec, output_dir)
    print(
        json.dumps(
            {
                "status": result["status"],
                "stage": result["stage"],
                "selected_ids": result["selected_ids"],
                "route_b_selection": result["route_b"]["selection"],
                "route_c_selection": result["route_c"]["selection"],
                "route_c_selected_round": result["route_c"]["selected_round"],
                "paired_b_minus_a": result["paired_b_minus_a"],
                "paired_c_minus_b": result["route_c"]["paired_c_minus_b"],
                "runtime_seconds": result["runtime_seconds"],
                "output_dir": str(output_dir),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
