from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from app.main_window import MainWindow
from app.resources import resource_path
from app.settings_store import SettingsStore, app_base_dir


APP_NAME = "Smoke Break"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, APP_NAME, "System tray is not available.")
        return 1

    data_dir = app_base_dir() / "data"
    settings = SettingsStore(data_dir)
    window = MainWindow(settings)

    if not settings.data.get("start_minimized_to_tray", False):
        window.show_popover()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
