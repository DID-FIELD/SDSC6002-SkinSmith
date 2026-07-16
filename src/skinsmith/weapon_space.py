from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from .obj_renderer import ObjMesh


@dataclass(frozen=True)
class CanonicalWeaponFrame:
    longitudinal_axis: tuple[float, float, float]
    up_axis: tuple[float, float, float]
    side_axis: tuple[float, float, float]
    bounds_min: tuple[float, float, float]
    bounds_max: tuple[float, float, float]

    @classmethod
    def from_mesh(
        cls,
        mesh: ObjMesh,
        longitudinal_axis: tuple[float, float, float],
        up_axis: tuple[float, float, float],
    ) -> "CanonicalWeaponFrame":
        longitudinal = _normalized(np.asarray(longitudinal_axis, dtype=np.float64))
        up = np.asarray(up_axis, dtype=np.float64)
        up = _normalized(up - np.dot(up, longitudinal) * longitudinal)
        side = _normalized(np.cross(up, longitudinal))
        basis = np.stack((longitudinal, up, side), axis=1)
        projected = mesh.vertices.astype(np.float64) @ basis
        return cls(
            longitudinal_axis=tuple(float(value) for value in longitudinal),
            up_axis=tuple(float(value) for value in up),
            side_axis=tuple(float(value) for value in side),
            bounds_min=tuple(float(value) for value in projected.min(axis=0)),
            bounds_max=tuple(float(value) for value in projected.max(axis=0)),
        )

    def normalized_coordinates(self, points: np.ndarray) -> np.ndarray:
        basis = np.stack(
            (
                np.asarray(self.longitudinal_axis),
                np.asarray(self.up_axis),
                np.asarray(self.side_axis),
            ),
            axis=1,
        )
        projected = points.astype(np.float64) @ basis
        minimum = np.asarray(self.bounds_min)
        span = np.maximum(np.asarray(self.bounds_max) - minimum, 1e-8)
        return np.clip((projected - minimum) / span, 0.0, 1.0).astype(np.float32)

    def normals_to_canonical(self, normals: np.ndarray) -> np.ndarray:
        basis = np.stack(
            (
                np.asarray(self.longitudinal_axis),
                np.asarray(self.up_axis),
                np.asarray(self.side_axis),
            ),
            axis=1,
        )
        transformed = normals.astype(np.float64) @ basis
        length = np.linalg.norm(transformed, axis=1, keepdims=True)
        return (transformed / np.maximum(length, 1e-8)).astype(np.float32)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class UVGeometryMaps:
    canonical_position: np.ndarray
    canonical_normal: np.ndarray
    valid_mask: np.ndarray
    face_index: np.ndarray
    coverage_count: np.ndarray

    def statistics(self) -> dict[str, float | int]:
        valid = self.valid_mask
        return {
            "size": int(valid.shape[0]),
            "valid_pixel_count": int(np.count_nonzero(valid)),
            "valid_pixel_fraction": float(np.count_nonzero(valid)) / valid.size,
            "overlap_pixel_count": int(np.count_nonzero(self.coverage_count > 1)),
            "overlap_pixel_fraction": float(np.count_nonzero(self.coverage_count > 1))
            / valid.size,
            "maximum_coverage_count": int(self.coverage_count.max()),
        }


