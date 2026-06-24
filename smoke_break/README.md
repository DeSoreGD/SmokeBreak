# Smoke Break

Smoke Break is a small Windows tray app for neutral break timing, audio reminders, and simple daily break tracking. It is a timer and tracking utility; app text avoids phrasing that encourages smoking.

## Features

- Windows system tray integration with Show / Hide, Start Timer, Pause / Resume, Reset, Stop Audio, Settings, and Quit.
- Compact dark popover window near the tray icon, with bottom-right fallback.
- Custom dark title bar with explicit Hide to tray control.
- Countdown timer with Short, Normal, Long, and Custom durations.
- Small custom popup when the timer ends, separate from the main app window.
- Popup image can come from embedded audio artwork, a user-selected image, or the bundled default image.
- Pause, resume, reset, restart, and delay actions.
- Custom audio playback through QtMultimedia.
- Long audio support, optional fade-in, and optional play-for-duration mode.
- Daily stats for Took Break, Skipped, and Delays.
- Optional daily break limit warning.
- Portable JSON storage next to the app.

## Requirements

- Windows
- Python 3.10 or newer
- PySide6
- PyInstaller for `.exe` builds

## Run From Source

```bat
cd "C:\*your path*\Smoke Break\smoke_break"
python -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" main.py
```

## Build Exe

```bat
cd "C:\*your path*\Smoke Break\smoke_break"
build_exe.bat
```

Output:

```text
dist\Smoke Break.exe
```

`build_exe.bat` uses `assets\icon.ico` for the executable, main window, and tray icon. For PyInstaller onefile builds it also bundles the assets folder with `--add-data "assets;assets"`.

## Tray Behavior

Use `Hide to tray` or the `X` button in the app title bar to hide the window without quitting. Use the tray icon or tray menu to show it again. Use `Quit` in the tray menu to fully exit.

## Storage

Settings and stats are stored relative to the source folder or packaged executable folder:

```text
data\settings.json
data\stats.json
```

If either JSON file is missing or corrupt, the app recreates it with safe defaults. Corrupt files are renamed with a `.corrupt-YYYYMMDDHHMMSS.json` suffix when possible.

## Supported Audio

The file picker allows:

- `.mp3`
- `.wav`
- `.m4a`
- `.ogg`

Actual playback support depends on QtMultimedia and installed Windows codecs. MP3 and WAV are the safest options.

## Python 3.10 Notes

This project is compatible with Python 3.10.6. `requirements.txt` pins PySide6 to the 6.7 line so `pip` does not select a future PySide6 release that may drop Python 3.10 support.

## Known Limitations

- No Windows toast notification is implemented; the popover is the reminder.
- No detailed event history is kept; only the current daily stats are stored.
- If `assets\icon.ico` is missing, the source app falls back to a generated runtime icon and the build script creates an executable without a custom icon.
