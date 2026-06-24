# Smoke Break

Small Windows tray break timer with custom audio reminders, fade-in playback, and simple daily stats.

The application source is in [`smoke_break/`](smoke_break/).

## Quick Start

```bat
cd smoke_break
python -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" main.py
```

## Build

```bat
cd smoke_break
build_exe.bat
```

The generated executable is created under `smoke_break/dist/` and should not be committed to source control.

## What To Commit

Commit the source files, documentation, default data JSON files, and asset placeholders. Do not commit virtual environments, build folders, generated executables, caches, or local runtime artifacts.

See [`smoke_break/README.md`](smoke_break/README.md) for full usage and packaging details.

## License

No license file is included yet. Add a `LICENSE` file before publishing if you want to define how other people may use or redistribute the code.
