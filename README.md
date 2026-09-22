# PixelForge

โปรแกรม GUI สำหรับปรับขนาดภาพ รองรับทั้งไฟล์เดียวและทั้งโฟลเดอร์ ใช้ preset ขนาดสำเร็จรูป (จนถึง 4K) หรือกำหนดขนาดเอง

รองรับไฟล์: `.exr` `.jpg` `.jpeg` `.png` `.bmp` `.tif` `.tiff` `.webp`

## สำหรับผู้ใช้ทั่วไป (ไม่ต้องติดตั้งอะไร)

ดับเบิลคลิก `dist\PixelForge.exe` ได้เลย ไม่ต้องลง Python หรือโปรแกรมอื่นเพิ่ม เพราะทุกอย่าง (รวมถึง oiiotool สำหรับไฟล์ .exr) ถูก build ฝังไว้ในไฟล์ .exe แล้ว

วิธีใช้ในโปรแกรม:
1. เลือกโหมด: **ทั้งโฟลเดอร์** หรือ **ไฟล์เดียว**
2. Browse เลือกไฟล์/โฟลเดอร์ต้นทาง และโฟลเดอร์ปลายทาง
3. เลือกขนาดจาก Preset หรือเลือก "กำหนดเอง (Custom)" แล้วใส่ Width/Height เอง
4. ติ๊ก "รักษาสัดส่วนภาพ" ถ้าไม่ต้องการให้ภาพบิดเบี้ยว (ย่อ/ขยายให้พอดีกรอบโดยรักษาสัดส่วนเดิม)
5. เลือก Output format ถ้าต้องการแปลงเป็น JPG/PNG/TIFF (หรือเลือก "เหมือนไฟล์ต้นฉบับ" เพื่อคงนามสกุลเดิม)
6. กด **Convert / Resize**

## สำหรับ Dev (แก้โค้ด / build ใหม่)

### โครงสร้างไฟล์
- `main.py` — หน้าจอ GUI (tkinter)
- `resizer.py` — logic การปรับขนาดภาพ (แยกออกจาก GUI เพื่อให้ทดสอบ/นำกลับมาใช้ง่าย)
- `requirements.txt` — dependency สำหรับรันจาก source
- `build.bat` — สคริปต์ build เป็น `.exe` แบบไฟล์เดียว
- `branding/pixelforge.ico` — ไอคอนโปรแกรม (ใช้ทั้งเป็นไอคอนไฟล์ .exe และไอคอนหน้าต่าง/taskbar ตอนรัน) ถ้าจะเปลี่ยนโลโก้ใหม่ ให้แทนไฟล์นี้ (แนะนำ export มาเป็น PNG สี่เหลี่ยมจัตุรัสอย่างน้อย 256x256 ก่อน แล้วแปลงเป็น .ico ด้วย Pillow: `Image.open(...).convert("RGBA").save("branding/pixelforge.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])`)

### รันจาก source
```bat
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python main.py
```

### Build เป็น .exe แจกจ่าย
```bat
venv\Scripts\pip install pyinstaller
build.bat
```
ได้ไฟล์ `dist\PixelForge.exe` — ก็อปไปเครื่องไหนก็เปิดใช้ได้ทันที (ทดสอบแล้วว่าทำงานได้โดยไม่ต้องมี Python/OpenImageIO ติดตั้งอยู่ในเครื่องปลายทาง)

หมายเหตุ: `build.bat` จะดึง `oiiotool.exe` และ DLL ที่เกี่ยวข้องจาก venv (ติดตั้งมาพร้อมกับแพ็กเกจ `OpenImageIO` บน PyPI) มาฝังไว้ใน .exe ให้อัตโนมัติ ไม่ต้องดาวน์โหลด OpenImageIO แยกเอง

## ข้อจำกัดที่ควรรู้
- ไฟล์ `.exr` ประมวลผลผ่าน `oiiotool` (external process) ส่วนไฟล์อื่น (jpg/png/bmp/tif/webp) ประมวลผลด้วย Pillow ในตัวโปรแกรมโดยตรง
- การแปลง `.exr` (ข้อมูลสี linear/HDR) เป็น `.jpg`/`.png` (sRGB) ตรงๆ โดยไม่ผ่านการปรับสี อาจได้ภาพที่มืด/สว่างผิดจากที่เห็นใน viewer ที่มี color management (เช่น Nuke, DJV) — ถ้าต้องการ preview ที่สีตรงกับที่ใช้ในงานจริง อาจต้องปรับ tone mapping เพิ่มเติมภายหลัง (ยังไม่รวมอยู่ในเวอร์ชันนี้)
- ตอนนี้ build ไว้สำหรับ Windows เท่านั้น (`oiiotool.exe`) — ถ้าจะแจกบน macOS/Linux ต้องดาวน์โหลด `OpenImageIO` binary ของ OS นั้นๆ มาแทน

## License

MIT License — ดูรายละเอียดใน [LICENSE](LICENSE)
