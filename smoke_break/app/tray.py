from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from app.resources import app_icon


class TrayController:
    def __init__(
        self,
        parent,
        toggle: Callable[[], None],
        start: Callable[[], None],
        pause_resume: Callable[[], None],
        reset: Callable[[], None],
        stop_audio: Callable[[], None],
        settings: Callable[[], None],
        quit_app: Callable[[], None],
    ) -> None:
        self.tray = QSystemTrayIcon(app_icon(), parent)
        self.tray.setToolTip("Smoke Break")

        menu = QMenu()
        self.show_action = QAction("Show / Hide", parent)
        self.start_action = QAction("Start Timer", parent)
        self.pause_action = QAction("Pause / Resume", parent)
        self.reset_action = QAction("Reset", parent)
        self.stop_audio_action = QAction("Stop Audio", parent)
        self.settings_action = QAction("Settings", parent)
        self.quit_action = QAction("Quit", parent)

        self.show_action.triggered.connect(toggle)
        self.start_action.triggered.connect(start)
        self.pause_action.triggered.connect(pause_resume)
        self.reset_action.triggered.connect(reset)
        self.stop_audio_action.triggered.connect(stop_audio)
        self.settings_action.triggered.connect(settings)
        self.quit_action.triggered.connect(quit_app)

        for action in [
            self.show_action,
            self.start_action,
            self.pause_action,
            self.reset_action,
            self.stop_audio_action,
            self.settings_action,
        ]:
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction(self.quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._activated)
        self._toggle = toggle
        self.tray.show()

    def _activated(self, reason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self._toggle()

    def geometry(self):
        return self.tray.geometry()

    def hide(self) -> None:
        self.tray.hide()
