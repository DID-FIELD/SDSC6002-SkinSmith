from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image, ImageDraw


class PreviewRenderer(ABC):
    supports_multiview_scoring = False

    @abstractmethod
    def render(self, texture: Image.Image, output_dir: Path, stem: str) -> list[Path]:
        raise NotImplementedError


class TiledPreviewRenderer(PreviewRenderer):
    """Phase-1 renderer that exposes repeat seams before 3D geometry is connected."""

    def render(self, texture: Image.Image, output_dir: Path, stem: str) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        texture = texture.convert("RGB")
        tile = texture.resize((256, 256), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (768, 768), "#20242A")
        for row in range(3):
            for column in range(3):
                canvas.paste(tile, (column * 256, row * 256))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, 767, 767), outline="#FFFFFF", width=2)
        path = output_dir / f"{stem}_tiled_preview.png"
        canvas.save(path)
        return [path]
