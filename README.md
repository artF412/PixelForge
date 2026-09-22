# PixelForge

A GUI tool for resizing images — single files or whole folders — using ready-made presets (up to 4K) or a custom size.

Supported formats: `.exr` `.jpg` `.jpeg` `.png` `.bmp` `.tif` `.tiff` `.webp`

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
