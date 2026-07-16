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

from skinsmith.asset_spec import AssetSpec  # noqa: E402


class AssetSpecTests(unittest.TestCase):
    def test_loads_and_verifies_versioned_mesh(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mesh = root / "mesh.obj"
            mesh.write_text("v 0 0 0\n", encoding="utf-8")
            digest = hashlib.sha256(mesh.read_bytes()).hexdigest()
            config = {
                "asset_id": "test_asset",
                "display_name": "Test",
                "game": "Test Game",
                "mesh_path": "mesh.obj",
                "mesh_sha256": digest,
                "mesh_version": "v1",
                "uv_source": "mesh_derived",
                "texture_size": 64,
                "export_format": "PNG",
                "camera_views": ["left"],
                "semantic_regions": [
                    {"name": "front", "color": [1, 2, 3], "centroid_min": {"z": 0}}
                ],
                "default_region": {"name": "other", "color": [4, 5, 6]},
            }
            path = root / "asset.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            spec = AssetSpec.load(path, root)
            self.assertEqual(spec.mesh_path, mesh)
            self.assertEqual(spec.verify_mesh(), digest)
            self.assertEqual(spec.uv_address_mode, "clamp")
            self.assertIsNone(spec.verify_uv_sheet())

    def test_binds_and_verifies_official_uv_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mesh = root / "mesh.obj"
            sheet = root / "uv.tga"
            mesh.write_text("v 0 0 0\n", encoding="utf-8")
            sheet.write_bytes(b"official uv")
            config = {
                "asset_id": "workbench_asset",
                "display_name": "Workbench",
                "game": "Test Game",
                "mesh_path": "mesh.obj",
                "mesh_sha256": hashlib.sha256(mesh.read_bytes()).hexdigest(),
                "mesh_version": "official",
                "uv_source": "official_uv_sheet",
                "uv_address_mode": "repeat",
                "uv_sheet_path": "uv.tga",
                "uv_sheet_sha256": hashlib.sha256(sheet.read_bytes()).hexdigest(),
                "texture_size": 64,
                "export_format": "TGA",
                "camera_views": ["left"],
                "semantic_regions": [],
                "default_region": {"name": "other", "color": [4, 5, 6]},
            }
            path = root / "asset.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            spec = AssetSpec.load(path, root)

            self.assertEqual(spec.uv_address_mode, "repeat")
            self.assertEqual(spec.uv_sheet_path, sheet)
            self.assertEqual(
                spec.verify_uv_sheet(), hashlib.sha256(sheet.read_bytes()).hexdigest()
            )


if __name__ == "__main__":
    unittest.main()
