from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

from .spec import SemanticScore


DEFAULT_CLIP_REVISION = "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"


def scale_clip_similarity(cosine: float) -> float:
    """CLIPScore scaling: 2.5 * max(cosine, 0), capped for weighted ranking."""
    return float(min(1.0, 2.5 * max(cosine, 0.0)))


class SemanticEvaluator(ABC):
    @abstractmethod
    def evaluate(self, text: str, texture: Image.Image, preview_paths: list[Path]) -> SemanticScore:
        raise NotImplementedError

    def metadata(self) -> dict[str, Any]:
        return {"backend": type(self).__name__}


class ClipSemanticEvaluator(SemanticEvaluator):
    """Reference-free text/image compatibility using OpenAI CLIP ViT-B/32."""

    def __init__(
        self,
        model_id: str = "openai/clip-vit-base-patch32",
        *,
        revision: str | None = DEFAULT_CLIP_REVISION,
        device: str = "cuda",
        model: Any | None = None,
        processor: Any | None = None,
    ) -> None:
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self._model = model
        self._processor = processor
        self._resolved_revision: str | None = revision
        self._last_runtime_seconds: float | None = None
        self._peak_vram_gb: float | None = None

    def _load(self) -> tuple[Any, Any]:
        if self._model is not None and self._processor is not None:
            return self._model, self._processor
        if self.device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("CUDA is required for the configured CLIP evaluator")
        try:
            from transformers import CLIPModel, CLIPProcessor
        except ImportError as error:
            raise RuntimeError("Transformers with CLIP support is required for semantic scoring") from error

        kwargs: dict[str, Any] = {}
        if self.revision:
            kwargs["revision"] = self.revision
        self._model = CLIPModel.from_pretrained(self.model_id, **kwargs).eval().to(self.device)
        self._processor = CLIPProcessor.from_pretrained(self.model_id, **kwargs)
        config = getattr(self._model, "config", None)
        self._resolved_revision = getattr(config, "_commit_hash", None) or self.revision
        return self._model, self._processor

    @staticmethod
    def _tensor(value: Any) -> torch.Tensor:
        if isinstance(value, torch.Tensor):
            return value
        for attribute in ("pooler_output", "image_embeds", "text_embeds"):
            candidate = getattr(value, attribute, None)
            if isinstance(candidate, torch.Tensor):
                return candidate
        if isinstance(value, (tuple, list)) and value and isinstance(value[0], torch.Tensor):
            return value[0]
        raise TypeError(f"Unsupported CLIP feature output: {type(value).__name__}")

    def evaluate(self, text: str, texture: Image.Image, preview_paths: list[Path]) -> SemanticScore:
        model, processor = self._load()
        individual_views = [path for path in preview_paths if not path.stem.endswith("_multiview")]
        images = [texture.convert("RGB")]
        images.extend(Image.open(path).convert("RGB") for path in individual_views)

        started = time.perf_counter()
        if self.device.startswith("cuda"):
            torch.cuda.reset_peak_memory_stats(self.device)
        image_inputs = processor(images=images, return_tensors="pt")
        text_inputs = processor(text=[text], return_tensors="pt", padding=True)
        image_inputs = {key: value.to(self.device) for key, value in image_inputs.items()}
        text_inputs = {key: value.to(self.device) for key, value in text_inputs.items()}

        with torch.inference_mode():
            image_features = self._tensor(model.get_image_features(**image_inputs))
            text_features = self._tensor(model.get_text_features(**text_inputs))
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            cosine = (image_features @ text_features.T).squeeze(-1).float().cpu().numpy()

        texture_cosine = float(cosine[0])
        view_cosines = tuple(float(value) for value in cosine[1:])
        view_mean = float(np.mean(view_cosines)) if view_cosines else texture_cosine
        combined = 0.60 * texture_cosine + 0.40 * view_mean
        self._last_runtime_seconds = time.perf_counter() - started
        if self.device.startswith("cuda"):
            self._peak_vram_gb = torch.cuda.max_memory_allocated(self.device) / 1024**3
        return SemanticScore(
            text=text,
            texture_cosine=texture_cosine,
            view_cosines=view_cosines,
            combined_cosine=combined,
            total_score=scale_clip_similarity(combined),
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "backend": type(self).__name__,
            "model_id": self.model_id,
            "requested_revision": self.revision,
            "resolved_revision": self._resolved_revision,
            "device": self.device,
            "last_runtime_seconds": self._last_runtime_seconds,
            "peak_vram_gb": self._peak_vram_gb,
            "formula": "min(1, 2.5 * max(0.6 * texture_cosine + 0.4 * mean_view_cosine, 0))",
        }
