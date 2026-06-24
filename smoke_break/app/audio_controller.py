from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioController(QObject):
    error = Signal(str)
    state_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.output)
        self.player.errorOccurred.connect(self._on_error)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)

        self.fade_timer = QTimer(self)
        self.fade_timer.setInterval(100)
        self.fade_timer.timeout.connect(self._fade_step)
        self.duration_timer = QTimer(self)
        self.duration_timer.setSingleShot(True)
        self.duration_timer.timeout.connect(self.stop)

        self.target_volume = 0.7
        self.fade_ms = 3000
        self.fade_elapsed_ms = 0

    def play(self, path_text: str, settings: dict) -> bool:
        path = Path(path_text)
        if not path_text:
            self.error.emit("No audio selected. Choose an audio file in Settings.")
            return False
        if not path.exists():
            self.error.emit("Selected audio file is missing. Choose a new file in Settings.")
            return False

        self.stop()
        self.target_volume = max(0, min(100, int(settings.get("volume", 70)))) / 100
        fade_enabled = bool(settings.get("fade_in_enabled", True))
        self.fade_ms = max(0, int(settings.get("fade_in_seconds", 3))) * 1000

        self.player.setSource(QUrl.fromLocalFile(str(path)))
        if fade_enabled and self.fade_ms > 0:
            self.output.setVolume(0)
            self.fade_elapsed_ms = 0
            self.fade_timer.start()
        else:
            self.output.setVolume(self.target_volume)

        self.player.play()
        if settings.get("play_mode") == "play_for_duration":
            minutes = max(1, int(settings.get("play_duration_minutes", 5)))
            self.duration_timer.start(minutes * 60 * 1000)
        return True

    def stop(self) -> None:
        self.fade_timer.stop()
        self.duration_timer.stop()
        self.player.stop()
        self.output.setVolume(self.target_volume)
        self.state_changed.emit(False)

    def set_volume(self, value: int) -> None:
        self.target_volume = max(0, min(100, int(value))) / 100
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState and not self.fade_timer.isActive():
            self.output.setVolume(self.target_volume)

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _fade_step(self) -> None:
        if self.fade_ms <= 0:
            self.output.setVolume(self.target_volume)
            self.fade_timer.stop()
            return
        self.fade_elapsed_ms += self.fade_timer.interval()
        ratio = min(1.0, self.fade_elapsed_ms / self.fade_ms)
        self.output.setVolume(self.target_volume * ratio)
        if ratio >= 1.0:
            self.fade_timer.stop()

    def _on_error(self, _error, error_string: str) -> None:
        self.error.emit(error_string or "Audio playback failed.")
        self.stop()

    def _on_playback_state_changed(self, state) -> None:
        self.state_changed.emit(state == QMediaPlayer.PlaybackState.PlayingState)
