from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .preview import PreviewRenderer


@dataclass(frozen=True)
class ObjMesh:
    vertices: np.ndarray
    texcoords: np.ndarray
    vertex_faces: np.ndarray
    texture_faces: np.ndarray


def load_obj(path: Path) -> ObjMesh:
    """Load the vertex, UV and triangular face data used by Valve's geometry pack."""

    vertices: list[tuple[float, float, float]] = []
    texcoords: list[tuple[float, float]] = []
    vertex_faces: list[tuple[int, int, int]] = []
    texture_faces: list[tuple[int, int, int]] = []

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("v "):
                _, x, y, z = line.split()[:4]
                vertices.append((float(x), float(y), float(z)))
            elif line.startswith("vt "):
                _, u, v = line.split()[:3]
                texcoords.append((float(u), float(v)))
            elif line.startswith("f "):
                corners = line.split()[1:]
                if len(corners) < 3:
                    raise ValueError(f"OBJ face must contain at least three corners: {line.strip()}")
                parsed = [corner.split("/") for corner in corners]
                if any(len(parts) < 2 or not parts[1] for parts in parsed):
                    raise ValueError("Every face must include a UV index")
                vertex_polygon = [_resolve_obj_index(parts[0], len(vertices)) for parts in parsed]
                texture_polygon = [_resolve_obj_index(parts[1], len(texcoords)) for parts in parsed]
                for corner_index in range(1, len(corners) - 1):
                    triangle = (0, corner_index, corner_index + 1)
                    vertex_faces.append(tuple(vertex_polygon[index] for index in triangle))
                    texture_faces.append(tuple(texture_polygon[index] for index in triangle))

    if not vertices or not texcoords or not vertex_faces:
        raise ValueError(f"OBJ contains no renderable textured mesh: {path}")

    mesh = ObjMesh(
        vertices=np.asarray(vertices, dtype=np.float32),
        texcoords=np.asarray(texcoords, dtype=np.float32),
        vertex_faces=np.asarray(vertex_faces, dtype=np.int32),
        texture_faces=np.asarray(texture_faces, dtype=np.int32),
    )
    if mesh.vertex_faces.max() >= len(mesh.vertices):
        raise ValueError("OBJ face references a missing vertex")
    if mesh.texture_faces.max() >= len(mesh.texcoords):
        raise ValueError("OBJ face references a missing UV coordinate")
    return mesh


def _resolve_obj_index(value: str, current_count: int) -> int:
    index = int(value)
    if index == 0:
        raise ValueError("OBJ indices are one-based and cannot be zero")
    resolved = index - 1 if index > 0 else current_count + index
    if resolved < 0 or resolved >= current_count:
        raise ValueError(f"OBJ index {index} is outside the available range")
    return resolved


