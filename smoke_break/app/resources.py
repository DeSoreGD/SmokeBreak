from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtCore import Qt


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = Path(__file__).resolve().parents[1]
    return str(base_dir / relative_path)


def app_icon() -> QIcon:
    icon = QIcon(resource_path("assets/icon.ico"))
    if not icon.isNull():
        return icon
    return fallback_icon()


def fallback_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#101821"))
    painter.setPen(QPen(QColor("#56d482"), 3))
    painter.drawEllipse(6, 6, 52, 52)
    painter.setPen(QPen(QColor("#ff6b6b"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawArc(18, 18, 28, 28, 100 * 16, -280 * 16)
    painter.setPen(QPen(QColor("#eef4fb"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(32, 18, 32, 32)
    painter.drawLine(32, 32, 42, 38)
    painter.end()
    return QIcon(pixmap)
