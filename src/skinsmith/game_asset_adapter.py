from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .asset_spec import AssetSpec
from .obj_renderer import ObjMesh, ObjMultiViewRenderer, load_obj
from .weapon_space import (
    CanonicalWeaponFrame,
    UVGeometryMaps,
    bake_uv_geometry_maps,
)


@dataclass(frozen=True)
class GameAssetAdapter:
    """Bind one target asset's authoritative mesh, UV, axes and preview contract."""

    spec: AssetSpec
    longitudinal_axis: tuple[float, float, float]
    up_axis: tuple[float, float, float]

    @classmethod
    def load(cls, path: Path, project_root: Path) -> "GameAssetAdapter":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        frame = data.get("canonical_frame", {})
        longitudinal = tuple(
            float(value) for value in frame.get("longitudinal_axis", (0, 0, 1))
        )
        up = tuple(float(value) for value in frame.get("up_axis", (0, 1, 0)))
        if len(longitudinal) != 3 or len(up) != 3:
            raise ValueError("canonical_frame axes must each contain three values")
        return cls(
            spec=AssetSpec.load(path, project_root),
            longitudinal_axis=longitudinal,
            up_axis=up,
        )

    def verify(self) -> dict[str, str | None]:
        return {
            "mesh_sha256": self.spec.verify_mesh(),
            "uv_sheet_sha256": self.spec.verify_uv_sheet(),
        }

    def load_mesh(self) -> ObjMesh:
        return load_obj(self.spec.mesh_path)

    def canonical_frame(self, mesh: ObjMesh) -> CanonicalWeaponFrame:
        return CanonicalWeaponFrame.from_mesh(
            mesh, self.longitudinal_axis, self.up_axis
        )

    def bake_geometry_maps(self, mesh: ObjMesh, size: int) -> UVGeometryMaps:
        return bake_uv_geometry_maps(
            mesh,
            self.canonical_frame(mesh),
            size,
            uv_address_mode=self.spec.uv_address_mode,
        )

    def renderer(self) -> ObjMultiViewRenderer:
        return ObjMultiViewRenderer(
            self.spec.mesh_path, uv_address_mode=self.spec.uv_address_mode
        )

    def to_log_dict(self) -> dict:
        return {
            "asset_spec": self.spec.to_log_dict(),
            "canonical_frame_axes": {
                "longitudinal_axis": list(self.longitudinal_axis),
                "up_axis": list(self.up_axis),
            },
        }
