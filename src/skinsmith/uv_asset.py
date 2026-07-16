from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from PIL import Image

from .asset_spec import SemanticRegionSpec
from .obj_renderer import ObjMesh, load_obj


@dataclass(frozen=True)
class UVSeamPair:
    vertex_indices: tuple[int, int]
    uv_indices_a: tuple[int, int]
    uv_indices_b: tuple[int, int]
    face_indices: tuple[int, int]

    def to_dict(self) -> dict:
        return asdict(self)


class _DisjointSet:
    def __init__(self, count: int) -> None:
        self.parent = list(range(count))
        self.rank = [0] * count

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1


def face_components(faces: np.ndarray) -> tuple[np.ndarray, ...]:
    """Return face components connected through a shared undirected edge."""

    disjoint = _DisjointSet(len(faces))
    edge_owner: dict[tuple[int, int], int] = {}
    for face_index, face in enumerate(faces):
        for start, end in ((0, 1), (1, 2), (2, 0)):
            edge = tuple(sorted((int(face[start]), int(face[end]))))
            owner = edge_owner.setdefault(edge, face_index)
            disjoint.union(face_index, owner)

    grouped: dict[int, list[int]] = {}
    for face_index in range(len(faces)):
        grouped.setdefault(disjoint.find(face_index), []).append(face_index)
    components = [np.asarray(indices, dtype=np.int32) for indices in grouped.values()]
    components.sort(key=len, reverse=True)
    return tuple(components)


def topology_component_ids(mesh: ObjMesh, weld_tolerance: float = 1e-5) -> np.ndarray:
    """Return a stable topology-component id for every face, largest first."""

    welded_ids = weld_vertex_ids(mesh.vertices, weld_tolerance)
    components = face_components(welded_ids[mesh.vertex_faces])
    labels = np.empty(len(mesh.vertex_faces), dtype=np.int32)
    for component_id, face_indices in enumerate(components):
        labels[face_indices] = component_id
    return labels


def topology_component_statistics(mesh: ObjMesh) -> list[dict]:
    component_ids = topology_component_ids(mesh)
    records: list[dict] = []
    for component_id in range(int(component_ids.max()) + 1):
        face_indices = np.flatnonzero(component_ids == component_id)
        vertex_indices = np.unique(mesh.vertex_faces[face_indices])
        vertices = mesh.vertices[vertex_indices]
        face_vertices = mesh.vertices[mesh.vertex_faces[face_indices]]
        twice_area = np.linalg.norm(
            np.cross(
                face_vertices[:, 1] - face_vertices[:, 0],
                face_vertices[:, 2] - face_vertices[:, 0],
            ),
            axis=1,
        )
        records.append(
            {
                "component_id": component_id,
                "face_count": int(len(face_indices)),
                "vertex_count": int(len(vertex_indices)),
                "surface_area": float(twice_area.sum() * 0.5),
                "centroid": vertices.mean(axis=0).astype(float).tolist(),
                "bounds_min": vertices.min(axis=0).astype(float).tolist(),
                "bounds_max": vertices.max(axis=0).astype(float).tolist(),
            }
        )
    return records


def semantic_face_labels(
    mesh: ObjMesh,
    regions: Iterable[SemanticRegionSpec],
    default_region: SemanticRegionSpec,
) -> tuple[np.ndarray, tuple[SemanticRegionSpec, ...]]:
    """Assign faces to ordered semantic rules using topology ids and 3D centroids."""

    ordered = tuple(regions)
    all_regions = ordered + (default_region,)
    face_labels = np.full(len(mesh.vertex_faces), len(ordered), dtype=np.int32)
    unassigned = np.ones(len(mesh.vertex_faces), dtype=bool)
    component_ids = topology_component_ids(mesh)
    centroids = mesh.vertices[mesh.vertex_faces].mean(axis=1)

    for label, region in enumerate(ordered):
        matches = unassigned.copy()
        if region.component_ids:
            matches &= np.isin(component_ids, np.asarray(region.component_ids, dtype=np.int32))
        for axis in range(3):
            minimum = region.centroid_min[axis]
            maximum = region.centroid_max[axis]
            if minimum is not None:
                matches &= centroids[:, axis] >= minimum
            if maximum is not None:
                matches &= centroids[:, axis] < maximum
        face_labels[matches] = label
        unassigned[matches] = False
    return face_labels, all_regions


