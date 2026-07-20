# Garden engine validation

These images preserve the final validation of the exact human-selected garden
case (`artwork_02`, *Ornamental Tapestry*) after formal Route B execution.

- `workshop_left.png`, `workshop_right.png`, and `workshop_top.png` are fixed
  CS2 Workshop views of the 2048 Custom Paint Job TGA.
- `workshop_item_editor.png` records the import contract: Custom Paint Job,
  texture scale `1.0`, zero rotation and offsets, Ignore Weapon Size Scale
  enabled, and no custom normal map.
- `in_game_detail.png` and `in_game_play_view.png` show the same texture in
  first-person inspection and normal play views.

The evidence validates base-colour placement, coverage, readability, and the
export/import path. It does not claim that SkinSmith generated normal,
roughness, metallic, height, or displacement channels.

The Checkpoint 3 comparison also preserves an important design result:
`artwork_03` had the highest automatic preview total (`0.8955`), while the user
selected `artwork_02` (`0.8293`). Automatic scores screen technical feasibility
and support recommendations; they do not replace human aesthetic choice.
