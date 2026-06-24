
# Smoke Break

**Smoke Break** is a small Windows tray timer for managing smoke break intervals with custom audio reminders, smooth fade-in playback, and simple daily break stats.

It runs quietly in the system tray, opens as a compact popover near the tray area, and lets you use your own audio file when the timer ends.

## Features

* Windows system tray app
* Compact dark timer UI
* Default 90-minute timer
* Custom timer duration
* Timer presets
* Start, pause, resume, reset, and restart controls
* Custom audio file at timer end
* Smooth audio fade-in
* Long audio playback support
* Volume control
* “Took Break”, “Skipped”, and “Delay” actions
* Simple daily stats
* Optional daily break limit
* Portable JSON settings
* Buildable as a standalone `.exe`

## Screenshots

<img width="430" height="700" alt="Smoke_Break_7w4bW36kDq" src="https://github.com/user-attachments/assets/ad6eee4d-df1e-4df8-99e0-855ffeecb44a" /><img width="430" height="700" alt="Smoke_Break_JyRm2ptA2k" src="https://github.com/user-attachments/assets/04fe1f7d-87d7-4b03-b76e-fb5f42b563ef" /><img width="430" height="700" alt="image" src="https://github.com/user-attachments/assets/7a77f273-6348-4198-b1a3-b95e28971d37" /><img width="380" height="214" alt="image" src="https://github.com/user-attachments/assets/67d871db-7eac-4e22-9688-22331f17fb87" />

## Requirements

* Windows 10/11
* Python 3.10.6+
* PySide6

## Run From Source

Clone the repository and enter the app folder:

```bat
cd smoke_break
```

Create a virtual environment:

```bat
python -m venv .venv
```

Install dependencies:

```bat
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
```

Run the app:

```bat
".venv\Scripts\python.exe" main.py
```

## Build Windows EXE

From the `smoke_break` folder, run:

```bat
build_exe.bat
```

The generated executable will be created in:

```txt
dist/
```

Build folders, virtual environments, caches, and generated `.exe` files should not be committed to Git.

## Audio Support

Smoke Break supports user-selected audio files for the timer end reminder.

Recommended formats:

* `.mp3`
* `.wav`

Other formats such as `.m4a` or `.ogg` may work depending on Windows and Qt multimedia codec support.

If an audio file cannot be played, choose another file from the settings screen.

## Data Storage

Smoke Break stores settings and daily stats locally.

Default files:

```txt
data/settings.json
data/stats.json
```

No account, cloud sync, analytics, or network connection is required.

## Notes

Smoke Break is a local personal utility app. It does not provide medical advice, health recommendations, or smoking cessation guidance.

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.