def render_semantic_uv_assets(
    mesh: ObjMesh,
    face_labels: np.ndarray,
    regions: tuple[SemanticRegionSpec, ...],
    size: int = 2048,
) -> dict[str, Image.Image]:
    """Render one colour atlas and one binary UV mask per semantic face label."""

    if len(face_labels) != len(mesh.vertex_faces):
        raise ValueError("face_labels must contain one value per mesh face")
    if np.any(face_labels < 0) or np.any(face_labels >= len(regions)):
        raise ValueError("face_labels reference an unavailable semantic region")
    pixels = _uv_to_pixels(mesh.texcoords, size)
    atlas = np.full((size, size, 3), 18, dtype=np.uint8)
    masks = [np.zeros((size, size), dtype=np.uint8) for _ in regions]
    for face_index, label in enumerate(face_labels):
        polygon = pixels[mesh.texture_faces[face_index]]
        region = regions[int(label)]
        cv2.fillConvexPoly(atlas, polygon, region.color, lineType=cv2.LINE_AA)
        cv2.fillConvexPoly(masks[int(label)], polygon, 255, lineType=cv2.LINE_AA)

    outputs = {"semantic_atlas": Image.fromarray(atlas, mode="RGB")}
    outputs.update(
        {
            f"mask_{region.name}": Image.fromarray(mask, mode="L")
            for region, mask in zip(regions, masks, strict=True)
        }
    )
    return outputs


def render_topology_component_atlas(mesh: ObjMesh, size: int = 2048) -> tuple[Image.Image, list[tuple[int, int, int]]]:
    """Render stable per-component colours for asset calibration and debugging."""

    component_ids = topology_component_ids(mesh)
    component_count = int(component_ids.max()) + 1
    colors: list[tuple[int, int, int]] = []
    for component_id in range(component_count):
        hue = int((component_id * 137.508) % 180)
        hsv = np.uint8([[[hue, 190, 230]]])
        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)[0, 0]
        colors.append(tuple(int(channel) for channel in rgb))

    pixels = _uv_to_pixels(mesh.texcoords, size)
    atlas = np.full((size, size, 3), 18, dtype=np.uint8)
    for face_index, component_id in enumerate(component_ids):
        polygon = pixels[mesh.texture_faces[face_index]]
        cv2.fillConvexPoly(atlas, polygon, colors[int(component_id)], lineType=cv2.LINE_AA)
    return Image.fromarray(atlas, mode="RGB"), colors


def semantic_assignment_statistics(
    face_labels: np.ndarray,
    regions: tuple[SemanticRegionSpec, ...],
    masks: dict[str, Image.Image] | None = None,
) -> list[dict]:
    total_faces = max(len(face_labels), 1)
    records: list[dict] = []
    for label, region in enumerate(regions):
        face_count = int(np.count_nonzero(face_labels == label))
        record = {
            "name": region.name,
            "color": list(region.color),
            "face_count": face_count,
            "face_fraction": face_count / total_faces,
        }
        if masks is not None:
            mask = np.asarray(masks[f"mask_{region.name}"])
            record["uv_pixel_count"] = int(np.count_nonzero(mask))
            record["uv_pixel_fraction"] = float(np.count_nonzero(mask)) / mask.size
        records.append(record)
    return records