@dataclass(frozen=True)
class WeaponSpaceLayerSpec:
    """Placement and blending rules for generated content in continuous weapon space."""

    layer_id: str
    surfaces: tuple[str, ...]
    center: tuple[float, float]
    size: tuple[float, float]
    rotation_degrees: float
    opacity: float
    blend_mode: str
    fit_mode: str
    mirror_on_right: bool
    feather_fraction: float
    source_crop: tuple[float, float, float, float] | None

    @classmethod
    def from_dict(cls, data: dict) -> "WeaponSpaceLayerSpec":
        layer = cls(
            layer_id=str(data["layer_id"]),
            surfaces=tuple(str(value) for value in data["surfaces"]),
            center=tuple(float(value) for value in data.get("center", (0.5, 0.5))),
            size=tuple(float(value) for value in data.get("size", (1.0, 1.0))),
            rotation_degrees=float(data.get("rotation_degrees", 0.0)),
            opacity=float(data.get("opacity", 1.0)),
            blend_mode=str(data.get("blend_mode", "normal")),
            fit_mode=str(data.get("fit_mode", "cover")),
            mirror_on_right=bool(data.get("mirror_on_right", False)),
            feather_fraction=float(data.get("feather_fraction", 0.0)),
            source_crop=(
                tuple(float(value) for value in data["source_crop"])
                if "source_crop" in data
                else None
            ),
        )
        layer.validate()
        return layer

    def validate(self) -> None:
        valid_surfaces = {"left", "right", "top"}
        if not self.layer_id:
            raise ValueError("Weapon-space layer_id cannot be empty")
        if not self.surfaces or not set(self.surfaces) <= valid_surfaces:
            raise ValueError("Weapon-space surfaces must use left, right, or top")
        if len(self.center) != 2 or not all(0.0 <= value <= 1.0 for value in self.center):
            raise ValueError("Weapon-space layer center must contain two normalized values")
        if len(self.size) != 2 or not all(0.0 < value <= 2.0 for value in self.size):
            raise ValueError("Weapon-space layer size must be in (0, 2]")
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError("Weapon-space layer opacity must be in [0, 1]")
        if self.blend_mode not in {"normal", "screen", "multiply"}:
            raise ValueError("Unsupported weapon-space blend mode")
        if self.fit_mode not in {"cover", "contain", "stretch"}:
            raise ValueError("Unsupported weapon-space fit mode")
        if not 0.0 <= self.feather_fraction <= 0.5:
            raise ValueError("Weapon-space feather_fraction must be in [0, 0.5]")
        if self.source_crop is not None:
            if len(self.source_crop) != 4:
                raise ValueError("source_crop must contain left, top, right, bottom")
            left, top, right, bottom = self.source_crop
            if not (0.0 <= left < right <= 1.0 and 0.0 <= top < bottom <= 1.0):
                raise ValueError("source_crop must be a valid normalized box")


@dataclass(frozen=True)
class WeaponDesignPlan:
    plan_id: str
    description: str
    palette: tuple[tuple[int, int, int], ...]
    canvas_size: tuple[int, int]
    focal_center: tuple[float, float]
    focal_radius: tuple[float, float]
    flow_center: float
    flow_amplitude: float
    flow_cycles: float
    flow_thicknesses: tuple[int, ...]
    quiet_start: float
    quiet_strength: float
    secondary_anchors: tuple[tuple[float, float], ...]
    projection_blend_power: float
    content_layers: tuple[WeaponSpaceLayerSpec, ...]

    @classmethod
    def load(cls, path: Path) -> "WeaponDesignPlan":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "WeaponDesignPlan":
        return cls(
            plan_id=str(data["plan_id"]),
            description=str(data["description"]),
            palette=tuple(_hex_to_rgb(value) for value in data["palette"]),
            canvas_size=tuple(int(value) for value in data["canvas_size"]),
            focal_center=tuple(float(value) for value in data["focal_center"]),
            focal_radius=tuple(float(value) for value in data["focal_radius"]),
            flow_center=float(data["flow_center"]),
            flow_amplitude=float(data["flow_amplitude"]),
            flow_cycles=float(data["flow_cycles"]),
            flow_thicknesses=tuple(int(value) for value in data["flow_thicknesses"]),
            quiet_start=float(data["quiet_start"]),
            quiet_strength=float(data["quiet_strength"]),
            secondary_anchors=tuple(
                tuple(float(value) for value in anchor) for anchor in data["secondary_anchors"]
            ),
            projection_blend_power=float(data.get("projection_blend_power", 4.0)),
            content_layers=tuple(
                WeaponSpaceLayerSpec.from_dict(layer)
                for layer in data.get("content_layers", ())
            ),
        )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["palette"] = [list(color) for color in self.palette]
        return data


def bake_uv_geometry_maps(
    mesh: ObjMesh,
    frame: CanonicalWeaponFrame,
    size: int,
    uv_address_mode: str = "clamp",
) -> UVGeometryMaps:
    """Rasterize interpolated object-space position and normal into the UV atlas."""

    if size < 32:
        raise ValueError("UV geometry-map size must be at least 32")
    if uv_address_mode not in {"clamp", "repeat", "discard_outside"}:
        raise ValueError(
            "uv_address_mode must be clamp, repeat, or discard_outside"
        )
    positions = frame.normalized_coordinates(mesh.vertices)
    normals = frame.normals_to_canonical(_vertex_normals(mesh))
    position_map = np.zeros((size, size, 3), dtype=np.float32)
    normal_map = np.zeros((size, size, 3), dtype=np.float32)
    face_map = np.full((size, size), -1, dtype=np.int32)
    coverage = np.zeros((size, size), dtype=np.uint16)

    for face_index, (vertex_face, texture_face) in enumerate(
        zip(mesh.vertex_faces, mesh.texture_faces, strict=True)
    ):
        for uv_triangle in _addressed_uv_triangles(
            mesh.texcoords[texture_face], uv_address_mode
        ):
            triangle = np.column_stack(
                (
                    uv_triangle[:, 0] * (size - 1),
                    (1.0 - uv_triangle[:, 1]) * (size - 1),
                )
            ).astype(np.float32)
            _rasterize_geometry_triangle(
                triangle,
                face_index,
                vertex_face,
                positions,
                normals,
                position_map,
                normal_map,
                face_map,
                coverage,
            )

    return UVGeometryMaps(
        canonical_position=position_map,
        canonical_normal=normal_map,
        valid_mask=face_map >= 0,
        face_index=face_map,
        coverage_count=coverage,
    )


