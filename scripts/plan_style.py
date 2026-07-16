from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.style_planner import StyleLibrary, StylePlanner  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Expand a user brief into paired Route-A and Route-B art directions."
    )
    parser.add_argument("brief", help="Natural-language skin design brief")
    parser.add_argument(
        "--style",
        default="auto",
        help="Style-pack filename under config/styles, or auto to infer from the brief",
    )
    parser.add_argument("--count", type=int, default=4, help="Number of alternatives")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "runs" / "style_plan" / "art_direction.json",
    )
    args = parser.parse_args()

    library = StyleLibrary.load_directory(PROJECT_ROOT / "config" / "styles")
    plan = StylePlanner(library.resolve(args.brief, args.style)).plan(args.brief, args.count)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {len(plan.candidates)} art directions to {args.output}")


if __name__ == "__main__":
    main()