class ObjMultiViewRenderer(PreviewRenderer):
    """Fast UV preview renderer for the official Valve OBJ geometry.

    The default path uses barycentric per-pixel UV interpolation and a z-buffer.
    Legacy flat centroid sampling remains available as a diagnostic ablation. This
    is still a research preview, not a replacement for CS2 Workbench.
    """

    VIEWS = {
        "left": (np.array([1.0, 0.0, 0.0], dtype=np.float32), np.array([0.0, 1.0, 0.0], dtype=np.float32)),
        "right": (np.array([-1.0, 0.0, 0.0], dtype=np.float32), np.array([0.0, 1.0, 0.0], dtype=np.float32)),
        "top": (np.array([0.0, 1.0, 0.0], dtype=np.float32), np.array([1.0, 0.0, 0.0], dtype=np.float32)),
    }
    supports_multiview_scoring = True

    def __init__(
        self,
        model_path: Path,
        size: tuple[int, int] = (960, 540),
        sampling: str = "barycentric",
        uv_address_mode: str = "clamp",
    ) -> None:
        if sampling not in {"barycentric", "flat"}:
            raise ValueError("sampling must be 'barycentric' or 'flat'")
        if uv_address_mode not in {"clamp", "repeat", "discard_outside"}:
            raise ValueError(
                "uv_address_mode must be clamp, repeat, or discard_outside"
            )
        self.model_path = Path(model_path)
        self.size = size
        self.sampling = sampling
        self.uv_address_mode = uv_address_mode
        self.mesh = load_obj(self.model_path)

    def render(self, texture: Image.Image, output_dir: Path, stem: str) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        texture_rgb = np.asarray(texture.convert("RGB"), dtype=np.uint8)
        paths: list[Path] = []
        rendered: list[Image.Image] = []

        for view_name, (forward, up_hint) in self.VIEWS.items():
            frame = self._render_view(texture_rgb, forward, up_hint)
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            path = output_dir / f"{stem}_{view_name}.png"
            image.save(path)
            paths.append(path)
            rendered.append(image)

        sheet = self._contact_sheet(rendered)
        sheet_path = output_dir / f"{stem}_multiview.png"
        sheet.save(sheet_path)
        paths.append(sheet_path)
        return paths

    def _render_view(self, texture: np.ndarray, forward: np.ndarray, up_hint: np.ndarray) -> np.ndarray:
        if self.sampling == "flat":
            return self._render_view_flat(texture, forward, up_hint)
        return self._render_view_barycentric(texture, forward, up_hint)

    def _render_view_flat(
        self, texture: np.ndarray, forward: np.ndarray, up_hint: np.ndarray
    ) -> np.ndarray:
        width, height = self.size
        background = np.zeros((height, width, 3), dtype=np.uint8)
        background[:] = (31, 29, 27)

        forward = forward / np.linalg.norm(forward)
        right = np.cross(up_hint, forward)
        right /= np.linalg.norm(right)
        up = np.cross(forward, right)

        centered = self.mesh.vertices - self.mesh.vertices.mean(axis=0, keepdims=True)
        projected = np.column_stack((centered @ right, centered @ up))
        depth = centered @ forward

        span = np.maximum(projected.max(axis=0) - projected.min(axis=0), 1e-6)
        scale = min((width * 0.88) / span[0], (height * 0.82) / span[1])
        screen = projected * scale
        screen[:, 0] += width / 2
        screen[:, 1] = height / 2 - screen[:, 1]

        face_vertices = self.mesh.vertices[self.mesh.vertex_faces]
        normals = np.cross(face_vertices[:, 1] - face_vertices[:, 0], face_vertices[:, 2] - face_vertices[:, 0])
        normal_length = np.linalg.norm(normals, axis=1, keepdims=True)
        normals /= np.maximum(normal_length, 1e-8)
        light = np.array([0.35, 0.75, 0.55], dtype=np.float32)
        light /= np.linalg.norm(light)
        shade = 0.55 + 0.45 * np.abs(normals @ light)

        raw_uv = self.mesh.texcoords[self.mesh.texture_faces].mean(axis=1)
        paintable = self._uv_is_paintable(raw_uv)
        uv = self._address_uv(raw_uv)
        texture_height, texture_width = texture.shape[:2]
        texture_x = np.clip(np.rint(uv[:, 0] * (texture_width - 1)), 0, texture_width - 1).astype(np.int32)
        texture_y = np.clip(np.rint((1.0 - uv[:, 1]) * (texture_height - 1)), 0, texture_height - 1).astype(np.int32)
        colors = texture[texture_y, texture_x].astype(np.float32) * shade[:, None]
        colors[~paintable] = np.asarray((18, 18, 18), dtype=np.float32)
        colors = np.clip(colors, 0, 255).astype(np.uint8)[:, ::-1]

        face_depth = depth[self.mesh.vertex_faces].mean(axis=1)
        for face_index in np.argsort(face_depth):
            polygon = np.rint(screen[self.mesh.vertex_faces[face_index]]).astype(np.int32)
            if abs(cv2.contourArea(polygon)) < 0.25:
                continue
            cv2.fillConvexPoly(background, polygon, colors[face_index].tolist(), lineType=cv2.LINE_AA)

        return background

    def _render_view_barycentric(
        self, texture: np.ndarray, forward: np.ndarray, up_hint: np.ndarray
    ) -> np.ndarray:
        width, height = self.size
        background = np.zeros((height, width, 3), dtype=np.uint8)
        background[:] = (31, 29, 27)
        z_buffer = np.full((height, width), -np.inf, dtype=np.float32)

        forward = forward / np.linalg.norm(forward)
        right = np.cross(up_hint, forward)
        right /= np.linalg.norm(right)
        up = np.cross(forward, right)

        centered = self.mesh.vertices - self.mesh.vertices.mean(axis=0, keepdims=True)
        projected = np.column_stack((centered @ right, centered @ up))
        depth = centered @ forward
        span = np.maximum(projected.max(axis=0) - projected.min(axis=0), 1e-6)
        scale = min((width * 0.88) / span[0], (height * 0.82) / span[1])
        screen = projected * scale
        screen[:, 0] += width / 2
        screen[:, 1] = height / 2 - screen[:, 1]

        face_vertices = self.mesh.vertices[self.mesh.vertex_faces]
        normals = np.cross(
            face_vertices[:, 1] - face_vertices[:, 0],
            face_vertices[:, 2] - face_vertices[:, 0],
        )
        normal_length = np.linalg.norm(normals, axis=1, keepdims=True)
        normals /= np.maximum(normal_length, 1e-8)
        light = np.array([0.35, 0.75, 0.55], dtype=np.float32)
        light /= np.linalg.norm(light)
        shade = 0.55 + 0.45 * np.abs(normals @ light)

        texture_height, texture_width = texture.shape[:2]
        for face_index, (vertex_face, texture_face) in enumerate(
            zip(self.mesh.vertex_faces, self.mesh.texture_faces, strict=True)
        ):
            triangle = screen[vertex_face]
            minimum = np.maximum(np.floor(triangle.min(axis=0)).astype(np.int32), 0)
            maximum = np.minimum(
                np.ceil(triangle.max(axis=0)).astype(np.int32),
                (width - 1, height - 1),
            )
            if np.any(maximum < minimum):
                continue
            x0, y0 = triangle[0]
            x1, y1 = triangle[1]
            x2, y2 = triangle[2]
            denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(float(denominator)) < 1e-8:
                continue
            grid_x, grid_y = np.meshgrid(
                np.arange(minimum[0], maximum[0] + 1, dtype=np.float32) + 0.5,
                np.arange(minimum[1], maximum[1] + 1, dtype=np.float32) + 0.5,
            )
            weight_0 = (
                (y1 - y2) * (grid_x - x2) + (x2 - x1) * (grid_y - y2)
            ) / denominator
            weight_1 = (
                (y2 - y0) * (grid_x - x2) + (x0 - x2) * (grid_y - y2)
            ) / denominator
            weight_2 = 1.0 - weight_0 - weight_1
            inside = (
                (weight_0 >= -1e-5)
                & (weight_1 >= -1e-5)
                & (weight_2 >= -1e-5)
            )
            if not np.any(inside):
                continue
            weights = np.stack((weight_0, weight_1, weight_2), axis=-1)
            interpolated_depth = weights @ depth[vertex_face]
            y_slice = slice(minimum[1], maximum[1] + 1)
            x_slice = slice(minimum[0], maximum[0] + 1)
            z_region = z_buffer[y_slice, x_slice]
            visible = inside & (interpolated_depth > z_region)
            if not np.any(visible):
                continue
            raw_interpolated_uv = weights @ self.mesh.texcoords[texture_face]
            paintable = self._uv_is_paintable(raw_interpolated_uv)
            interpolated_uv = self._address_uv(raw_interpolated_uv)
            tex_x = np.clip(
                interpolated_uv[..., 0] * (texture_width - 1),
                0,
                texture_width - 1,
            )
            tex_y = np.clip(
                (1.0 - interpolated_uv[..., 1]) * (texture_height - 1),
                0,
                texture_height - 1,
            )
            colors = _bilinear_sample(texture, tex_x, tex_y)
            colors = np.clip(colors * shade[face_index], 0, 255).astype(np.uint8)
            colors[~paintable] = (18, 18, 18)
            frame_region = background[y_slice, x_slice]
            frame_region[visible] = colors[visible, ::-1]
            z_region[visible] = interpolated_depth[visible]

        return background

    def _address_uv(self, uv: np.ndarray) -> np.ndarray:
        if self.uv_address_mode == "repeat":
            return np.mod(uv, 1.0)
        return np.clip(uv, 0.0, 1.0)

    def _uv_is_paintable(self, uv: np.ndarray) -> np.ndarray:
        if self.uv_address_mode != "discard_outside":
            return np.ones(uv.shape[:-1], dtype=bool)
        return np.all((uv >= 0.0) & (uv <= 1.0), axis=-1)

    def _contact_sheet(self, images: list[Image.Image]) -> Image.Image:
        thumb_width = 480
        thumb_height = 270
        canvas = Image.new("RGB", (thumb_width * len(images), thumb_height + 42), "#1B1D1F")
        draw = ImageDraw.Draw(canvas)
        for index, (name, image) in enumerate(zip(self.VIEWS, images, strict=True)):
            thumb = image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            canvas.paste(thumb, (index * thumb_width, 0))
            draw.text((index * thumb_width + 16, thumb_height + 11), name.upper(), fill="#E8EAED")
        return canvas


def _bilinear_sample(texture: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.minimum(x0 + 1, texture.shape[1] - 1)
    y1 = np.minimum(y0 + 1, texture.shape[0] - 1)
    fraction_x = (x - x0)[..., None]
    fraction_y = (y - y0)[..., None]
    top = texture[y0, x0].astype(np.float32) * (1.0 - fraction_x) + texture[
        y0, x1
    ].astype(np.float32) * fraction_x
    bottom = texture[y1, x0].astype(np.float32) * (1.0 - fraction_x) + texture[
        y1, x1
    ].astype(np.float32) * fraction_x
    return top * (1.0 - fraction_y) + bottom * fraction_y
