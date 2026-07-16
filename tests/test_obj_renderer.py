from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.obj_renderer import ObjMultiViewRenderer, load_obj  # noqa: E402
from skinsmith.evaluation import evaluate_multiview  # noqa: E402


class ObjRendererTests(unittest.TestCase):
    def test_loads_textured_triangle(self) -> None:
        content = """v 0 0 0
v 1 0 0
v 0 1 0
vt 0 0
vt 1 0
vt 0 1
f 1/1/1 2/2/1 3/3/1
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "triangle.obj"
            path.write_text(content, encoding="utf-8")
            mesh = load_obj(path)

        self.assertEqual(mesh.vertices.shape, (3, 3))
        self.assertEqual(mesh.texcoords.shape, (3, 2))
        np.testing.assert_array_equal(mesh.vertex_faces[0], [0, 1, 2])
        np.testing.assert_array_equal(mesh.texture_faces[0], [0, 1, 2])

    def test_triangulates_textured_quad(self) -> None:
        content = """v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
vt 0 0
vt 1 0
vt 1 1
vt 0 1
f 1/1 2/2 3/3 4/4
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quad.obj"
            path.write_text(content, encoding="utf-8")
            mesh = load_obj(path)

        np.testing.assert_array_equal(mesh.vertex_faces, [[0, 1, 2], [0, 2, 3]])
        np.testing.assert_array_equal(mesh.texture_faces, [[0, 1, 2], [0, 2, 3]])

    def test_multiview_metrics_are_bounded_and_named(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, name in enumerate(("left", "right", "top")):
                image = Image.new("RGB", (160, 90), "#1B1D1F")
                draw = ImageDraw.Draw(image)
                draw.rectangle((20, 30, 140, 60), fill=(35 + index * 10, 170, 210))
                draw.line((20, 45, 140, 45), fill=(240, 240, 240), width=3)
                path = Path(directory) / f"candidate_01_{name}.png"
                image.save(path)
                paths.append(path)

            score = evaluate_multiview(paths)

        self.assertEqual([view.view_name for view in score.views], ["left", "right", "top"])
        self.assertGreaterEqual(score.total_score, 0.0)
        self.assertLessEqual(score.total_score, 1.0)
        self.assertGreaterEqual(score.consistency_score, 0.0)
        self.assertLessEqual(score.consistency_score, 1.0)

    def test_barycentric_renderer_preserves_texture_variation_inside_face(self) -> None:
        content = """v 0 0 0
v 0 0 1
v 0 1 0
vt 0 0
vt 1 0
vt 0 1
f 1/1 2/2 3/3
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "triangle.obj"
            model_path.write_text(content, encoding="utf-8")
            gradient = np.zeros((64, 64, 3), dtype=np.uint8)
            gradient[..., 0] = np.arange(64, dtype=np.uint8)[None, :] * 4
            gradient[..., 2] = 255 - gradient[..., 0]
            renderer = ObjMultiViewRenderer(
                model_path, size=(160, 90), sampling="barycentric"
            )
            paths = renderer.render(Image.fromarray(gradient), root, "gradient")
            image = np.asarray(Image.open(paths[0]).convert("RGB"))

        foreground = np.any(image != (27, 29, 31), axis=2)
        unique_colors = np.unique(image[foreground], axis=0)
        self.assertGreater(len(unique_colors), 8)

    def test_repeat_address_mode_wraps_official_uv_tiles(self) -> None:
        content = """v 0 0 0
v 0 0 1
v 0 1 0
vt 0 0
vt 1 0
vt 0 1
f 1/1 2/2 3/3
"""
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / "triangle.obj"
            model_path.write_text(content, encoding="utf-8")
            renderer = ObjMultiViewRenderer(model_path, uv_address_mode="repeat")
            addressed = renderer._address_uv(
                np.asarray(((1.2, -2.1), (-0.25, 3.4)), dtype=np.float32)
            )

        np.testing.assert_allclose(addressed, ((0.2, 0.9), (0.75, 0.4)), atol=1e-6)


if __name__ == "__main__":
    unittest.main()