def weld_vertex_ids(vertices: np.ndarray, tolerance: float = 1e-5) -> np.ndarray:
    """Assign one stable id to OBJ vertices sharing the same 3D position."""

    if tolerance <= 0:
        raise ValueError("weld tolerance must be positive")
    quantized = np.rint(vertices.astype(np.float64) / tolerance).astype(np.int64)
    key_to_id: dict[tuple[int, int, int], int] = {}
    welded = np.empty(len(vertices), dtype=np.int32)
    for vertex_index, coordinate in enumerate(quantized):
        key = (int(coordinate[0]), int(coordinate[1]), int(coordinate[2]))
        welded[vertex_index] = key_to_id.setdefault(key, len(key_to_id))
    return welded


def build_uv_seam_pairs(
    mesh: ObjMesh,
    uv_tolerance: float = 1e-7,
    weld_tolerance: float = 1e-5,
) -> tuple[UVSeamPair, ...]:
    """Find position-welded 3D edges that use different UV edge coordinates."""

    welded_ids = weld_vertex_ids(mesh.vertices, weld_tolerance)
    edge_records: dict[tuple[int, int], list[tuple[int, tuple[int, int]]]] = {}
    for face_index, (vertex_face, texture_face) in enumerate(
        zip(mesh.vertex_faces, mesh.texture_faces, strict=True)
    ):
        for start, end in ((0, 1), (1, 2), (2, 0)):
            vertex_start = int(welded_ids[int(vertex_face[start])])
            vertex_end = int(welded_ids[int(vertex_face[end])])
            uv_start = int(texture_face[start])
            uv_end = int(texture_face[end])
            if vertex_start <= vertex_end:
                key = (vertex_start, vertex_end)
                uv_edge = (uv_start, uv_end)
            else:
                key = (vertex_end, vertex_start)
                uv_edge = (uv_end, uv_start)
            edge_records.setdefault(key, []).append((face_index, uv_edge))

    pairs: list[UVSeamPair] = []
    for vertex_edge, records in edge_records.items():
        if len(records) < 2:
            continue
        for (face_a, uv_edge_a), (face_b, uv_edge_b) in combinations(records, 2):
            coordinates_a = mesh.texcoords[np.asarray(uv_edge_a)]
            coordinates_b = mesh.texcoords[np.asarray(uv_edge_b)]
            if np.allclose(coordinates_a, coordinates_b, atol=uv_tolerance, rtol=0.0):
                continue
            pairs.append(
                UVSeamPair(
                    vertex_indices=vertex_edge,
                    uv_indices_a=uv_edge_a,
                    uv_indices_b=uv_edge_b,
                    face_indices=(face_a, face_b),
                )
            )
    return tuple(pairs)


def mesh_edge_statistics(mesh: ObjMesh, weld_tolerance: float = 1e-5) -> dict[str, int]:
    welded_ids = weld_vertex_ids(mesh.vertices, weld_tolerance)
    welded_faces = welded_ids[mesh.vertex_faces]
    raw = _edge_statistics(mesh.vertex_faces)
    welded = _edge_statistics(welded_faces)
    return {
        "raw_geometric_edge_count": raw["edge_count"],
        "raw_boundary_edge_count": raw["boundary_edge_count"],
        "welded_geometric_edge_count": welded["edge_count"],
        "welded_boundary_edge_count": welded["boundary_edge_count"],
        "welded_manifold_edge_count": welded["manifold_edge_count"],
        "welded_nonmanifold_edge_count": welded["nonmanifold_edge_count"],
    }


def _edge_statistics(faces: np.ndarray) -> dict[str, int]:
    edge_counts: dict[tuple[int, int], int] = {}
    for face in faces:
        for start, end in ((0, 1), (1, 2), (2, 0)):
            edge = tuple(sorted((int(face[start]), int(face[end]))))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    return {
        "edge_count": len(edge_counts),
        "boundary_edge_count": sum(count == 1 for count in edge_counts.values()),
        "manifold_edge_count": sum(count == 2 for count in edge_counts.values()),
        "nonmanifold_edge_count": sum(count > 2 for count in edge_counts.values()),
    }


