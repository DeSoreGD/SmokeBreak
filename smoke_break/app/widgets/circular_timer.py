from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class CircularTimer(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(248, 248)
        self.progress = 1.0
        self.countdown = "01:30:00"
        self.state = "Idle"

    def set_values(self, remaining_seconds: int, duration_seconds: int, state: str) -> None:
        self.state = state
        self.countdown = format_seconds(remaining_seconds)
        self.progress = remaining_seconds / duration_seconds if duration_seconds > 0 else 0
        self.progress = max(0.0, min(1.0, self.progress))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(18, 18, self.width() - 36, self.height() - 36)

        painter.setPen(QPen(QColor("#263241"), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 90 * 16, -360 * 16)

        painter.setPen(QPen(self.accent_color(), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 90 * 16, int(-360 * self.progress * 16))

        painter.setPen(QColor("#eef4fb"))
        timer_font = QFont("Segoe UI", 31, QFont.Weight.DemiBold)
        timer_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0)
        painter.setFont(timer_font)
        painter.drawText(rect.adjusted(-8, 58, 8, -78), Qt.AlignmentFlag.AlignCenter, self.countdown)

        painter.setPen(QColor("#91a1b4"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        painter.drawText(rect.adjusted(0, 126, 0, -34), Qt.AlignmentFlag.AlignCenter, self.state)

    def accent_color(self) -> QColor:
        if self.state == "Running":
            return QColor("#56d482")
        if self.state in {"Finished", "Audio Playing"}:
            return QColor("#ff6b6b")
        if self.state == "Paused":
            return QColor("#a3adba")
        return QColor("#3b8cff")


def format_seconds(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"
