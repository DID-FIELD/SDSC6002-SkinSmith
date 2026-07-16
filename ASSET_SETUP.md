# Official asset setup

The code repository must not redistribute Valve geometry, UV sheets, or game files.

Start from Valve's official Workshop Resources page:

https://www.counter-strike.net/workshop/workshopresources

The page currently exposes two separate packages. Download the new CS2 weapon
geometry from:

https://media.steampowered.com/apps/csgo/images/workshop/workshop/cs2_weapon_model_geometry.zip

Optionally download the legacy Workbench materials, examples, and UV sheets from:

https://media.steampowered.com/apps/csgo/workshop/workbench_materials.zip?v=103

Place the archives under:

```text
project/third_party/downloads/
```

For the initial AK-47 case study, extract `weapon_rif_ak47.obj` to:

```text
project/third_party/valve_geometry/weapon_rif_ak47.obj
```

The current local workspace has already completed this step. Both the ZIP and the
extracted OBJ remain ignored by Git.

The optional Workbench package contains weapon UV sheets such as:

```text
project/third_party/valve_workbench/UVSheets/ak-47.tga
project/third_party/valve_workbench/UVSheets/m4a4.tga
```

## Asset-version rule

Do not assume that an official UV sheet matches every model with the same weapon
name. Valve lists the legacy Workbench package and the new CS2 geometry as
separate downloads. Local inspection confirms that the legacy AK-47 sheet/model
and the new CS2 AK-47 OBJ use different UV layouts.

Every experiment must therefore bind these fields as one versioned asset:

```text
asset_id + mesh_path + mesh_version + uv_source + texture_size + export_profile
```

Use one of the following valid pairings:

- legacy Workbench OBJ + its corresponding official UV sheet;
- new CS2 OBJ + a UV atlas derived from that same OBJ;
- another game's mesh + UV data exposed by its own `GameAssetAdapter`.

Never combine the legacy AK-47 UV sheet with the new CS2 AK-47 geometry. When the
Workbench target version is uncertain, import a component-colour calibration
texture first and identify the active layout before producing formal results.

## Portability policy

The official sheet is a convenient, artist-readable input for the Valve case
study, not a dependency of the SkinSmith method. The core implementation derives
paintable coverage, UV islands, and 3D-corresponding UV seam pairs directly from
the selected OBJ. This fallback is required for weapons or games that do not
publish ready-made UV sheets. Human semantic labels such as stock, receiver, and
magazine are stored as adapter masks layered on top of the derived atlas.

For an exact, non-tiling Custom Paint texture, the final export target is
2048 x 2048 TGA. Lower-resolution PNG diagnostics may be used during development,
but they are not the formal Workbench export.

Do not commit that directory. The project `.gitignore` excludes all of
`third_party/`.
