from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.media_art import embedded_art_bytes
from app.resources import app_icon, resource_path


class BreakNotificationPopup(QWidget):
    def __init__(
        self,
        took_break: Callable[[], None],
        skipped: Callable[[], None],
        delay_5: Callable[[], None],
        delay_10: Callable[[], None],
        stop_audio: Callable[[], None],
        open_timer: Callable[[], None],
    ) -> None:
        super().__init__()
        self.setWindowTitle("Smoke Break")
        self.setWindowIcon(app_icon())
        self.setFixedSize(380, 214)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("PopupCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(12)
        root.addWidget(card)

        top = QHBoxLayout()
        top.setSpacing(14)
        self.image = QLabel()
        self.image.setObjectName("CoverImage")
        self.image.setFixedSize(86, 86)
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(self.image)

        text_col = QVBoxLayout()
        text_col.setSpacing(7)
        title = QLabel("Break timer ended")
        title.setObjectName("PopupTitle")
        subtitle = QLabel("Take a break?")
        subtitle.setObjectName("PopupSubtitle")
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        text_col.addStretch(1)
        open_button = QPushButton("Open Timer")
        open_button.setObjectName("SecondaryButton")
        open_button.clicked.connect(open_timer)
        text_col.addWidget(open_button)
        top.addLayout(text_col, 1)
        card_layout.addLayout(top)

        actions = QGridLayout()
        actions.setHorizontalSpacing(10)
        actions.setVerticalSpacing(9)
        buttons = [
            ("Took Break", took_break, ""),
            ("Skipped", skipped, "SecondaryButton"),
            ("Delay 5", delay_5, "SecondaryButton"),
            ("Delay 10", delay_10, "SecondaryButton"),
            ("Stop Audio", stop_audio, "SecondaryButton"),
        ]
        for index, (text, callback, object_name) in enumerate(buttons):
            button = QPushButton(text)
            if object_name:
                button.setObjectName(object_name)
            button.clicked.connect(callback)
            if index < 4:
                actions.addWidget(button, index // 2, index % 2)
            else:
                actions.addWidget(button, 2, 0, 1, 2)
        card_layout.addLayout(actions)

    def show_for_settings(self, settings: dict) -> None:
        self.image.setPixmap(self.resolve_pixmap(settings))
        self.position_bottom_right()
        self.show()
        self.raise_()
        self.activateWindow()

    def resolve_pixmap(self, settings: dict) -> QPixmap:
        size = self.image.size()
        custom_path = settings.get("selected_notification_image_path", "")
        if custom_path and Path(custom_path).exists():
            pixmap = QPixmap(custom_path)
            if not pixmap.isNull():
                return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

        art = embedded_art_bytes(settings.get("selected_audio_path", ""))
        if art:
            pixmap = QPixmap()
            if pixmap.loadFromData(art):
                return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

        pixmap = QPixmap(resource_path("assets/smoke_break_default_img.png"))
        if pixmap.isNull():
            pixmap = app_icon().pixmap(size)
        return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)

    def position_bottom_right(self) -> None:
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        x = available.right() - self.width() - 18
        y = available.bottom() - self.height() - 18
        self.move(x, y)


STYLE = """
QWidget {
    background: transparent;
    color: #eaf2fb;
    font-family: "Segoe UI";
    font-size: 12px;
}
#PopupCard {
    background: #101a26;
    border: 1px solid #304057;
    border-radius: 12px;
}
#CoverImage {
    background: #0b121b;
    border: 1px solid #263343;
    border-radius: 8px;
}
#PopupTitle {
    color: #f6fbff;
    font-size: 17px;
    font-weight: 700;
}
#PopupSubtitle {
    color: #9fb1c6;
    font-size: 12px;
}
QPushButton {
    background: #267555;
    border: 0;
    border-radius: 7px;
    color: #f6fbff;
    font-weight: 700;
    min-height: 32px;
    padding: 0 10px;
}
QPushButton:hover {
    background: #2e8a66;
}
#SecondaryButton {
    background: #192433;
    color: #dce5ef;
    border: 1px solid #2d3b4f;
}
#SecondaryButton:hover {
    background: #233247;
}
"""
