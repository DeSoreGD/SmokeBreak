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

if exist "assets\icon.ico" (
  ".venv\Scripts\pyinstaller.exe" --noconfirm --onefile --windowed --name "Smoke Break" --icon "assets\icon.ico" --add-data "assets;assets" main.py
) else (
  echo assets\icon.ico not found; building without a custom icon.
  ".venv\Scripts\pyinstaller.exe" --noconfirm --onefile --windowed --name "Smoke Break" main.py
)

endlocal
