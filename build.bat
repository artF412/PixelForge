@echo off
REM Builds a single, standalone Windows .exe for PixelForge.
REM Run this AFTER setting up the venv (see README.md):
REM     python -m venv venv
REM     venv\Scripts\pip install -r requirements.txt pyinstaller
REM
REM The resulting dist\PixelForge.exe needs nothing installed on the
REM machine it is copied to - oiiotool.exe and its DLLs are bundled inside it.

setlocal

set VENV_PY=venv\Scripts\python.exe
if not exist "%VENV_PY%" (
    echo [ERROR] venv not found. Run:
    echo     python -m venv venv
    echo     venv\Scripts\pip install -r requirements.txt pyinstaller
    exit /b 1
)

for /f "delims=" %%i in ('%VENV_PY% -c "import OpenImageIO, os; print(os.path.dirname(OpenImageIO.__file__))"') do set OIIO_DIR=%%i
set OIIO_BIN=%OIIO_DIR%\bin

if not exist "%OIIO_BIN%\oiiotool.exe" (
    echo [ERROR] oiiotool.exe not found under %OIIO_BIN%
    echo Make sure "pip install OpenImageIO" succeeded in the venv.
    exit /b 1
)

if not exist "branding\pixelforge.ico" (
    echo [ERROR] branding\pixelforge.ico not found.
    exit /b 1
)

"%VENV_PY%" -m PyInstaller --noconfirm --onefile --windowed --name "PixelForge" ^
    --icon "branding\pixelforge.ico" ^
    --add-data "%OIIO_BIN%;bin" ^
    --add-data "branding\pixelforge.ico;branding" ^
    main.py

if errorlevel 1 (
    echo [ERROR] Build failed.
    exit /b 1
)

echo.
echo Build complete: dist\PixelForge.exe
echo This single file can be copied to any Windows PC and run directly.
endlocal
