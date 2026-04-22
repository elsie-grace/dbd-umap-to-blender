# dbd-umap-to-blender

A Python script for converting Unreal Engine `.umap` files into Blender, including static meshes and lights.

## Prerequisites

- **Blender** (tested with 5.1.1)
- **[FModel](https://github.com/4sval/FModel)** - for extracting and exporting Unreal Engine assets
- **[UEFormat Blender addon](https://github.com/h4lfheart/UEFormat)** - for importing `.uemodel` files into Blender

## How to use

1. Find the .umap file in FModel that you want to convert to blender. Export it as .json (Right-click -> Save properties).
2. Open Blender and create a new scene (or use an existing one)
3. Open the **Scripting** workspace (top menu bar)
4. Click `Open` in the text editor and select downloaded `umap.py`. Or click `New` and just copy-paste the script inside the text editor.
5. Edit the settings section at the top of `umap.py`:

```python
# ---- SETTINGS ----
SCALE = 0.01
LIGHT_POWER_MULTIPLIER = 10
ENABLE_PLANES = False
JSON_PATH = r"G:\FModel\Export\DeadByDaylight\Content\Maps\LobbyKetchup.json"
MESH_FOLDER = r"G:\FModel\Export"
```

| Parameter | Description |
|-----------|-------------|
| `SCALE` | Scale multiplier for objects positions. Must match the object scale (default: 0.01 to match ueformat) |
| `LIGHT_POWER_MULTIPLIER` | Multiplier for light intensity (default: 10) |
| `ENABLE_PLANES` | Whether to import plane meshes (default: False) |
| `JSON_PATH` | **Full path to the exported .umap JSON file** |
| `MESH_FOLDER` | **Must match your FModel Output Directory exactly** |
6. Click `Run Script` or press `Alt + P`
7. (Optional) You can select all created objects and use [FFUS](https://gitlab.com/Frutto47/ffus) to setup the materials/textures.