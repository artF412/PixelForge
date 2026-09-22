"""PixelForge - GUI front-end.

Lets a user resize either a single image or a whole folder of images
(.exr, .jpg, .png, .bmp, .tif/.tiff, .webp) to a preset or custom size.
See resizer.py for the actual resizing logic.
"""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from resizer import SUPPORTED_EXTENSIONS, ResizeError, find_oiiotool, resource_path, run_batch

ICON_PATH = resource_path(os.path.join("branding", "pixelforge.ico"))

PRESETS = [
    ("HD (1280 x 720)", 1280, 720),
    ("Full HD (1920 x 1080)", 1920, 1080),
    ("QHD / 2K (2560 x 1440)", 2560, 1440),
    ("2K DCI (2048 x 1080)", 2048, 1080),
    ("4K UHD (3840 x 2160)", 3840, 2160),
    ("4K DCI (4096 x 2160)", 4096, 2160),
    ("กำหนดเอง (Custom)", None, None),
]
CUSTOM_PRESET_NAME = PRESETS[-1][0]
DEFAULT_PRESET_NAME = PRESETS[4][0]  # 4K UHD

OUTPUT_FORMAT_MAP = {
    "เหมือนไฟล์ต้นฉบับ (Original)": "ORIGINAL",
    "JPG": "JPG",
    "PNG": "PNG",
    "TIFF": "TIFF",
}

IMAGE_FILETYPES = [
    ("Image files", "*.exr *.jpg *.jpeg *.png *.bmp *.tif *.tiff *.webp"),
    ("All files", "*.*"),
]


class ResizeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PixelForge")
        self.geometry("640x620")
        self.minsize(640, 620)
        self._set_icon()

        self.mode_var = tk.StringVar(value="batch")
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.preset_var = tk.StringVar(value=DEFAULT_PRESET_NAME)
        self.width_var = tk.StringVar(value="3840")
        self.height_var = tk.StringVar(value="2160")
        self.keep_aspect_var = tk.BooleanVar(value=True)
        self.format_var = tk.StringVar(value="เหมือนไฟล์ต้นฉบับ (Original)")

        self.message_queue = queue.Queue()
        self.worker_thread = None

        self._build_ui()
        self._check_oiiotool()
        self.after(100, self._poll_queue)

    # ---------------------------------------------------------------- UI --
    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        mode_frame = ttk.LabelFrame(self, text="โหมดการทำงาน (Mode)")
        mode_frame.pack(fill="x", **pad)
        ttk.Radiobutton(
            mode_frame, text="ทั้งโฟลเดอร์ (Batch Folder)", value="batch",
            variable=self.mode_var, command=self._on_mode_change,
        ).pack(side="left", padx=10, pady=6)
        ttk.Radiobutton(
            mode_frame, text="ไฟล์เดียว (Single File)", value="single",
            variable=self.mode_var, command=self._on_mode_change,
        ).pack(side="left", padx=10, pady=6)

        input_frame = ttk.LabelFrame(self, text="ไฟล์ / โฟลเดอร์ต้นทาง (Input)")
        input_frame.pack(fill="x", **pad)
        ttk.Entry(input_frame, textvariable=self.input_var).pack(
            side="left", fill="x", expand=True, padx=(10, 6), pady=8
        )
        ttk.Button(input_frame, text="Browse...", command=self._browse_input).pack(
            side="left", padx=(0, 10)
        )

        output_frame = ttk.LabelFrame(self, text="โฟลเดอร์ปลายทาง (Output Folder)")
        output_frame.pack(fill="x", **pad)
        ttk.Entry(output_frame, textvariable=self.output_var).pack(
            side="left", fill="x", expand=True, padx=(10, 6), pady=8
        )
        ttk.Button(output_frame, text="Browse...", command=self._browse_output).pack(
            side="left", padx=(0, 10)
        )

        size_frame = ttk.LabelFrame(self, text="ขนาดภาพ (Size)")
        size_frame.pack(fill="x", **pad)

        preset_row = ttk.Frame(size_frame)
        preset_row.pack(fill="x", padx=10, pady=(8, 4))
        ttk.Label(preset_row, text="Preset:").pack(side="left")
        preset_combo = ttk.Combobox(
            preset_row, textvariable=self.preset_var, state="readonly",
            values=[p[0] for p in PRESETS], width=28,
        )
        preset_combo.pack(side="left", padx=8)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        custom_row = ttk.Frame(size_frame)
        custom_row.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(custom_row, text="Width:").pack(side="left")
        self.width_entry = ttk.Entry(custom_row, textvariable=self.width_var, width=8)
        self.width_entry.pack(side="left", padx=(4, 12))
        ttk.Label(custom_row, text="Height:").pack(side="left")
        self.height_entry = ttk.Entry(custom_row, textvariable=self.height_var, width=8)
        self.height_entry.pack(side="left", padx=(4, 0))

        ttk.Checkbutton(
            size_frame, text="รักษาสัดส่วนภาพ (Keep aspect ratio)",
            variable=self.keep_aspect_var,
        ).pack(anchor="w", padx=10, pady=(0, 8))

        format_row = ttk.Frame(size_frame)
        format_row.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(format_row, text="Output format:").pack(side="left")
        ttk.Combobox(
            format_row, textvariable=self.format_var, state="readonly",
            values=list(OUTPUT_FORMAT_MAP.keys()), width=28,
        ).pack(side="left", padx=8)

        self._on_preset_change()

        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", **pad)
        self.convert_button = ttk.Button(
            action_frame, text="Convert / Resize", command=self._start_resize
        )
        self.convert_button.pack(side="left")
        self.status_label = ttk.Label(action_frame, text="พร้อมทำงาน (Ready)")
        self.status_label.pack(side="left", padx=12)

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill="x", **pad)

        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=True, **pad)
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=12, state="disabled", wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)

    def _set_icon(self):
        if os.path.isfile(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except tk.TclError:
                pass  # e.g. running on a platform that can't load .ico

    def _check_oiiotool(self):
        if not find_oiiotool():
            self._log(
                "[คำเตือน] ไม่พบ oiiotool ในเครื่องนี้ - จะไม่สามารถแปลงไฟล์ .exr ได้ "
                "(ยังใช้กับ JPG/PNG/BMP/TIFF/WEBP ได้ตามปกติ)"
            )

    # -------------------------------------------------------- event handlers --
    def _on_mode_change(self):
        self.input_var.set("")

    def _on_preset_change(self, event=None):
        selected = self.preset_var.get()
        is_custom = selected == CUSTOM_PRESET_NAME
        state = "normal" if is_custom else "disabled"
        self.width_entry.configure(state=state)
        self.height_entry.configure(state=state)
        if not is_custom:
            for name, w, h in PRESETS:
                if name == selected:
                    self.width_var.set(str(w))
                    self.height_var.set(str(h))
                    break

    def _browse_input(self):
        if self.mode_var.get() == "batch":
            path = filedialog.askdirectory(title="เลือกโฟลเดอร์ต้นทาง")
        else:
            path = filedialog.askopenfilename(title="เลือกไฟล์ภาพ", filetypes=IMAGE_FILETYPES)
        if path:
            self.input_var.set(path)

    def _browse_output(self):
        path = filedialog.askdirectory(title="เลือกโฟลเดอร์ปลายทาง")
        if path:
            self.output_var.set(path)

    # -------------------------------------------------------- run / validate --
    def _start_resize(self):
        input_path = self.input_var.get().strip()
        output_folder = self.output_var.get().strip()
        batch_mode = self.mode_var.get() == "batch"

        if not input_path:
            messagebox.showerror("Error", "กรุณาเลือกไฟล์หรือโฟลเดอร์ต้นทาง")
            return
        if batch_mode and not os.path.isdir(input_path):
            messagebox.showerror("Error", "โฟลเดอร์ต้นทางไม่ถูกต้อง")
            return
        if not batch_mode and not os.path.isfile(input_path):
            messagebox.showerror("Error", "ไฟล์ต้นทางไม่ถูกต้อง")
            return
        if not batch_mode and os.path.splitext(input_path)[1].lower() not in SUPPORTED_EXTENSIONS:
            messagebox.showerror(
                "Error", "รองรับเฉพาะไฟล์ .exr .jpg .jpeg .png .bmp .tif .tiff .webp"
            )
            return
        if not output_folder:
            messagebox.showerror("Error", "กรุณาเลือกโฟลเดอร์ปลายทาง")
            return

        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            if width <= 0 or height <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "กรุณาระบุ Width / Height เป็นตัวเลขที่มากกว่า 0")
            return

        self.convert_button.configure(state="disabled")
        self.status_label.configure(text="กำลังประมวลผล...")
        self.progress.configure(value=0, maximum=100)
        self._clear_log()

        output_format = OUTPUT_FORMAT_MAP[self.format_var.get()]
        keep_aspect = self.keep_aspect_var.get()

        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(input_path, output_folder, width, height, keep_aspect, batch_mode, output_format),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_worker(self, input_path, output_folder, width, height, keep_aspect, batch_mode, output_format):
        def on_progress(index, total, filename):
            self.message_queue.put(("progress", index, total, filename))

        try:
            total, errors = run_batch(
                input_path, output_folder, width, height, keep_aspect, batch_mode,
                output_format=output_format, progress_callback=on_progress,
            )
            self.message_queue.put(("done", total, errors))
        except ResizeError as exc:
            self.message_queue.put(("fatal", str(exc)))
        except Exception as exc:  # unexpected errors should still surface, not vanish
            self.message_queue.put(("fatal", f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {exc}"))

    # -------------------------------------------------------------- queue --
    def _poll_queue(self):
        try:
            while True:
                message = self.message_queue.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _handle_message(self, message):
        kind = message[0]
        if kind == "progress":
            _, index, total, filename = message
            self.progress.configure(maximum=total, value=index)
            self.status_label.configure(text=f"กำลังประมวลผล {index}/{total}: {filename}")
            self._log(f"[{index}/{total}] Resizing {filename}...")
        elif kind == "done":
            _, total, errors = message
            self.progress.configure(value=total)
            ok = total - len(errors)
            self.status_label.configure(text=f"เสร็จสิ้น: {ok}/{total} ไฟล์สำเร็จ")
            self._log(f"เสร็จสิ้น {ok}/{total} ไฟล์")
            for error in errors:
                self._log(f"[ERROR] {error}")
            self.convert_button.configure(state="normal")
            if errors:
                messagebox.showwarning(
                    "Done with errors",
                    f"เสร็จสิ้นแต่มี {len(errors)} ไฟล์ที่ผิดพลาด ดู Log สำหรับรายละเอียด",
                )
            else:
                messagebox.showinfo("Done", f"ปรับขนาดภาพสำเร็จ {ok} ไฟล์")
        elif kind == "fatal":
            _, error_message = message
            self.status_label.configure(text="เกิดข้อผิดพลาด")
            self._log(f"[FATAL] {error_message}")
            self.convert_button.configure(state="normal")
            messagebox.showerror("Error", error_message)

    def _log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


def main():
    app = ResizeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