def _addressed_uv_triangles(
    triangle: np.ndarray, uv_address_mode: str
) -> tuple[np.ndarray, ...]:
    triangle = triangle.astype(np.float32)
    if uv_address_mode == "clamp":
        return (triangle,)
    if uv_address_mode == "discard_outside":
        if np.all((triangle >= 0.0) & (triangle <= 1.0)):
            return (triangle,)
        return ()
    local = triangle - np.floor(triangle.mean(axis=0, keepdims=True))
    addressed: list[np.ndarray] = []
    for shift_x in (-1.0, 0.0, 1.0):
        for shift_y in (-1.0, 0.0, 1.0):
            shifted = local + (shift_x, shift_y)
            if (
                shifted[:, 0].max() >= 0.0
                and shifted[:, 0].min() <= 1.0
                and shifted[:, 1].max() >= 0.0
                and shifted[:, 1].min() <= 1.0
            ):
                addressed.append(shifted)
    return tuple(addressed)


def _rasterize_geometry_triangle(
    triangle: np.ndarray,
    face_index: int,
    vertex_face: np.ndarray,
    positions: np.ndarray,
    normals: np.ndarray,
    position_map: np.ndarray,
    normal_map: np.ndarray,
    face_map: np.ndarray,
    coverage: np.ndarray,
) -> None:
        size = face_map.shape[0]
        minimum = np.maximum(np.floor(triangle.min(axis=0)).astype(int), 0)
        maximum = np.minimum(np.ceil(triangle.max(axis=0)).astype(int), size - 1)
        if np.any(maximum < minimum):
            return
        x0, y0 = triangle[0]
        x1, y1 = triangle[1]
        x2, y2 = triangle[2]
        denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(float(denominator)) < 1e-10:
            return
        grid_x, grid_y = np.meshgrid(
            np.arange(minimum[0], maximum[0] + 1, dtype=np.float32),
            np.arange(minimum[1], maximum[1] + 1, dtype=np.float32),
        )
        weight_0 = ((y1 - y2) * (grid_x - x2) + (x2 - x1) * (grid_y - y2)) / denominator
        weight_1 = ((y2 - y0) * (grid_x - x2) + (x0 - x2) * (grid_y - y2)) / denominator
        weight_2 = 1.0 - weight_0 - weight_1
        inside = (weight_0 >= -1e-5) & (weight_1 >= -1e-5) & (weight_2 >= -1e-5)
        if not np.any(inside):
            return
        weights = np.stack((weight_0, weight_1, weight_2), axis=-1)
        interpolated_position = weights @ positions[vertex_face]
        interpolated_normal = weights @ normals[vertex_face]
        normal_length = np.linalg.norm(interpolated_normal, axis=-1, keepdims=True)
        interpolated_normal /= np.maximum(normal_length, 1e-8)
        y_slice = slice(minimum[1], maximum[1] + 1)
        x_slice = slice(minimum[0], maximum[0] + 1)
        position_region = position_map[y_slice, x_slice]
        normal_region = normal_map[y_slice, x_slice]
        face_region = face_map[y_slice, x_slice]
        coverage_region = coverage[y_slice, x_slice]
        position_region[inside] = interpolated_position[inside]
        normal_region[inside] = interpolated_normal[inside]
        face_region[inside] = face_index
        coverage_region[inside] += 1


