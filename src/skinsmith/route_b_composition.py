from __future__ import annotations

from pathlib import Path
from typing import Mapping, Any

import cv2
import numpy as np
from PIL import Image

from .weapon_space import WeaponDesignPlan


ROLE_LAYER_IDS = {
    "background": ("background_all",),
    "secondary": ("secondary_stock", "secondary_magazine"),
    "connector": ("connector_side", "connector_top"),
    "hero": ("hero_receiver", "hero_top"),
}


def _component(layout: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [item for item in layout if item.get("component") == name]
    if len(matches) != 1:
        raise ValueError(f"Route-B component_layout must contain exactly one {name}")
    return matches[0]


def _canvas_center(component: Mapping[str, Any]) -> tuple[float, float]:
    """Return normalized image-space coordinates (origin at top-left)."""

    values = component.get("canvas_center")
    if not isinstance(values, list) or len(values) != 2:
        raise ValueError("Route-B component canvas_center must contain x and y")
    x, y = (float(value) for value in values)
    if not 0.0 <= x <= 1.0 or not 0.0 <= y <= 1.0:
        raise ValueError("Route-B component canvas_center must be normalized")
    return x, y


def _canonical_center(component: Mapping[str, Any]) -> tuple[float, float]:
    """Convert top-left image-space anchors to canonical longitudinal/up coordinates."""

    x, canvas_y = _canvas_center(component)
    return x, 1.0 - canvas_y


def _graph_groups(weapon: Mapping[str, Any]) -> list[dict[str, Any]]:
    graph = weapon.get("composition_graph")
    if not isinstance(graph, dict):
        return []
    strategy = str(graph.get("strategy", "legacy_semantic_roles"))
    groups = graph.get("groups")
    if strategy == "legacy_semantic_roles" or not isinstance(groups, (list, tuple)):
        return []
    if not all(isinstance(group, Mapping) for group in groups):
        raise ValueError("weapon_theme.composition_graph.groups must contain objects")
    return [dict(group) for group in groups]


def composition_strategy(bundle: Mapping[str, Any]) -> str:
    weapon = bundle.get("weapon_theme")
    graph = weapon.get("composition_graph") if isinstance(weapon, Mapping) else None
    return (
        str(graph.get("strategy", "legacy_semantic_roles"))
        if isinstance(graph, Mapping)
        else "legacy_semantic_roles"
    )


def has_master_artwork(bundle: Mapping[str, Any]) -> bool:
    return composition_strategy(bundle) == "master_artwork"


def _group_layer_specs(
    groups: list[dict[str, Any]],
    layout: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    components = {
        str(item.get("component")): item
        for item in layout
        if isinstance(item, dict) and isinstance(item.get("component"), str)
    }
    role_order = {"background": 0, "connector": 1, "secondary": 2, "hero": 3}
    role_opacity = {
        "background": 1.0,
        "connector": 0.72,
        "secondary": 0.66,
        "hero": 0.96,
    }
    ordered = sorted(
        groups,
        key=lambda group: (
            role_order.get(str(group.get("semantic_role")), 9),
            str(group.get("group_id")),
        ),
    )
    layers: list[dict[str, Any]] = []
    for group in ordered:
        group_id = str(group.get("group_id", "")).strip()
        mode = str(group.get("composition_mode", "")).strip()
        role = str(group.get("semantic_role", "")).strip()
        group_components = tuple(str(value) for value in group.get("components", ()))
        surfaces = tuple(str(value) for value in group.get("surfaces", ()))
        if not group_id or not group_components or not surfaces:
            raise ValueError("composition graph group is incomplete")
        missing = set(group_components) - components.keys()
        if missing:
            raise ValueError(
                f"composition graph group {group_id} references unknown components: "
                f"{sorted(missing)}"
            )
        if mode == "background":
            layers.append(
                {
                    "layer_id": group_id,
                    "surfaces": list(surfaces),
                    "center": [0.5, 0.5],
                    "size": [1.0, 1.0],
                    "opacity": 1.0,
                    "blend_mode": "normal",
                    "fit_mode": "cover",
                    "mirror_on_right": bool(group.get("mirror_on_right", True)),
                    "feather_fraction": 0.0,
                }
            )
            continue

        side_surfaces = [surface for surface in surfaces if surface in {"left", "right"}]
        has_top = "top" in surfaces
        if mode == "spanning":
            placements = [components[component] for component in group_components]
            centers = [_canvas_center(item) for item in placements]
            x_values = [center[0] for center in centers]
            y_values = [center[1] for center in centers]
            center_x = (min(x_values) + max(x_values)) / 2.0
            center_y = (min(y_values) + max(y_values)) / 2.0
            size_x = min(1.35, max(0.30, max(x_values) - min(x_values) + 0.30))
            size_y = min(0.90, max(0.38, max(y_values) - min(y_values) + 0.42))
            if side_surfaces:
                layers.append(
                    {
                        "layer_id": f"{group_id}__side",
                        "surfaces": side_surfaces,
                        "center": [center_x, center_y],
                        "size": [size_x, size_y],
                        "opacity": role_opacity.get(role, 0.8),
                        "blend_mode": "screen",
                        "fit_mode": "contain",
                        "mirror_on_right": bool(group.get("mirror_on_right", True)),
                        "feather_fraction": 0.06,
                    }
                )
            if has_top:
                layers.append(
                    {
                        "layer_id": f"{group_id}__top",
                        "surfaces": ["top"],
                        "center": [center_x, 0.5],
                        "size": [size_x, 0.72],
                        "opacity": role_opacity.get(role, 0.8) * 0.90,
                        "blend_mode": "screen",
                        "fit_mode": "contain",
                        "mirror_on_right": False,
                        "feather_fraction": 0.08,
                    }
                )
            continue

        for component in group_components:
            placement = components[component]
            center = _canvas_center(placement)
            prominence = float(placement.get("prominence", 0.5))
            detail = float(placement.get("detail_density", 0.5))
            size = [
                min(0.48, 0.22 + 0.20 * prominence),
                min(0.62, 0.30 + 0.22 * max(prominence, detail)),
            ]
            if side_surfaces:
                layers.append(
                    {
                        "layer_id": f"{group_id}__{component}__side",
                        "surfaces": side_surfaces,
                        "center": list(center),
                        "size": size,
                        "opacity": role_opacity.get(role, 0.8),
                        "blend_mode": "screen",
                        "fit_mode": "contain",
                        "mirror_on_right": bool(group.get("mirror_on_right", True)),
                        "feather_fraction": 0.08,
                    }
                )
            if has_top:
                layers.append(
                    {
                        "layer_id": f"{group_id}__{component}__top",
                        "surfaces": ["top"],
                        "center": [center[0], 0.5],
                        "size": [size[0], min(0.78, size[1] + 0.12)],
                        "opacity": role_opacity.get(role, 0.8) * 0.90,
                        "blend_mode": "screen",
                        "fit_mode": "contain",
                        "mirror_on_right": False,
                        "feather_fraction": 0.08,
                    }
                )
    if not layers:
        raise ValueError("composition graph did not compile any weapon-space layers")
    return layers


def compile_weapon_design_plan(bundle: Mapping[str, Any]) -> WeaponDesignPlan:
    """Compile semantic Route-B planning into a generated-asset weapon-space plan."""

    weapon = bundle.get("weapon_theme")
    if not isinstance(weapon, dict):
        raise ValueError("route bundle is missing weapon_theme")
    palette = weapon.get("palette")
    if not isinstance(palette, list) or len(palette) < 4:
        raise ValueError("Route-B palette must contain at least four colours")
    layout = weapon.get("component_layout")
    if not isinstance(layout, list):
        raise ValueError("route bundle is missing weapon_theme.component_layout")
    receiver = _component(layout, "receiver")
    stock = _component(layout, "stock")
    magazine = _component(layout, "magazine")
    handguard = _component(layout, "handguard")
    barrel = _component(layout, "barrel_muzzle")
    receiver_canvas = _canvas_center(receiver)
    stock_canvas = _canvas_center(stock)
    magazine_canvas = _canvas_center(magazine)
    handguard_canvas = _canvas_center(handguard)
    barrel_canvas = _canvas_center(barrel)
    receiver_center = _canonical_center(receiver)
    stock_center = _canonical_center(stock)
    magazine_center = _canonical_center(magazine)
    handguard_center = _canonical_center(handguard)
    flow_center = sum(
        center[1] for center in (stock_canvas, receiver_canvas, handguard_canvas)
    ) / 3.0
    quiet_start = max(0.72, min(0.92, barrel_canvas[0] - 0.08))

    groups = _graph_groups(weapon)
    focal_component = str(weapon.get("focal_component", "receiver"))
    focal_placement = _component(layout, focal_component)
    focal_center = _canonical_center(focal_placement)
    muzzle_focus = (
        composition_strategy(bundle) == "master_artwork"
        or any(bool(group.get("allow_muzzle_focus", False)) for group in groups)
    )
    if composition_strategy(bundle) == "master_artwork":
        content_layers = [
            {
                "layer_id": "master_artwork__side",
                "surfaces": ["left", "right"],
                "center": [0.5, 0.5],
                "size": [1.0, 1.0],
                "opacity": 1.0,
                "blend_mode": "normal",
                "fit_mode": "cover",
                "mirror_on_right": True,
                "feather_fraction": 0.0,
            },
            {
                "layer_id": "master_artwork__top",
                "surfaces": ["top"],
                "center": [0.5, 0.5],
                "size": [1.0, 1.0],
                "opacity": 1.0,
                "blend_mode": "normal",
                "fit_mode": "cover",
                "mirror_on_right": False,
                "feather_fraction": 0.0,
            },
        ]
    elif groups:
        content_layers = _group_layer_specs(groups, layout)
    else:
        content_layers = [
            {
                "layer_id": "background_all",
                "surfaces": ["left", "right", "top"],
                "center": [0.5, 0.5],
                "size": [1.0, 1.0],
                "opacity": 1.0,
                "blend_mode": "normal",
                "fit_mode": "cover",
                "mirror_on_right": True,
                "feather_fraction": 0.0,
            },
            {
                "layer_id": "secondary_stock",
                "surfaces": ["left", "right"],
                "center": list(stock_canvas),
                "size": [0.30, 0.46],
                "opacity": 0.48,
                "blend_mode": "screen",
                "fit_mode": "contain",
                "mirror_on_right": True,
                "feather_fraction": 0.10,
            },
            {
                "layer_id": "secondary_magazine",
                "surfaces": ["left", "right"],
                "center": list(magazine_canvas),
                "size": [0.30, 0.48],
                "rotation_degrees": -10.0,
                "opacity": 0.58,
                "blend_mode": "screen",
                "fit_mode": "contain",
                "mirror_on_right": True,
                "feather_fraction": 0.10,
            },
            {
                "layer_id": "connector_side",
                "surfaces": ["left", "right"],
                "center": [
                    (stock_canvas[0] + handguard_canvas[0]) / 2.0,
                    flow_center,
                ],
                "size": [0.76, 0.30],
                "rotation_degrees": -4.0,
                "opacity": 0.68,
                "blend_mode": "screen",
                "fit_mode": "stretch",
                "mirror_on_right": True,
                "feather_fraction": 0.08,
            },
            {
                "layer_id": "connector_top",
                "surfaces": ["top"],
                "center": [0.58, 0.5],
                "size": [0.70, 0.44],
                "opacity": 0.60,
                "blend_mode": "screen",
                "fit_mode": "stretch",
                "mirror_on_right": False,
                "feather_fraction": 0.10,
            },
            {
                "layer_id": "hero_receiver",
                "surfaces": ["left", "right"],
                "center": list(receiver_canvas),
                "size": [0.36, 0.56],
                "rotation_degrees": -12.0,
                "opacity": 0.92,
                "blend_mode": "screen",
                "fit_mode": "contain",
                "mirror_on_right": True,
                "feather_fraction": 0.08,
            },
            {
                "layer_id": "hero_top",
                "surfaces": ["top"],
                "center": [receiver_center[0], 0.5],
                "size": [0.34, 0.62],
                "opacity": 0.82,
                "blend_mode": "screen",
                "fit_mode": "contain",
                "mirror_on_right": False,
                "feather_fraction": 0.08,
            },
        ]
    plan_data = {
        "plan_id": f"{weapon.get('theme_id', 'generated_theme')}_weapon_space_v1",
        "description": str(
            weapon.get(
                "composition_prompt",
                "Generated semantic assets composed in continuous weapon space.",
            )
        ),
        "palette": palette,
        "canvas_size": [1536, 768],
        "focal_center": list(focal_center),
        "focal_radius": [0.11, 0.15],
        "flow_center": flow_center,
        "flow_amplitude": 0.045,
        "flow_cycles": 1.15,
        "flow_thicknesses": [30, 18, 10],
        "quiet_start": quiet_start,
        "quiet_strength": 0.0 if muzzle_focus else 0.88,
        "secondary_anchors": [list(stock_center), list(magazine_center), list(handguard_center)],
        "projection_blend_power": 4.0,
        "content_layers": content_layers,
    }
    return WeaponDesignPlan.from_dict(plan_data)


def load_generated_role_images(
    directory: Path,
    bundle: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Image.Image], dict[str, dict[str, str]]]:
    """Bind generated role or composition-group images to weapon-space layers."""

    directory = Path(directory)
    images: dict[str, Image.Image] = {}
    provenance: dict[str, dict[str, str]] = {}
    import hashlib

    weapon = bundle.get("weapon_theme") if isinstance(bundle, Mapping) else None
    groups = _graph_groups(weapon) if isinstance(weapon, Mapping) else []
    if isinstance(bundle, Mapping) and has_master_artwork(bundle):
        plan = compile_weapon_design_plan(bundle)
        path = directory / "route_b_master_artwork.png"
        if not path.is_file():
            raise ValueError(f"missing generated Route-B master artwork: {path}")
        payload = path.read_bytes()
        opened = Image.open(path).convert("RGBA")
        for layer in plan.content_layers:
            images[layer.layer_id] = opened.copy()
            provenance[layer.layer_id] = {
                "semantic_role": "master_artwork",
                "composition_group_id": "master_artwork",
                "source_path": str(path),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        return images, provenance
    if groups:
        plan = compile_weapon_design_plan(bundle)
        layer_ids = tuple(layer.layer_id for layer in plan.content_layers)
        for group in groups:
            group_id = str(group["group_id"])
            role = str(group["semantic_role"])
            path = directory / f"route_b_{group_id}.png"
            if not path.is_file():
                raise ValueError(
                    f"missing generated Route-B composition group {group_id}: {path}"
                )
            payload = path.read_bytes()
            opened = Image.open(path).convert("RGBA")
            if role != "background":
                opened = extract_removable_background(opened)
            consumers = tuple(
                layer_id
                for layer_id in layer_ids
                if layer_id == group_id or layer_id.startswith(f"{group_id}__")
            )
            if not consumers:
                raise ValueError(f"composition group {group_id} has no compiled layer")
            for layer_id in consumers:
                images[layer_id] = opened.copy()
                provenance[layer_id] = {
                    "semantic_role": role,
                    "composition_group_id": group_id,
                    "source_path": str(path),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
        return images, provenance

    for role, layer_ids in ROLE_LAYER_IDS.items():
        path = directory / f"route_b_{role}.png"
        if not path.is_file():
            raise ValueError(f"missing generated Route-B {role} asset: {path}")
        payload = path.read_bytes()
        opened = Image.open(path).convert("RGBA")
        if role != "background":
            opened = extract_removable_background(opened)
        for layer_id in layer_ids:
            images[layer_id] = opened.copy()
            provenance[layer_id] = {
                "semantic_role": role,
                "source_path": str(path),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
    return images, provenance


def extract_removable_background(image: Image.Image) -> Image.Image:
    """Convert a near-uniform generated role background into a soft alpha mask."""

    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()
    rgb = rgba[..., :3].astype(np.float32)
    height, width = rgb.shape[:2]
    border_width = max(2, round(min(width, height) * 0.04))
    border = np.concatenate(
        (
            rgb[:border_width].reshape(-1, 3),
            rgb[-border_width:].reshape(-1, 3),
            rgb[:, :border_width].reshape(-1, 3),
            rgb[:, -border_width:].reshape(-1, 3),
        ),
        axis=0,
    )
    background = np.median(border, axis=0)
    distance = np.linalg.norm(rgb - background, axis=2)
    low = max(8.0, float(np.quantile(distance, 0.45)))
    high = max(low + 12.0, float(np.quantile(distance, 0.72)))
    alpha = np.clip((distance - low) / (high - low), 0.0, 1.0)
    alpha = cv2.GaussianBlur(alpha.astype(np.float32), (0, 0), 1.5)
    alpha[alpha < 0.025] = 0.0
    rgba[..., 3] = np.rint(np.clip(alpha, 0.0, 1.0) * 255.0).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")