def asset_uv_seam_error(
    image: Image.Image,
    mesh: ObjMesh,
    seam_pairs: Iterable[UVSeamPair] | None = None,
    samples_per_edge: int = 16,
    uv_address_mode: str = "clamp",
) -> dict[str, float | int]:
    """Measure color and along-edge gradient disagreement across mesh-derived UV seams."""

    if samples_per_edge < 2:
        raise ValueError("samples_per_edge must be at least 2")
    pairs = tuple(seam_pairs) if seam_pairs is not None else build_uv_seam_pairs(mesh)
    if not pairs:
        return {
            "seam_pair_count": 0,
            "samples_per_edge": samples_per_edge,
            "color_error": 0.0,
            "gradient_error": 0.0,
            "total_error": 0.0,
        }

    texture = np.asarray(image.convert("RGB"), dtype=np.float32)
    positions = np.linspace(0.0, 1.0, samples_per_edge, dtype=np.float32)[:, None]
    color_errors: list[float] = []
    gradient_errors: list[float] = []
    for pair in pairs:
        edge_a = mesh.texcoords[np.asarray(pair.uv_indices_a)]
        edge_b = mesh.texcoords[np.asarray(pair.uv_indices_b)]
        if uv_address_mode == "discard_outside" and not (
            np.all((edge_a >= 0.0) & (edge_a <= 1.0))
            and np.all((edge_b >= 0.0) & (edge_b <= 1.0))
        ):
            continue
        samples_a = edge_a[0] * (1.0 - positions) + edge_a[1] * positions
        samples_b = edge_b[0] * (1.0 - positions) + edge_b[1] * positions
        colors_a = _bilinear_sample(texture, samples_a, uv_address_mode)
        colors_b = _bilinear_sample(texture, samples_b, uv_address_mode)
        color_errors.append(float(np.mean(np.abs(colors_a - colors_b))) / 255.0)
        gradient_a = np.diff(colors_a, axis=0)
        gradient_b = np.diff(colors_b, axis=0)
        gradient_errors.append(float(np.mean(np.abs(gradient_a - gradient_b))) / 255.0)

    if not color_errors:
        return {
            "seam_pair_count": 0,
            "samples_per_edge": samples_per_edge,
            "color_error": 0.0,
            "gradient_error": 0.0,
            "total_error": 0.0,
        }
    color_error = float(np.mean(color_errors))
    gradient_error = float(np.mean(gradient_errors))
    return {
        "seam_pair_count": len(color_errors),
        "samples_per_edge": samples_per_edge,
        "color_error": color_error,
        "gradient_error": gradient_error,
        "total_error": 0.75 * color_error + 0.25 * gradient_error,
    }


def render_uv_diagnostics(mesh: ObjMesh, size: int = 2048) -> dict[str, Image.Image]:
    """Render the paintable UV footprint, islands, wireframe, and seam graph."""

    if size < 64:
        raise ValueError("UV diagnostic size must be at least 64")
    pixels = _uv_to_pixels(mesh.texcoords, size)
    mask = np.zeros((size, size), dtype=np.uint8)
    wireframe = np.full((size, size, 3), 18, dtype=np.uint8)
    islands_image = np.full((size, size, 3), 18, dtype=np.uint8)
    island_components = face_components(mesh.texture_faces)

    for island_index, face_indices in enumerate(island_components):
        hue = int((island_index * 137.508) % 180)
        hsv = np.uint8([[[hue, 165, 220]]])
        color = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)[0, 0].tolist()
        for face_index in face_indices:
            polygon = pixels[mesh.texture_faces[face_index]]
            cv2.fillConvexPoly(mask, polygon, 255, lineType=cv2.LINE_AA)
            cv2.fillConvexPoly(islands_image, polygon, color, lineType=cv2.LINE_AA)
            cv2.polylines(wireframe, [polygon], True, (95, 95, 95), 1, cv2.LINE_AA)

    seam_graph = wireframe.copy()
    for pair in build_uv_seam_pairs(mesh):
        edge_a = pixels[np.asarray(pair.uv_indices_a)]
        edge_b = pixels[np.asarray(pair.uv_indices_b)]
        cv2.line(seam_graph, edge_a[0], edge_a[1], (255, 67, 67), 2, cv2.LINE_AA)
        cv2.line(seam_graph, edge_b[0], edge_b[1], (255, 189, 46), 2, cv2.LINE_AA)

    return {
        "paintable_mask": Image.fromarray(mask, mode="L"),
        "uv_wireframe": Image.fromarray(wireframe, mode="RGB"),
        "uv_islands": Image.fromarray(islands_image, mode="RGB"),
        "uv_seam_graph": Image.fromarray(seam_graph, mode="RGB"),
    }


