from __future__ import annotations

import numpy as np
from PIL import Image


def seam_error(image: Image.Image, strip_width: int = 12) -> float:
    """Return periodic edge and gradient disagreement; lower is better."""
    array = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    strip_width = max(1, min(strip_width, array.shape[0] // 4, array.shape[1] // 4))

    edge_horizontal = np.mean(np.abs(array[:, 0] - array[:, -1]))
    edge_vertical = np.mean(np.abs(array[0, :] - array[-1, :]))

    left_gradient = np.mean(np.diff(array[:, : strip_width + 1], axis=1), axis=1)
    right_gradient = np.mean(np.diff(array[:, -strip_width - 1 :], axis=1), axis=1)
    top_gradient = np.mean(np.diff(array[: strip_width + 1, :], axis=0), axis=0)
    bottom_gradient = np.mean(np.diff(array[-strip_width - 1 :, :], axis=0), axis=0)
    gradient_horizontal = np.mean(np.abs(left_gradient - right_gradient))
    gradient_vertical = np.mean(np.abs(top_gradient - bottom_gradient))

    edge_loss = (edge_horizontal + edge_vertical) / 2.0
    gradient_loss = (gradient_horizontal + gradient_vertical) / 2.0
    return float(0.75 * edge_loss + 0.25 * gradient_loss)


def make_seamless(image: Image.Image) -> Image.Image:
    """Extract the periodic component with a frequency-domain Poisson solve.

    Boundary disagreement becomes a smooth, image-wide correction instead of a
    blurred or mirrored frame around the texture.
    """
    array = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
    height, width = array.shape[:2]
    boundary = np.zeros_like(array)
    boundary[0, :, :] = array[-1, :, :] - array[0, :, :]
    boundary[-1, :, :] = array[0, :, :] - array[-1, :, :]
    boundary[:, 0, :] += array[:, -1, :] - array[:, 0, :]
    boundary[:, -1, :] += array[:, 0, :] - array[:, -1, :]

    x = np.arange(width, dtype=np.float64)[None, :]
    y = np.arange(height, dtype=np.float64)[:, None]
    denominator = 2.0 * np.cos(2.0 * np.pi * x / width) + 2.0 * np.cos(2.0 * np.pi * y / height) - 4.0
    denominator[0, 0] = 1.0

    smooth = np.empty_like(array)
    for channel in range(3):
        spectrum = np.fft.fft2(boundary[..., channel]) / denominator
        spectrum[0, 0] = 0.0
        smooth[..., channel] = np.fft.ifft2(spectrum).real

    periodic = np.clip(array - smooth, 0.0, 1.0)
    return Image.fromarray(np.rint(periodic * 255.0).astype(np.uint8), mode="RGB")
