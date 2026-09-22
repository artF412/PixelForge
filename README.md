# PixelForge

A GUI tool for resizing images — single files or whole folders — using ready-made presets (up to 4K) or a custom size.

Supported formats: `.exr` `.jpg` `.jpeg` `.png` `.bmp` `.tif` `.tiff` `.webp`

## For end users (nothing to install)

Just double-click `dist\PixelForge.exe`. No need to install Python or anything else — everything (including `oiiotool` for `.exr` files) is bundled into the `.exe`.

How to use:
1. Choose a mode: **Batch Folder** or **Single File**
2. Browse for the source file/folder and the output folder
3. Pick a size from the Preset list, or choose "Custom" and enter Width/Height yourself
4. Check "Keep aspect ratio" if you don't want the image distorted (it will fit within the target box while preserving the original proportions)
5. Choose an Output format if you want to convert to JPG/PNG/TIFF (or leave it as "Original" to keep the source extension)
6. Click **Convert / Resize**

## Running from source

```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python main.py
```

## Known limitations
- `.exr` files are processed via `oiiotool` (an external process); everything else (jpg/png/bmp/tif/webp) is processed directly in-app with Pillow.
- Converting `.exr` (linear/HDR color data) straight to `.jpg`/`.png` (sRGB) without any color adjustment may look darker/brighter than what you see in a color-managed viewer (e.g. Nuke, DJV). If you need a preview that matches production color, you may need additional tone mapping afterward (not included in this version).
- Currently built for Windows only (`oiiotool.exe`) — to distribute on macOS/Linux you'd need to bundle that OS's `OpenImageIO` binary instead.

## License

MIT License — see [LICENSE](LICENSE)
