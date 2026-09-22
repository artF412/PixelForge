"""Core image-resizing logic, kept separate from the GUI so it has no
dependency on tkinter and can be reused or unit-tested on its own.

Two backends are used depending on the source format:
  - .exr is handled by ``oiiotool`` (via subprocess), since Pillow cannot
    read/write OpenEXR files.
  - everything else (jpg, png, bmp, tif/tiff, webp) is handled in-process
    with Pillow, which is faster and needs no external binary.
"""
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from PIL import Image

EXR_EXTENSIONS = {".exr"}
PILLOW_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SUPPORTED_EXTENSIONS = EXR_EXTENSIONS | PILLOW_EXTENSIONS

FORMAT_EXTENSION = {
    "JPG": ".jpg",
    "PNG": ".png",
    "TIFF": ".tiff",
}


class ResizeError(RuntimeError):
    """Raised for any expected, user-facing failure while resizing."""


def resource_path(relative_path: str) -> str:
    """Resolve a path to a bundled resource.

    Works both when running from source and when frozen into a single
    executable by PyInstaller (which extracts bundled files under
    ``sys._MEIPASS`` at runtime).
    """
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def find_oiiotool() -> Optional[str]:
    """Locate an oiiotool executable to use for .exr files.

    Search order:
      1. Bundled next to this script / inside the frozen exe (``bin/oiiotool.exe``).
      2. The ``oiiotool.exe`` that ships inside an installed ``OpenImageIO``
         Python package (useful when running from source in a venv).
      3. Whatever ``oiiotool`` is available on PATH.
    """
    exe_name = "oiiotool.exe" if os.name == "nt" else "oiiotool"

    bundled = resource_path(os.path.join("bin", exe_name))
    if os.path.isfile(bundled):
        return bundled

    try:
        import OpenImageIO
        candidate = os.path.join(os.path.dirname(OpenImageIO.__file__), "bin", exe_name)
        if os.path.isfile(candidate):
            return candidate
    except ImportError:
        pass

    return shutil.which("oiiotool")


@dataclass
class ResizeJob:
    input_path: str
    output_path: str
    width: int
    height: int
    keep_aspect: bool


def _compute_target_size(src_w: int, src_h: int, width: int, height: int, keep_aspect: bool) -> Tuple[int, int]:
    if not keep_aspect:
        return width, height
    scale = min(width / src_w, height / src_h)
    return max(1, round(src_w * scale)), max(1, round(src_h * scale))


def resize_with_pillow(job: ResizeJob) -> None:
    with Image.open(job.input_path) as img:
        target_w, target_h = _compute_target_size(img.width, img.height, job.width, job.height, job.keep_aspect)
        resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

        os.makedirs(os.path.dirname(job.output_path) or ".", exist_ok=True)

        save_kwargs = {}
        if job.output_path.lower().endswith((".jpg", ".jpeg")):
            if resized.mode in ("RGBA", "P", "LA"):
                resized = resized.convert("RGB")
            save_kwargs["quality"] = 95

        resized.save(job.output_path, **save_kwargs)


def resize_with_oiiotool(job: ResizeJob, oiiotool_path: str) -> None:
    size_arg = f"{job.width}x{job.height}"
    command = [oiiotool_path, job.input_path]
    if job.keep_aspect:
        command += ["--fit", size_arg]
    else:
        command += ["--resize", size_arg]

    os.makedirs(os.path.dirname(job.output_path) or ".", exist_ok=True)
    command += ["-o", job.output_path]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise ResizeError(result.stderr.strip() or f"oiiotool failed on {job.input_path}")


def process_image(job: ResizeJob, oiiotool_path: Optional[str]) -> None:
    ext = os.path.splitext(job.input_path)[1].lower()
    if ext in EXR_EXTENSIONS:
        if not oiiotool_path:
            raise ResizeError(
                "ไม่พบ oiiotool สำหรับประมวลผลไฟล์ .exr "
                "(โปรแกรมรุ่นนี้ควรมี oiiotool.exe แนบมาด้วย)"
            )
        resize_with_oiiotool(job, oiiotool_path)
    else:
        resize_with_pillow(job)


def gather_input_files(input_path: str, batch_mode: bool) -> List[str]:
    if not batch_mode:
        return [input_path]

    files = []
    for name in sorted(os.listdir(input_path)):
        ext = os.path.splitext(name)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            files.append(os.path.join(input_path, name))
    return files


def build_output_path(input_file: str, output_folder: str, output_format: str) -> str:
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    ext = os.path.splitext(input_file)[1].lower()
    if output_format != "ORIGINAL":
        ext = FORMAT_EXTENSION[output_format]
    return os.path.join(output_folder, base_name + ext)


def run_batch(
    input_path: str,
    output_folder: str,
    width: int,
    height: int,
    keep_aspect: bool,
    batch_mode: bool,
    output_format: str = "ORIGINAL",
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Tuple[int, List[str]]:
    """Resize one file or a whole folder. Returns (total_files, list_of_error_strings)."""
    oiiotool_path = find_oiiotool()
    files = gather_input_files(input_path, batch_mode)
    if not files:
        raise ResizeError(
            "ไม่พบไฟล์ภาพที่รองรับ (.exr .jpg .jpeg .png .bmp .tif .tiff .webp)"
        )

    os.makedirs(output_folder, exist_ok=True)

    total = len(files)
    errors: List[str] = []
    for index, input_file in enumerate(files, start=1):
        output_path = build_output_path(input_file, output_folder, output_format)
        job = ResizeJob(input_file, output_path, width, height, keep_aspect)
        if progress_callback:
            progress_callback(index, total, os.path.basename(input_file))
        try:
            process_image(job, oiiotool_path)
        except Exception as exc:
            errors.append(f"{os.path.basename(input_file)}: {exc}")

    return total, errors
