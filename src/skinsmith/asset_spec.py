from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


AXES = {"x": 0, "y": 1, "z": 2}


@dataclass(frozen=True)
class SemanticRegionSpec:
    name: str
    color: tuple[int, int, int]
    component_ids: tuple[int, ...] = ()
    centroid_min: tuple[float | None, float | None, float | None] = (None, None, None)
    centroid_max: tuple[float | None, float | None, float | None] = (None, None, None)

    @classmethod
    def from_dict(cls, data: dict) -> "SemanticRegionSpec":
        color = data.get("color")
        if not isinstance(color, list) or len(color) != 3:
            raise ValueError(f"Region {data.get('name')} must define an RGB color")
        return cls(
            name=str(data["name"]),
            color=tuple(int(channel) for channel in color),
            component_ids=tuple(int(value) for value in data.get("component_ids", [])),
            centroid_min=_axis_tuple(data.get("centroid_min", {})),
            centroid_max=_axis_tuple(data.get("centroid_max", {})),
        )


@dataclass(frozen=True)
class AssetSpec:
    asset_id: str
    display_name: str
    game: str
    mesh_path: Path
    mesh_sha256: str
    mesh_version: str
    uv_source: str
    uv_address_mode: str
    uv_sheet_path: Path | None
    uv_sheet_sha256: str | None
    texture_size: int
    export_format: str
    camera_views: tuple[str, ...]
    semantic_regions: tuple[SemanticRegionSpec, ...]
    default_region: SemanticRegionSpec
    source_path: Path

    @classmethod
    def load(cls, path: Path, project_root: Path | None = None) -> "AssetSpec":
        path = Path(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        root = Path(project_root) if project_root is not None else path.parent
        mesh_path = Path(data["mesh_path"])
        if not mesh_path.is_absolute():
            mesh_path = root / mesh_path
        uv_address_mode = str(data.get("uv_address_mode", "clamp"))
        if uv_address_mode not in {"clamp", "repeat", "discard_outside"}:
            raise ValueError(
                "Asset uv_address_mode must be clamp, repeat, or discard_outside"
            )
        uv_sheet_path = None
        if data.get("uv_sheet_path"):
            uv_sheet_path = Path(data["uv_sheet_path"])
            if not uv_sheet_path.is_absolute():
                uv_sheet_path = root / uv_sheet_path
        uv_sheet_sha256 = (
            str(data["uv_sheet_sha256"]).lower()
            if data.get("uv_sheet_sha256")
            else None
        )
        if bool(uv_sheet_path) != bool(uv_sheet_sha256):
            raise ValueError("Asset UV sheet path and SHA-256 must be provided together")
        regions = tuple(SemanticRegionSpec.from_dict(item) for item in data["semantic_regions"])
        names = [region.name for region in regions]
        if len(names) != len(set(names)):
            raise ValueError("Semantic region names must be unique")
        texture_size = int(data["texture_size"])
        if texture_size < 64:
            raise ValueError("Asset texture_size must be at least 64")
        default_region = SemanticRegionSpec.from_dict(data["default_region"])
        return cls(
            asset_id=str(data["asset_id"]),
            display_name=str(data["display_name"]),
            game=str(data["game"]),
            mesh_path=mesh_path,
            mesh_sha256=str(data["mesh_sha256"]).lower(),
            mesh_version=str(data["mesh_version"]),
            uv_source=str(data["uv_source"]),
            uv_address_mode=uv_address_mode,
            uv_sheet_path=uv_sheet_path,
            uv_sheet_sha256=uv_sheet_sha256,
            texture_size=texture_size,
            export_format=str(data["export_format"]),
            camera_views=tuple(str(view) for view in data["camera_views"]),
            semantic_regions=regions,
            default_region=default_region,
            source_path=path,
        )

    def verify_mesh(self) -> str:
        if not self.mesh_path.exists():
            raise FileNotFoundError(f"Asset mesh is missing: {self.mesh_path}")
        digest = hashlib.sha256(self.mesh_path.read_bytes()).hexdigest()
        if digest != self.mesh_sha256:
            raise ValueError(
                f"Mesh hash mismatch for {self.asset_id}: expected {self.mesh_sha256}, got {digest}"
            )
        return digest

    def verify_uv_sheet(self) -> str | None:
        if self.uv_sheet_path is None:
            return None
        if not self.uv_sheet_path.exists():
            raise FileNotFoundError(f"Asset UV sheet is missing: {self.uv_sheet_path}")
        digest = hashlib.sha256(self.uv_sheet_path.read_bytes()).hexdigest()
        if digest != self.uv_sheet_sha256:
            raise ValueError(
                f"UV sheet hash mismatch for {self.asset_id}: "
                f"expected {self.uv_sheet_sha256}, got {digest}"
            )
        return digest

    def to_log_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "display_name": self.display_name,
            "game": self.game,
            "mesh_path": str(self.mesh_path),
            "mesh_sha256": self.mesh_sha256,
            "mesh_version": self.mesh_version,
            "uv_source": self.uv_source,
            "uv_address_mode": self.uv_address_mode,
            "uv_sheet_path": str(self.uv_sheet_path) if self.uv_sheet_path else None,
            "uv_sheet_sha256": self.uv_sheet_sha256,
            "texture_size": self.texture_size,
            "export_format": self.export_format,
            "camera_views": list(self.camera_views),
            "semantic_region_order": [region.name for region in self.semantic_regions],
            "default_region": self.default_region.name,
            "source_path": str(self.source_path),
        }


def _axis_tuple(values: dict) -> tuple[float | None, float | None, float | None]:
    unknown = set(values) - AXES.keys()
    if unknown:
        raise ValueError(f"Unknown centroid axes: {sorted(unknown)}")
    return tuple(float(values[axis]) if axis in values else None for axis in ("x", "y", "z"))