def summarize_uv_asset(mesh: ObjMesh, source_path: Path | None = None) -> dict:
    welded_ids = weld_vertex_ids(mesh.vertices)
    topology_components = face_components(welded_ids[mesh.vertex_faces])
    uv_islands = face_components(mesh.texture_faces)
    seam_pairs = build_uv_seam_pairs(mesh)
    return {
        "source_path": str(source_path) if source_path else None,
        "vertex_count": int(len(mesh.vertices)),
        "welded_vertex_count": int(welded_ids.max()) + 1,
        "uv_count": int(len(mesh.texcoords)),
        "triangle_count": int(len(mesh.vertex_faces)),
        "uv_bounds": {
            "minimum": mesh.texcoords.min(axis=0).astype(float).tolist(),
            "maximum": mesh.texcoords.max(axis=0).astype(float).tolist(),
        },
        "topology_component_count": len(topology_components),
        "largest_topology_components": [int(len(component)) for component in topology_components[:20]],
        "uv_island_count": len(uv_islands),
        "largest_uv_islands": [int(len(component)) for component in uv_islands[:20]],
        "uv_seam_pair_count": len(seam_pairs),
        **mesh_edge_statistics(mesh),
    }


def load_and_summarize(path: Path) -> tuple[ObjMesh, dict]:
    mesh = load_obj(path)
    return mesh, summarize_uv_asset(mesh, path)


def _uv_to_pixels(texcoords: np.ndarray, size: int) -> np.ndarray:
    x = np.clip(np.rint(texcoords[:, 0] * (size - 1)), 0, size - 1)
    y = np.clip(np.rint((1.0 - texcoords[:, 1]) * (size - 1)), 0, size - 1)
    return np.column_stack((x, y)).astype(np.int32)


def _bilinear_sample(
    texture: np.ndarray, uv: np.ndarray, uv_address_mode: str = "clamp"
) -> np.ndarray:
    if uv_address_mode == "repeat":
        uv = np.mod(uv, 1.0)
    elif uv_address_mode in {"clamp", "discard_outside"}:
        uv = np.clip(uv, 0.0, 1.0)
    else:
        raise ValueError(
            "uv_address_mode must be clamp, repeat, or discard_outside"
        )
    height, width = texture.shape[:2]
    x = np.clip(uv[:, 0] * (width - 1), 0.0, width - 1)
    y = np.clip((1.0 - uv[:, 1]) * (height - 1), 0.0, height - 1)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.minimum(x0 + 1, width - 1)
    y1 = np.minimum(y0 + 1, height - 1)
    wx = (x - x0)[:, None]
    wy = (y - y0)[:, None]
    top = texture[y0, x0] * (1.0 - wx) + texture[y0, x1] * wx
    bottom = texture[y1, x0] * (1.0 - wx) + texture[y1, x1] * wx
    return top * (1.0 - wy) + bottom * wy