def render_weapon_space_canvases(
    plan: WeaponDesignPlan,
    content_images: Mapping[str, Image.Image] | None = None,
) -> dict[str, Image.Image]:
    """Create coherent canonical side/top designs before any UV fragmentation."""

    width, height = plan.canvas_size
    left = _render_side_canvas(plan, width, height, phase=0.0)
    right = _render_side_canvas(plan, width, height, phase=np.pi * 0.28)
    top = _render_top_canvas(plan, width, height)
    canvases = {
        "left": Image.fromarray(left, mode="RGB"),
        "right": Image.fromarray(right, mode="RGB"),
        "top": Image.fromarray(top, mode="RGB"),
    }
    if plan.content_layers:
        if content_images is None:
            raise ValueError("WeaponDesignPlan requires content_images for configured layers")
        canvases = compose_weapon_space_layers(
            canvases, plan.content_layers, content_images
        )
    return canvases


def compose_weapon_space_layers(
    canvases: Mapping[str, Image.Image],
    layers: tuple[WeaponSpaceLayerSpec, ...],
    content_images: Mapping[str, Image.Image],
) -> dict[str, Image.Image]:
    """Place generated assets on canonical canvases, never directly in UV coordinates."""

    result = {name: image.convert("RGB").copy() for name, image in canvases.items()}
    if set(result) != {"left", "right", "top"}:
        raise ValueError("Weapon-space canvases must contain left, right, and top")
    for layer in layers:
        layer.validate()
        if layer.layer_id not in content_images:
            raise KeyError(f"Missing content image for layer {layer.layer_id!r}")
        source = content_images[layer.layer_id].convert("RGBA")
        if layer.source_crop is not None:
            left, top, right, bottom = layer.source_crop
            source = source.crop(
                (
                    int(round(left * source.width)),
                    int(round(top * source.height)),
                    int(round(right * source.width)),
                    int(round(bottom * source.height)),
                )
            )
        for surface in layer.surfaces:
            surface_source = (
                ImageOps.mirror(source)
                if surface == "right" and layer.mirror_on_right
                else source
            )
            result[surface] = _place_content_layer(
                result[surface], surface_source, layer
            )
    return result


def bake_weapon_space_texture(
    maps: UVGeometryMaps,
    canvases: dict[str, Image.Image],
    base_color: tuple[int, int, int],
    projection_blend_power: float = 4.0,
) -> Image.Image:
    """Sample coherent weapon-space canvases into fragmented UV storage."""

    if projection_blend_power <= 0:
        raise ValueError("projection_blend_power must be positive")

    side_left = np.asarray(canvases["left"].convert("RGB"), dtype=np.uint8)
    side_right = np.asarray(canvases["right"].convert("RGB"), dtype=np.uint8)
    top = np.asarray(canvases["top"].convert("RGB"), dtype=np.uint8)
    position = maps.canonical_position
    normal = maps.canonical_normal
    side_x = position[..., 0] * (side_left.shape[1] - 1)
    side_y = (1.0 - position[..., 1]) * (side_left.shape[0] - 1)
    top_x = position[..., 0] * (top.shape[1] - 1)
    top_y = (1.0 - position[..., 2]) * (top.shape[0] - 1)
    left_sample = cv2.remap(side_left, side_x, side_y, cv2.INTER_LINEAR)
    right_sample = cv2.remap(side_right, side_x, side_y, cv2.INTER_LINEAR)
    top_sample = cv2.remap(top, top_x, top_y, cv2.INTER_LINEAR)
    normal_side = normal[..., 2]
    use_left = normal_side < 0
    side_fallback = np.abs(normal_side) < 1e-5
    use_left = np.where(side_fallback, position[..., 2] < 0.5, use_left)
    side_sample = np.where(use_left[..., None], left_sample, right_sample)
    side_weight = np.abs(normal_side) ** projection_blend_power
    top_weight = np.abs(normal[..., 1]) ** projection_blend_power
    weight_sum = side_weight + top_weight
    end_surface = weight_sum < 1e-8
    side_weight[end_surface] = 1.0
    weight_sum[end_surface] = 1.0
    sampled = (
        side_sample.astype(np.float32) * side_weight[..., None]
        + top_sample.astype(np.float32) * top_weight[..., None]
    ) / weight_sum[..., None]
    sampled = np.rint(np.clip(sampled, 0, 255)).astype(np.uint8)
    output = np.empty_like(sampled, dtype=np.uint8)
    output[:] = base_color
    output[maps.valid_mask] = sampled[maps.valid_mask]
    return Image.fromarray(output, mode="RGB")


