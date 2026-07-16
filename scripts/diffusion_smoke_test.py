from __future__ import annotations

import json
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.generator import DiffusionTextureGenerator  # noqa: E402
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
        candidate_count=1,
    )
    generator = DiffusionTextureGenerator()
    started = time.perf_counter()
    image = generator.generate(spec, spec.seed)
    output_dir = PROJECT_ROOT / "runs" / "diffusion_smoke"
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / "neon_tide_seed_20260714.png"
    image.save(image_path)
    evidence = {
        "design_spec": spec.to_dict(),
        "generator": generator.metadata(),
        "runtime_seconds": time.perf_counter() - started,
        "image": str(image_path),
    }
    (output_dir / "generation_log.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
