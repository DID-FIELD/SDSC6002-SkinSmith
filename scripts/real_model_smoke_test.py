from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith import SkinSmithPipeline  # noqa: E402
from skinsmith.obj_renderer import ObjMultiViewRenderer  # noqa: E402
from skinsmith.spec import DesignSpec  # noqa: E402


def main() -> None:
    model_path = PROJECT_ROOT / "third_party" / "valve_geometry" / "weapon_rif_ak47.obj"
    if not model_path.exists():
        raise SystemExit(f"Missing local Valve model: {model_path}\nSee ASSET_SETUP.md.")

    themes = json.loads((PROJECT_ROOT / "config" / "themes.json").read_text(encoding="utf-8"))
    theme_name = "neon_tide"
    theme = themes[theme_name]
    spec = DesignSpec(
        theme_name=theme_name,
        description=theme["description"],
        palette=tuple(theme["palette"]),
        motif=theme["motif"],
        candidate_count=4,
    )
    renderer = ObjMultiViewRenderer(model_path)
    result = SkinSmithPipeline(renderer=renderer).run(spec, PROJECT_ROOT / "runs" / "real_model_smoke")
    print(json.dumps({"best_candidate": result["best_candidate"], "previews": result["candidates"][0]["previews"]}, indent=2))


if __name__ == "__main__":
    main()