def _place_content_layer(
    base: Image.Image,
    source: Image.Image,
    layer: WeaponSpaceLayerSpec,
) -> Image.Image:
    canvas = base.convert("RGB")
    target_size = (
        max(1, int(round(canvas.width * layer.size[0]))),
        max(1, int(round(canvas.height * layer.size[1]))),
    )
    if layer.fit_mode == "cover":
        placed = ImageOps.fit(source, target_size, method=Image.Resampling.LANCZOS)
    elif layer.fit_mode == "contain":
        contained = ImageOps.contain(source, target_size, method=Image.Resampling.LANCZOS)
        placed = Image.new("RGBA", target_size, (0, 0, 0, 0))
        placed.alpha_composite(
            contained,
            ((target_size[0] - contained.width) // 2, (target_size[1] - contained.height) // 2),
        )
    else:
        placed = source.resize(target_size, Image.Resampling.LANCZOS)
    if layer.rotation_degrees:
        placed = placed.rotate(
            layer.rotation_degrees,
            resample=Image.Resampling.BICUBIC,
            expand=True,
        )
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    x = int(round(layer.center[0] * canvas.width - placed.width / 2))
    y = int(round(layer.center[1] * canvas.height - placed.height / 2))
    overlay.alpha_composite(placed, (x, y))
    overlay_array = np.asarray(overlay, dtype=np.float32)
    base_array = np.asarray(canvas, dtype=np.float32)
    alpha = overlay_array[..., 3] / 255.0 * layer.opacity
    if layer.feather_fraction > 0:
        alpha *= _edge_feather(canvas.size, layer.center, layer.size, layer.feather_fraction)
    source_rgb = overlay_array[..., :3]
    if layer.blend_mode == "screen":
        blended = 255.0 - (255.0 - base_array) * (255.0 - source_rgb) / 255.0
    elif layer.blend_mode == "multiply":
        blended = base_array * source_rgb / 255.0
    else:
        blended = source_rgb
    result = base_array * (1.0 - alpha[..., None]) + blended * alpha[..., None]
    return Image.fromarray(np.rint(np.clip(result, 0, 255)).astype(np.uint8), mode="RGB")


def _edge_feather(
    canvas_size: tuple[int, int],
    center: tuple[float, float],
    size: tuple[float, float],
    feather_fraction: float,
) -> np.ndarray:
    width, height = canvas_size
    x = (np.arange(width, dtype=np.float32) + 0.5) / width
    y = (np.arange(height, dtype=np.float32) + 0.5) / height
    left = center[0] - size[0] / 2
    top = center[1] - size[1] / 2
    local_x = (x - left) / size[0]
    local_y = (y - top) / size[1]
    distance_x = np.minimum(local_x, 1.0 - local_x)
    distance_y = np.minimum(local_y, 1.0 - local_y)
    distance = np.minimum(distance_y[:, None], distance_x[None, :])
    return np.clip(distance / feather_fraction, 0.0, 1.0)


def geometry_map_diagnostics(maps: UVGeometryMaps) -> dict[str, Image.Image]:
    position = np.rint(np.clip(maps.canonical_position, 0, 1) * 255).astype(np.uint8)
    normal = np.rint(np.clip(maps.canonical_normal * 0.5 + 0.5, 0, 1) * 255).astype(np.uint8)
    position[~maps.valid_mask] = 0
    normal[~maps.valid_mask] = 0
    side = np.zeros((*maps.valid_mask.shape, 3), dtype=np.uint8)
    side[(maps.canonical_position[..., 2] < 0.5) & maps.valid_mask] = (55, 156, 240)
    side[(maps.canonical_position[..., 2] >= 0.5) & maps.valid_mask] = (235, 92, 116)
    use_top = np.abs(maps.canonical_normal[..., 1]) > np.abs(maps.canonical_normal[..., 2])
    side[use_top & maps.valid_mask] = (238, 190, 58)
    return {
        "uv_position_map": Image.fromarray(position, mode="RGB"),
        "uv_normal_map": Image.fromarray(normal, mode="RGB"),
        "uv_surface_chart": Image.fromarray(side, mode="RGB"),
        "uv_valid_mask": Image.fromarray(maps.valid_mask.astype(np.uint8) * 255, mode="L"),
    }


def _vertex_normals(mesh: ObjMesh) -> np.ndarray:
    face_vertices = mesh.vertices[mesh.vertex_faces].astype(np.float64)
    face_normals = np.cross(
        face_vertices[:, 1] - face_vertices[:, 0],
        face_vertices[:, 2] - face_vertices[:, 0],
    )
    normals = np.zeros_like(mesh.vertices, dtype=np.float64)
    for corner in range(3):
        np.add.at(normals, mesh.vertex_faces[:, corner], face_normals)
    length = np.linalg.norm(normals, axis=1, keepdims=True)
    return (normals / np.maximum(length, 1e-8)).astype(np.float32)


def _render_side_canvas(
    plan: WeaponDesignPlan, width: int, height: int, phase: float
) -> np.ndarray:
    base = np.asarray(plan.palette[0], dtype=np.float32)
    accent = np.asarray(plan.palette[1], dtype=np.float32)
    secondary = np.asarray(plan.palette[2], dtype=np.float32)
    highlight = np.asarray(plan.palette[3], dtype=np.float32)
    x_normalized = np.linspace(0, 1, width, dtype=np.float32)
    gradient = (0.12 + 0.18 * np.sin(np.pi * x_normalized))[None, :, None]
    canvas = np.broadcast_to(base, (height, width, 3)).copy()
    canvas = canvas * (1.0 - gradient) + secondary * gradient
    canvas = np.clip(canvas, 0, 255).astype(np.uint8)
    x = np.arange(width, dtype=np.float32)
    center = plan.flow_center * height
    for index, thickness in enumerate(plan.flow_thicknesses):
        offset = (index - (len(plan.flow_thicknesses) - 1) / 2) * height * 0.055
        y = center + offset + plan.flow_amplitude * height * np.sin(
            plan.flow_cycles * 2 * np.pi * x / width + phase + index * 0.42
        )
        points = np.column_stack((x, y)).astype(np.int32)
        color = tuple(int(value) for value in (accent if index % 2 == 0 else secondary))
        cv2.polylines(canvas, [points], False, color, thickness, cv2.LINE_AA)
    focal = (
        int(plan.focal_center[0] * width),
        int((1.0 - plan.focal_center[1]) * height),
    )
    radius = (int(plan.focal_radius[0] * width), int(plan.focal_radius[1] * height))
    for scale, color, thickness in (
        (1.0, secondary, -1),
        (0.72, accent, -1),
        (0.43, highlight, -1),
        (0.18, base, -1),
    ):
        axes = (max(1, int(radius[0] * scale)), max(1, int(radius[1] * scale)))
        cv2.ellipse(canvas, focal, axes, -14, 0, 360, tuple(int(v) for v in color), thickness, cv2.LINE_AA)
    for anchor_index, anchor in enumerate(plan.secondary_anchors):
        point = (int(anchor[0] * width), int((1.0 - anchor[1]) * height))
        color = accent if anchor_index % 2 == 0 else highlight
        cv2.circle(canvas, point, max(5, height // 48), tuple(int(v) for v in color), -1, cv2.LINE_AA)
        cv2.circle(canvas, point, max(8, height // 28), tuple(int(v) for v in color), 3, cv2.LINE_AA)
    quiet_start = int(plan.quiet_start * width)
    if quiet_start < width:
        fade = np.linspace(0, plan.quiet_strength, width - quiet_start, dtype=np.float32)[None, :, None]
        canvas[:, quiet_start:] = np.clip(
            canvas[:, quiet_start:].astype(np.float32) * (1.0 - fade) + base * fade,
            0,
            255,
        ).astype(np.uint8)
    return canvas


def _render_top_canvas(plan: WeaponDesignPlan, width: int, height: int) -> np.ndarray:
    canvas = np.empty((height, width, 3), dtype=np.uint8)
    canvas[:] = plan.palette[0]
    x = np.arange(width, dtype=np.float32)
    for index, fraction in enumerate((0.38, 0.5, 0.62)):
        y = fraction * height + 0.035 * height * np.sin(2 * np.pi * x / width + index)
        points = np.column_stack((x, y)).astype(np.int32)
        cv2.polylines(
            canvas,
            [points],
            False,
            plan.palette[1 + index % 2],
            max(4, plan.flow_thicknesses[min(index, len(plan.flow_thicknesses) - 1)] // 2),
            cv2.LINE_AA,
        )
    focal_x = int(plan.focal_center[0] * width)
    cv2.circle(canvas, (focal_x, height // 2), height // 8, plan.palette[3], -1, cv2.LINE_AA)
    cv2.circle(canvas, (focal_x, height // 2), height // 14, plan.palette[1], -1, cv2.LINE_AA)
    return canvas


def _normalized(vector: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    if length <= 1e-10:
        raise ValueError("Canonical axis cannot be zero or parallel to another axis")
    return vector / length


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))
