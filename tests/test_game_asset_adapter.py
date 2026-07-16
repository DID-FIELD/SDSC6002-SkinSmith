from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skinsmith.game_asset_adapter import GameAssetAdapter  # noqa: E402


class GameAssetAdapterTests(unittest.TestCase):
    def test_loads_asset_specific_canonical_axes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mesh = root / "mesh.obj"
            mesh.write_text(
                "v 0 0 0\nv 1 0 0\nv 0 1 0\n"
                "vt 0 0\nvt 1 0\nvt 0 1\nf 1/1 2/2 3/3\n",
                encoding="utf-8",
            )
            config = {
                "asset_id": "adapter_test",
                "display_name": "Adapter Test",
                "game": "Test",
                "mesh_path": "mesh.obj",
                "mesh_sha256": hashlib.sha256(mesh.read_bytes()).hexdigest(),
                "mesh_version": "v1",
                "uv_source": "mesh_derived",
                "texture_size": 64,
                "export_format": "PNG",
                "camera_views": ["left", "right", "top"],
                "canonical_frame": {
                    "longitudinal_axis": [1, 0, 0],
                    "up_axis": [0, 1, 0],
                },
                "semantic_regions": [],
                "default_region": {"name": "other", "color": [1, 2, 3]},
            }
            path = root / "asset.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            adapter = GameAssetAdapter.load(path, root)
            self.assertEqual(adapter.longitudinal_axis, (1.0, 0.0, 0.0))
            self.assertEqual(adapter.up_axis, (0.0, 1.0, 0.0))
            self.assertEqual(adapter.verify()["mesh_sha256"], config["mesh_sha256"])
            maps = adapter.bake_geometry_maps(adapter.load_mesh(), 64)
            self.assertGreater(maps.statistics()["valid_pixel_count"], 0)


if __name__ == "__main__":
    unittest.main()
