from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.obj_renderer import ObjMesh  # noqa: E402
from skinsmith.asset_spec import SemanticRegionSpec  # noqa: E402
from skinsmith.uv_asset import (  # noqa: E402
    asset_uv_seam_error,
    build_uv_seam_pairs,
    face_components,
    render_semantic_uv_assets,
    semantic_face_labels,
    topology_component_ids,
    weld_vertex_ids,
)


class UVAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.vertices = np.asarray(
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)], dtype=np.float32
        )
        self.vertex_faces = np.asarray([(0, 1, 2), (1, 3, 2)], dtype=np.int32)

    def test_detects_split_uv_edge_and_two_islands(self) -> None:
        texcoords = np.asarray(
            [(0.1, 0.1), (0.4, 0.1), (0.1, 0.4), (0.6, 0.1), (0.9, 0.4), (0.6, 0.4)],
            dtype=np.float32,
        )
        mesh = ObjMesh(
            self.vertices,
            texcoords,
            self.vertex_faces,
            np.asarray([(0, 1, 2), (3, 4, 5)], dtype=np.int32),
        )
        pairs = build_uv_seam_pairs(mesh)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0].vertex_indices, (1, 2))
        self.assertEqual(len(face_components(mesh.texture_faces)), 2)

        gradient = np.tile(np.arange(64, dtype=np.uint8), (64, 1))
        image = Image.fromarray(np.dstack((gradient, gradient, gradient)), mode="RGB")
        score = asset_uv_seam_error(image, mesh, pairs, samples_per_edge=8)
        self.assertGreater(score["total_error"], 0.0)

    def test_continuous_uv_edge_is_not_a_seam(self) -> None:
        mesh = ObjMesh(
            self.vertices,
            np.asarray([(0.1, 0.1), (0.8, 0.1), (0.1, 0.8), (0.8, 0.8)], dtype=np.float32),
            self.vertex_faces,
            np.asarray([(0, 1, 2), (1, 3, 2)], dtype=np.int32),
        )
        self.assertEqual(build_uv_seam_pairs(mesh), ())
        self.assertEqual(len(face_components(mesh.texture_faces)), 1)

    def test_welds_duplicated_obj_positions_before_seam_detection(self) -> None:
        duplicated_vertices = np.asarray(
            [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],
            dtype=np.float32,
        )
        mesh = ObjMesh(
            duplicated_vertices,
            np.asarray(
                [(0.1, 0.1), (0.4, 0.1), (0.1, 0.4), (0.6, 0.1), (0.9, 0.4), (0.6, 0.4)],
                dtype=np.float32,
            ),
            np.asarray([(0, 1, 2), (3, 4, 5)], dtype=np.int32),
            np.asarray([(0, 1, 2), (3, 4, 5)], dtype=np.int32),
        )
        self.assertEqual(len(np.unique(weld_vertex_ids(mesh.vertices))), 4)
        self.assertEqual(len(build_uv_seam_pairs(mesh)), 1)

    def test_semantic_regions_use_ordered_component_and_spatial_rules(self) -> None:
        mesh = ObjMesh(
            self.vertices,
            np.asarray([(0.1, 0.1), (0.8, 0.1), (0.1, 0.8), (0.8, 0.8)], dtype=np.float32),
            self.vertex_faces,
            np.asarray([(0, 1, 2), (1, 3, 2)], dtype=np.int32),
        )
        self.assertEqual(topology_component_ids(mesh).tolist(), [0, 0])
        priority = SemanticRegionSpec(
            name="priority",
            color=(255, 0, 0),
            component_ids=(0,),
            centroid_min=(0.5, None, None),
        )
        fallback = SemanticRegionSpec(
            name="fallback",
            color=(0, 255, 0),
            centroid_min=(0.0, None, None),
        )
        other = SemanticRegionSpec(name="other", color=(0, 0, 255))
        labels, regions = semantic_face_labels(mesh, (priority, fallback), other)
        self.assertEqual(labels.tolist(), [1, 0])
        outputs = render_semantic_uv_assets(mesh, labels, regions, size=64)
        self.assertEqual(set(outputs), {"semantic_atlas", "mask_priority", "mask_fallback", "mask_other"})
        self.assertGreater(np.count_nonzero(np.asarray(outputs["mask_priority"])), 0)
        self.assertGreater(np.count_nonzero(np.asarray(outputs["mask_fallback"])), 0)


if __name__ == "__main__":
    unittest.main()
