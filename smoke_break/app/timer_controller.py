from __future__ import annotations

from enum import Enum
from time import monotonic

from PySide6.QtCore import QObject, QTimer, Signal


class TimerState(str, Enum):
    IDLE = "Idle"
    RUNNING = "Running"
    PAUSED = "Paused"
    FINISHED = "Finished"


class TimerController(QObject):
    tick = Signal(int, int, str)
    finished = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.duration_seconds = 90 * 60
        self.remaining_seconds = self.duration_seconds
        self.state = TimerState.IDLE
        self._end_at = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._on_tick)

    def start(self, minutes: int) -> None:
        minutes = max(1, int(minutes))
        self.duration_seconds = minutes * 60
        self.remaining_seconds = self.duration_seconds
        self.state = TimerState.RUNNING
        self._end_at = monotonic() + self.remaining_seconds
        self._timer.start()
        self._emit()

    def pause(self) -> None:
        if self.state != TimerState.RUNNING:
            return
        self._update_remaining()
        self._timer.stop()
        self.state = TimerState.PAUSED
        self._emit()

    def resume(self) -> None:
        if self.state != TimerState.PAUSED:
            return
        self.state = TimerState.RUNNING
        self._end_at = monotonic() + self.remaining_seconds
        self._timer.start()
        self._emit()

    def reset(self, minutes: int | None = None) -> None:
        self._timer.stop()
        if minutes is not None:
            self.duration_seconds = max(1, int(minutes)) * 60
        self.remaining_seconds = self.duration_seconds
        self.state = TimerState.IDLE
        self._emit()

    def force_finished(self) -> None:
        self._timer.stop()
        self.remaining_seconds = 0
        self.state = TimerState.FINISHED
        self._emit()
        self.finished.emit()

    def _on_tick(self) -> None:
        self._update_remaining()
        if self.remaining_seconds <= 0:
            self.force_finished()
            return
        self._emit()

    def _update_remaining(self) -> None:
        self.remaining_seconds = max(0, round(self._end_at - monotonic()))

    def _emit(self) -> None:
        self.tick.emit(self.remaining_seconds, self.duration_seconds, self.state.value)
