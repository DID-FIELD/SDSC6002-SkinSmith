from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import cv2
import numpy as np
from PIL import Image

from .spec import DesignSpec


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


class TextureGenerator(ABC):
    @abstractmethod
    def generate(self, spec: DesignSpec, seed: int) -> Image.Image:
        raise NotImplementedError

    def metadata(self) -> dict[str, Any]:
        return {"backend": type(self).__name__}


class ApiTextureGenerator(TextureGenerator):
    """Route-A image adapter for any API backend exposing generate_image(prompt)."""

    def __init__(self, image_backend: Any) -> None:
        if not callable(getattr(image_backend, "generate_image", None)):
            raise TypeError("image_backend must expose generate_image(prompt)")
        self.image_backend = image_backend
        self._last_prompt: str | None = None
        self._last_seed: int | None = None

    def generate(self, spec: DesignSpec, seed: int) -> Image.Image:
        prompt = (
            f"{build_texture_prompt(spec)}; candidate variation token {seed}; "
            "original professional game-skin illustration; visually rich theme-specific subjects; "
            "no text, logo, watermark, weapon mockup, or UV wireframe"
        )
        self._last_prompt = prompt
        self._last_seed = seed
        return self.image_backend.generate_image(prompt).resize(
            (spec.size, spec.size), Image.Resampling.LANCZOS
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "backend": type(self).__name__,
            "provider_backend": getattr(self.image_backend, "backend_id", None),
            "last_prompt": self._last_prompt,
            "last_seed_label": self._last_seed,
            "provider_seed_control": False,
        }


