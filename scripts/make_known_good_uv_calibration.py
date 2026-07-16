from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skinsmith.obj_renderer import ObjMultiViewRenderer, load_obj  # noqa: E402
from skinsmith.uv_asset import face_components  # noqa: E402


SIZE = 2048
MAJOR_ISLAND_COUNT = 24
OUTPUT_DIR = ROOT / "runs" / "known_good_uv_calibration"
MESH_PATH = ROOT / "third_party" / "valve_geometry" / "weapon_rif_ak47.obj"
REFERENCE_PATH = ROOT / "runs" / "uv_asset_diagnostics" / "viper_reference" / "weapon_rif_ak47_uv_viper.png"
WIREFRAME_PATH = ROOT / "runs" / "uv_asset_diagnostics" / "uv_wireframe.png"


PALETTE = [
    (230, 57, 70), (36, 163, 219), (255, 183, 3), (131, 56, 236),
    (6, 214, 160), (255, 112, 67), (76, 201, 240), (247, 37, 133),
    (144, 190, 109), (255, 209, 102), (0, 187, 249), (181, 101, 167),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def uv_pixels(texcoords: np.ndarray) -> np.ndarray:
    pixels = np.empty_like(texcoords, dtype=np.float32)
    pixels[:, 0] = texcoords[:, 0] * (SIZE - 1)
    pixels[:, 1] = (1.0 - texcoords[:, 1]) * (SIZE - 1)
    return np.rint(pixels).astype(np.int32)


def label_box(canvas: np.ndarray, text: str, origin: tuple[int, int], color: tuple[int, int, int]) -> None:
    x, y = origin
    scale = 1.05
    thickness = 3
    (width, height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    cv2.rectangle(canvas, (x - 10, y - height - 10), (x + width + 10, y + baseline + 10), (12, 12, 12), -1)
    cv2.putText(canvas, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mesh = load_obj(MESH_PATH)
    pixels = uv_pixels(mesh.texcoords)
    components = face_components(mesh.texture_faces)

    canvas = np.full((SIZE, SIZE, 3), (24, 24, 28), dtype=np.uint8)
    island_records: list[dict] = []
    for rank, face_indices in enumerate(components[:MAJOR_ISLAND_COUNT], start=1):
        color = PALETTE[(rank - 1) % len(PALETTE)]
        mask = np.zeros((SIZE, SIZE), dtype=np.uint8)
        for face_index in face_indices:
            polygon = pixels[mesh.texture_faces[face_index]]
            cv2.fillConvexPoly(mask, polygon, 255, lineType=cv2.LINE_8)
        canvas[mask > 0] = color
        count, _, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
        component_index = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        cx, cy = np.rint(centroids[component_index]).astype(int)
        island_records.append({
            "label": f"I{rank:02d}",
            "face_count": int(len(face_indices)),
            "pixel_area": int(np.count_nonzero(mask)),
            "label_pixel_xy": [int(cx), int(cy)],
            "color_rgb": list(color),
        })
        cv2.putText(canvas, f"I{rank:02d}", (cx - 30, cy + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 5, cv2.LINE_AA)
        cv2.putText(canvas, f"I{rank:02d}", (cx - 30, cy + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA)

    # Fine UV edges remain visible over the pure island colours.
    for texture_face in mesh.texture_faces:
        cv2.polylines(canvas, [pixels[texture_face]], True, (225, 225, 225), 1, cv2.LINE_AA)

    block = 230
    corners = [
        ((0, 0), (225, 45, 45), "TOP-LEFT  U0 V1"),
        ((SIZE - block, 0), (45, 185, 75), "TOP-RIGHT U1 V1"),
        ((0, SIZE - block), (45, 105, 230), "BOTTOM-LEFT  U0 V0"),
        ((SIZE - block, SIZE - block), (235, 205, 45), "BOTTOM-RIGHT U1 V0"),
    ]
    for (x, y), color, text in corners:
        cv2.rectangle(canvas, (x, y), (x + block - 1, y + block - 1), color, -1)
        label_box(canvas, text, (x + 14, y + 65), (255, 255, 255))

    center = SIZE // 2
    cv2.line(canvas, (center, center - 150), (center, center + 150), (255, 255, 255), 18, cv2.LINE_AA)
    cv2.line(canvas, (center - 150, center), (center + 150, center), (255, 255, 255), 18, cv2.LINE_AA)
    cv2.line(canvas, (center, center - 150), (center, center + 150), (0, 0, 0), 5, cv2.LINE_AA)
    cv2.line(canvas, (center - 150, center), (center + 150, center), (0, 0, 0), 5, cv2.LINE_AA)
    label_box(canvas, "CENTER U0.5 V0.5", (center + 175, center + 12), (255, 255, 255))

    image = Image.fromarray(canvas, mode="RGB")
    png_path = OUTPUT_DIR / "ak47_hd_uv_calibration_2048.png"
    tga_path = OUTPUT_DIR / "ak47_hd_uv_calibration_2048__custom-paint-job.tga"
    image.save(png_path)
    image.save(tga_path, format="TGA")

    decoded_tga = np.asarray(Image.open(tga_path).convert("RGB"))
    if not np.array_equal(canvas, decoded_tga):
        raise RuntimeError("Decoded TGA pixels differ from the source RGB image")
    header = tga_path.read_bytes()[:18]
    if header[16] != 24:
        raise RuntimeError(f"Expected 24-bit TGA, got {header[16]} bits")

    renderer = ObjMultiViewRenderer(MESH_PATH)
    render_paths = renderer.render(image, OUTPUT_DIR, "ak47_hd_uv_calibration_local")
    manifest = {
        "status": "local_calibration_ready_pending_workshop_screenshots",
        "contract": "known-good new CS2 HD OBJ UV; normal displayed orientation; no global V flip",
        "size": [SIZE, SIZE],
        "mode": "RGB",
        "tga_bits_per_pixel": int(header[16]),
        "tga_image_descriptor": int(header[17]),
        "decoded_png_tga_pixels_identical": True,
        "mesh": {"path": str(MESH_PATH.relative_to(ROOT)), "sha256": sha256(MESH_PATH), "triangle_count": int(len(mesh.vertex_faces))},
        "references": {
            "viper_uv": {"path": str(REFERENCE_PATH.relative_to(ROOT)), "sha256": sha256(REFERENCE_PATH)},
            "local_wireframe": {"path": str(WIREFRAME_PATH.relative_to(ROOT)), "sha256": sha256(WIREFRAME_PATH)},
        },
        "outputs": {
            "png": {"path": str(png_path.relative_to(ROOT)), "sha256": sha256(png_path)},
            "tga": {"path": str(tga_path.relative_to(ROOT)), "sha256": sha256(tga_path)},
            "local_renders": [str(path.relative_to(ROOT)) for path in render_paths],
        },
        "major_islands": island_records,
        "workshop_settings": {
            "finish_style": "Custom Paint Job", "scale": 1, "offset_u": 0, "offset_v": 0,
            "rotation": 0, "ignore_weapon_size_scale": True, "wear": "minimum",
        },
        "required_workshop_evidence": ["left screenshot", "right screenshot", "top screenshot"],
    }
    (OUTPUT_DIR / "calibration_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest["outputs"], indent=2))


if __name__ == "__main__":
    main()
