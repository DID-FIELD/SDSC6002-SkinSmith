from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith import SkinSmithPipeline  # noqa: E402
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
    )
    result = SkinSmithPipeline().run(spec, PROJECT_ROOT / "runs" / "smoke")
    print(json.dumps({"best_candidate": result["best_candidate"], "count": len(result["candidates"])}, indent=2))


if __name__ == "__main__":
    main()