class ProceduralTextureGenerator(TextureGenerator):
    """Deterministic placeholder backend used to validate the full agent loop."""

    def generate(self, spec: DesignSpec, seed: int) -> Image.Image:
        rng = np.random.default_rng(seed)
        size = spec.size
        palette = np.asarray([_hex_to_rgb(color) for color in spec.palette], dtype=np.uint8)
        image = np.empty((size, size, 3), dtype=np.uint8)
        image[:] = palette[0]

        if spec.motif == "waves":
            self._waves(image, palette, rng)
        elif spec.motif == "diagonal":
            self._diagonal(image, palette, rng)
        else:
            self._circuits(image, palette, rng)

        noise = rng.normal(0, 5, image.shape).astype(np.int16)
        image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(image, mode="RGB")

    def metadata(self) -> dict[str, Any]:
        return {"backend": type(self).__name__, "deterministic": True}

    @staticmethod
    def _waves(image: np.ndarray, palette: np.ndarray, rng: np.random.Generator) -> None:
        height, width = image.shape[:2]
        x = np.arange(width)
        for index in range(28):
            amplitude = int(rng.integers(12, 45))
            frequency = float(rng.uniform(0.015, 0.05))
            phase = float(rng.uniform(0, np.pi * 2))
            center = int(rng.integers(0, height))
            y = center + amplitude * np.sin(frequency * x + phase)
            points = np.column_stack((x, np.mod(y, height))).astype(np.int32)
            color = tuple(int(v) for v in palette[1 + index % (len(palette) - 1)])
            cv2.polylines(image, [points], False, color, int(rng.integers(2, 8)), cv2.LINE_AA)

    @staticmethod
    def _diagonal(image: np.ndarray, palette: np.ndarray, rng: np.random.Generator) -> None:
        height, width = image.shape[:2]
        for index in range(40):
            start_x = int(rng.integers(-width, width))
            thickness = int(rng.integers(8, 42))
            color = tuple(int(v) for v in palette[1 + index % (len(palette) - 1)])
            cv2.line(image, (start_x, height), (start_x + width, 0), color, thickness, cv2.LINE_AA)
        for _ in range(20):
            x1, y1 = int(rng.integers(0, width)), int(rng.integers(0, height))
            w, h = int(rng.integers(25, 110)), int(rng.integers(12, 55))
            color = tuple(int(v) for v in palette[int(rng.integers(1, len(palette)))])
            cv2.rectangle(image, (x1, y1), (min(width - 1, x1 + w), min(height - 1, y1 + h)), color, -1)

    @staticmethod
    def _circuits(image: np.ndarray, palette: np.ndarray, rng: np.random.Generator) -> None:
        height, width = image.shape[:2]
        grid = 32
        for index in range(36):
            x, y = int(rng.integers(0, width // grid)) * grid, int(rng.integers(0, height // grid)) * grid
            points = [(x, y)]
            for _ in range(int(rng.integers(2, 6))):
                if rng.random() < 0.5:
                    x = int(np.clip(x + rng.choice([-1, 1]) * grid * int(rng.integers(1, 4)), 0, width - 1))
                else:
                    y = int(np.clip(y + rng.choice([-1, 1]) * grid * int(rng.integers(1, 4)), 0, height - 1))
                points.append((x, y))
            color = tuple(int(v) for v in palette[1 + index % (len(palette) - 1)])
            cv2.polylines(image, [np.asarray(points, dtype=np.int32)], False, color, 4, cv2.LINE_AA)
            cv2.circle(image, points[-1], 7, color, -1, cv2.LINE_AA)


def build_texture_prompt(spec: DesignSpec) -> str:
    palette = ", ".join(spec.palette)
    prompt_motif = spec.prompt_motif or spec.motif
    if spec.refinement_directives:
        directives = "; ".join(spec.refinement_directives)
        return (
            f"Seamless tile. {spec.description}. {prompt_motif}; {palette}; "
            f"{directives}; no weapon"
        )
    return (
        f"Seamless repeating texture tile. {spec.description}. {prompt_motif} motif; "
        f"palette {palette}; flat uniform pattern; no object or weapon"
    )


class DiffusionTextureGenerator(TextureGenerator):
    """Lazy Diffusers backend selected for the 512 px / 8 GB VRAM acceptance gate."""

    def __init__(
        self,
        model_id: str = "stabilityai/sd-turbo",
        *,
        revision: str | None = "b261bac6fd2cf515557d5d0707481eafa0485ec2",
        device: str = "cuda",
        inference_steps: int = 2,
        pipeline: Any | None = None,
        pipeline_factory: Callable[..., Any] | None = None,
    ) -> None:
        if inference_steps < 1 or inference_steps > 4:
            raise ValueError("SD-Turbo acceptance backend supports 1 to 4 inference steps")
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self.inference_steps = inference_steps
        self._pipeline = pipeline
        self._pipeline_factory = pipeline_factory
        self._last_prompt: str | None = None
        self._last_seed: int | None = None
        self._peak_vram_gb: float | None = None
        self._resolved_revision: str | None = None
        self._last_prompt_tokens: int | None = None

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline

        import torch

        if self.device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("CUDA is required for the configured diffusion backend")
        if self._pipeline_factory is None:
            try:
                from diffusers import AutoPipelineForText2Image
            except ImportError as error:
                raise RuntimeError(
                    "Diffusers is not installed. Install the generation dependencies before running this backend."
                ) from error
            self._pipeline_factory = AutoPipelineForText2Image.from_pretrained

        kwargs: dict[str, Any] = {
            "torch_dtype": torch.float16 if self.device.startswith("cuda") else torch.float32,
            "use_safetensors": True,
        }
        if self.device.startswith("cuda"):
            kwargs["variant"] = "fp16"
        if self.revision:
            kwargs["revision"] = self.revision
        self._pipeline = self._pipeline_factory(self.model_id, **kwargs)
        self._pipeline.to(self.device)
        if hasattr(self._pipeline, "enable_attention_slicing"):
            self._pipeline.enable_attention_slicing()
        vae = getattr(self._pipeline, "vae", None)
        if vae is not None and hasattr(vae, "enable_slicing"):
            vae.enable_slicing()
        config = getattr(self._pipeline, "config", None)
        self._resolved_revision = getattr(config, "_commit_hash", None) or self.revision
        return self._pipeline

    def generate(self, spec: DesignSpec, seed: int) -> Image.Image:
        import torch

        pipeline = self._load_pipeline()
        prompt = build_texture_prompt(spec)
        tokenizer = getattr(pipeline, "tokenizer", None)
        if tokenizer is not None:
            encoded = tokenizer(prompt, truncation=False)
            input_ids = encoded["input_ids"]
            self._last_prompt_tokens = len(input_ids)
            maximum = int(getattr(tokenizer, "model_max_length", 77))
            if self._last_prompt_tokens > maximum:
                raise ValueError(
                    f"Texture prompt uses {self._last_prompt_tokens} tokens, exceeding the model limit of {maximum}"
                )
        if self.device.startswith("cuda"):
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(self.device)
        generator = torch.Generator(device=self.device).manual_seed(seed)
        result = pipeline(
            prompt=prompt,
            num_inference_steps=self.inference_steps,
            guidance_scale=0.0,
            height=spec.size,
            width=spec.size,
            generator=generator,
        )
        if self.device.startswith("cuda"):
            self._peak_vram_gb = torch.cuda.max_memory_allocated(self.device) / 1024**3
        self._last_prompt = prompt
        self._last_seed = seed
        return result.images[0].convert("RGB")

    def metadata(self) -> dict[str, Any]:
        return {
            "backend": type(self).__name__,
            "model_id": self.model_id,
            "requested_revision": self.revision,
            "resolved_revision": self._resolved_revision,
            "device": self.device,
            "dtype": "float16" if self.device.startswith("cuda") else "float32",
            "inference_steps": self.inference_steps,
            "guidance_scale": 0.0,
            "last_prompt": self._last_prompt,
            "last_prompt_tokens": self._last_prompt_tokens,
            "last_seed": self._last_seed,
            "peak_vram_gb": self._peak_vram_gb,
            "safety_checker_enabled": getattr(self._pipeline, "safety_checker", None) is not None
            if self._pipeline is not None
            else None,
        }
