@echo off
setlocal
cd /d "%~dp0"

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
  echo Python 3.10 or newer is required. Ensure python points to Python 3.10+.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

set "ICON_PATH=%CD%\assets\icon.ico"
if exist "dist\Smoke Break.exe" (
  del /f /q "dist\Smoke Break.exe"
)

if exist "assets\icon.ico" (
  ".venv\Scripts\pyinstaller.exe" --noconfirm --clean --onefile --windowed --name "Smoke Break" --icon "%ICON_PATH%" --add-data "assets;assets" main.py
) else (
  echo assets\icon.ico not found; building without a custom icon.
  ".venv\Scripts\pyinstaller.exe" --noconfirm --clean --onefile --windowed --name "Smoke Break" --add-data "assets;assets" main.py
)

endlocal
