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

## For developers (editing code / rebuilding)

### File structure
- `main.py` — GUI (tkinter)
- `resizer.py` — image resizing logic (kept separate from the GUI so it's easy to test/reuse)
- `requirements.txt` — dependencies for running from source
- `build.bat` — script that builds a single-file `.exe`
- `branding/pixelforge.ico` — the app icon (used both as the `.exe` icon and the window/taskbar icon at runtime). To change the logo, replace this file (export a square PNG at least 256x256, then convert to `.ico` with Pillow: `Image.open(...).convert("RGBA").save("branding/pixelforge.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])`)

### Run from source
```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python main.py
```

### Build a distributable .exe
```bat
venv\Scripts\pip install pyinstaller
build.bat
```
This produces `dist\PixelForge.exe` — copy it to any machine and run it directly (tested to work without Python/OpenImageIO installed on the target machine).

Note: `build.bat` automatically pulls `oiiotool.exe` and its related DLLs from the venv (installed alongside the `OpenImageIO` package from PyPI) and bundles them into the `.exe` — no need to download OpenImageIO separately.

## Known limitations
- `.exr` files are processed via `oiiotool` (an external process); everything else (jpg/png/bmp/tif/webp) is processed directly in-app with Pillow.
- Converting `.exr` (linear/HDR color data) straight to `.jpg`/`.png` (sRGB) without any color adjustment may look darker/brighter than what you see in a color-managed viewer (e.g. Nuke, DJV). If you need a preview that matches production color, you may need additional tone mapping afterward (not included in this version).
- Currently built for Windows only (`oiiotool.exe`) — to distribute on macOS/Linux you'd need to bundle that OS's `OpenImageIO` binary instead.

## License

MIT License — see [LICENSE](LICENSE)
