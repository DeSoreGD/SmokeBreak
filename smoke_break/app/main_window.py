from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QAbstractSpinBox,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.audio_controller import AudioController
from app.notification_popup import BreakNotificationPopup
from app.resources import app_icon
from app.settings_store import SettingsStore
from app.stats_store import StatsStore
from app.timer_controller import TimerController, TimerState
from app.tray import TrayController
from app.widgets.circular_timer import CircularTimer


SUPPORTED_AUDIO_FILTER = "Audio Files (*.mp3 *.wav *.m4a *.ogg);;All Files (*.*)"
SUPPORTED_IMAGE_FILTER = "Image Files (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*.*)"


class MainWindow(QMainWindow):
    def __init__(self, settings_store: SettingsStore) -> None:
        super().__init__()
        self.settings_store = settings_store
        self.settings = settings_store.data
        self.stats_store = StatsStore(settings_store.path.parent)
        self.timer = TimerController()
        self.audio = AudioController()
        self.break_popup = BreakNotificationPopup(
            self.mark_took_break,
            self.mark_skipped,
            lambda: self.delay_timer(5),
            lambda: self.delay_timer(10),
            self.stop_audio,
            self.show_popover,
        )
        self._quitting = False
        self._loading_settings = False
        self._drag_offset: QPoint | None = None
        self.current_state = TimerState.IDLE.value

        self.setWindowTitle("Smoke Break")
        self.setWindowIcon(app_icon())
        self.setFixedSize(430, 700)
        self.apply_window_flags()
        self.build_ui()
        self.load_settings_into_controls()

        self.timer.tick.connect(self.on_timer_tick)
        self.timer.finished.connect(self.on_timer_finished)
        self.audio.error.connect(self.show_audio_error)
        self.audio.state_changed.connect(self.on_audio_state_changed)
        self.tray = TrayController(
            self,
            self.toggle_popover,
            self.start_timer,
            self.pause_resume_timer,
            self.reset_timer,
            self.stop_audio,
            self.show_settings,
            self.quit_app,
        )
        self.update_stats()
        self.timer.reset(self.custom_minutes.value())

    def apply_window_flags(self) -> None:
        flags = Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
        if self.settings.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def build_ui(self) -> None:
        self.setStyleSheet(STYLE)
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(root)

        self.build_title_bar(layout)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 20)
        content_layout.setSpacing(14)
        layout.addWidget(content, 1)

        header = QHBoxLayout()
        title = QLabel("Smoke Break")
        title.setObjectName("AppTitle")
        header.addWidget(title)
        header.addStretch(1)
        self.settings_button = QPushButton("Settings")
        self.settings_button.setObjectName("GhostButton")
        self.settings_button.clicked.connect(self.toggle_settings_page)
        header.addWidget(self.settings_button)
        content_layout.addLayout(header)

        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages, 1)
        self.build_main_page()
        self.build_finished_page()
        self.build_settings_page()
        self.pages.currentChanged.connect(self.update_navigation_button)
        self.update_navigation_button()

    def build_title_bar(self, layout: QVBoxLayout) -> None:
        title_bar = QFrame()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(34)
        title_bar.mousePressEvent = self.start_window_drag
        title_bar.mouseMoveEvent = self.drag_window
        title_bar.mouseReleaseEvent = self.end_window_drag

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 6, 0)
        title_layout.setSpacing(6)

        title = QLabel("Smoke Break")
        title.setObjectName("TitleBarLabel")
        title_layout.addWidget(title)
        title_layout.addStretch(1)

        hide_button = QPushButton("Hide to tray")
        hide_button.setObjectName("TitleBarButton")
        hide_button.clicked.connect(self.hide_to_tray)
        title_layout.addWidget(hide_button)

        close_button = QPushButton("X")
        close_button.setObjectName("TitleBarCloseButton")
        close_button.setFixedWidth(30)
        close_button.clicked.connect(self.hide_to_tray)
        title_layout.addWidget(close_button)

        layout.addWidget(title_bar)

    def build_main_page(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)

        self.notice_label = QLabel("")
        self.notice_label.setObjectName("Notice")
        self.notice_label.setWordWrap(True)
        page_layout.addWidget(self.notice_label)

        self.timer_ring = CircularTimer()
        page_layout.addWidget(self.timer_ring, 0, Qt.AlignmentFlag.AlignHCenter)

        timer_row = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Short Break Timer", "Normal Break Timer", "Long Break Timer", "Custom"])
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        timer_row.addWidget(self.preset_combo, 1)
        self.custom_minutes = QSpinBox()
        self.custom_minutes.setRange(1, 1440)
        self.custom_minutes.setSuffix(" min")
        self.custom_minutes.valueChanged.connect(self.on_custom_minutes_changed)
        timer_row.addWidget(self.custom_minutes)
        page_layout.addLayout(timer_row)

        controls = QGridLayout()
        controls.setHorizontalSpacing(8)
        controls.setVerticalSpacing(8)
        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.reset_button = QPushButton("Reset")
        self.took_break_button = QPushButton("Took Break")
        self.reset_button.setObjectName("SecondaryButton")
        self.took_break_button.setObjectName("SecondaryButton")
        self.start_button.clicked.connect(self.start_timer)
        self.pause_button.clicked.connect(self.pause_resume_timer)
        self.reset_button.clicked.connect(self.reset_timer)
        self.took_break_button.clicked.connect(self.mark_took_break)
        controls.addWidget(self.start_button, 0, 0)
        controls.addWidget(self.pause_button, 0, 1)
        controls.addWidget(self.took_break_button, 1, 0)
        controls.addWidget(self.reset_button, 1, 1)
        page_layout.addLayout(controls)

        self.stats_card = QFrame()
        self.stats_card.setObjectName("StatsCard")
        stats_layout = QGridLayout(self.stats_card)
        stats_layout.setContentsMargins(14, 10, 14, 10)
        stats_layout.setHorizontalSpacing(8)
        self.stats_title = QLabel("Today")
        self.stats_title.setObjectName("SectionTitle")
        self.took_label = QLabel()
        self.skipped_label = QLabel()
        self.delays_label = QLabel()
        stats_layout.addWidget(self.stats_title, 0, 0, 1, 3)
        stats_layout.addWidget(self.took_label, 1, 0)
        stats_layout.addWidget(self.skipped_label, 1, 1)
        stats_layout.addWidget(self.delays_label, 1, 2)
        page_layout.addWidget(self.stats_card)
        page_layout.addStretch(1)

        self.main_page = page
        self.pages.addWidget(page)

    def build_finished_page(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 18, 0, 0)
        layout.setSpacing(12)

        ended = QLabel("Break timer ended")
        ended.setObjectName("EndedTitle")
        ended.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ended)

        self.finished_message = QLabel("")
        self.finished_message.setObjectName("Notice")
        self.finished_message.setWordWrap(True)
        self.finished_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.finished_message)

        self.finished_ring = CircularTimer()
        layout.addWidget(self.finished_ring, 0, Qt.AlignmentFlag.AlignHCenter)

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(8)
        buttons.setVerticalSpacing(8)
        actions = [
            ("Took Break", self.mark_took_break),
            ("Skipped", self.mark_skipped),
            ("Delay 5 min", lambda: self.delay_timer(5)),
            ("Delay 10 min", lambda: self.delay_timer(10)),
            ("Start New Timer", self.start_timer),
            ("Stop Audio", self.stop_audio),
        ]
        for index, (text, callback) in enumerate(actions):
            button = QPushButton(text)
            if text in {"Skipped", "Stop Audio"}:
                button.setObjectName("SecondaryButton")
            button.clicked.connect(callback)
            buttons.addWidget(button, index // 2, index % 2)
        layout.addLayout(buttons)
        layout.addStretch(1)

        self.finished_page = page
        self.pages.addWidget(page)

    def build_settings_page(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)

        title = QLabel("Settings")
        title.setObjectName("SectionTitle")
        page_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setObjectName("SettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 2, 0)
        layout.setSpacing(12)

        self.default_minutes = spin_box(1, 1440, " min")
        self.short_minutes = spin_box(1, 1440, " min")
        self.normal_minutes = spin_box(1, 1440, " min")
        self.long_minutes = spin_box(1, 1440, " min")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.fade_seconds = spin_box(0, 60, " sec")
        self.play_mode = QComboBox()
        self.play_mode.addItem("Play once", "play_once")
        self.play_mode.addItem("Play for duration", "play_for_duration")
        self.play_duration = spin_box(1, 180, " min")
        self.daily_limit = spin_box(1, 99, "")
        self.fade_enabled = QCheckBox("Fade in")
        self.daily_limit_enabled = QCheckBox("Daily limit")
        self.fade_enabled.stateChanged.connect(self.save_settings_from_controls)
        self.daily_limit_enabled.stateChanged.connect(self.save_settings_from_controls)

        timer_card, timer_form = self.settings_card("Timer")
        add_setting_row(timer_form, "Default", self.default_minutes)
        add_setting_row(timer_form, "Short", self.short_minutes)
        add_setting_row(timer_form, "Normal", self.normal_minutes)
        add_setting_row(timer_form, "Long", self.long_minutes)
        layout.addWidget(timer_card)

        audio_card, audio_form = self.settings_card("Audio")
        add_setting_row(audio_form, "Volume", self.volume_slider)
        add_setting_row(audio_form, "Fade seconds", self.fade_seconds)
        add_setting_row(audio_form, "Play mode", self.play_mode)
        add_setting_row(audio_form, "Duration", self.play_duration)
        audio_form.addWidget(self.fade_enabled)
        layout.addWidget(audio_card)

        tracking_card, tracking_form = self.settings_card("Tracking")
        add_setting_row(tracking_form, "Limit count", self.daily_limit)
        tracking_form.addWidget(self.daily_limit_enabled)
        layout.addWidget(tracking_card)

        choose_audio = QPushButton("Choose Audio")
        choose_audio.clicked.connect(self.choose_audio)
        layout.addWidget(choose_audio)
        self.audio_path_label = QLabel("No audio selected")
        self.audio_path_label.setObjectName("PathLabel")
        self.audio_path_label.setWordWrap(True)
        layout.addWidget(self.audio_path_label)

        choose_image = QPushButton("Choose Popup Image")
        choose_image.setObjectName("SecondaryButton")
        choose_image.clicked.connect(self.choose_notification_image)
        layout.addWidget(choose_image)
        self.notification_image_path_label = QLabel("Using audio artwork or default image")
        self.notification_image_path_label.setObjectName("PathLabel")
        self.notification_image_path_label.setWordWrap(True)
        layout.addWidget(self.notification_image_path_label)

        reset = QPushButton("Reset Settings")
        reset.setObjectName("SecondaryButton")
        reset.clicked.connect(self.reset_settings)
        layout.addWidget(reset)
        layout.addStretch(1)

        scroll.setWidget(body)
        page_layout.addWidget(scroll, 1)

        for widget in [
            self.default_minutes,
            self.short_minutes,
            self.normal_minutes,
            self.long_minutes,
            self.volume_slider,
            self.fade_seconds,
            self.play_mode,
            self.play_duration,
            self.daily_limit,
        ]:
            if isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self.save_settings_from_controls)
            else:
                widget.valueChanged.connect(self.save_settings_from_controls)

        self.settings_page = page
        self.pages.addWidget(page)

    def settings_card(self, title_text: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("SettingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)
        title = QLabel(title_text)
        title.setObjectName("CardTitle")
        layout.addWidget(title)
        return card, layout

    def load_settings_into_controls(self) -> None:
        self._loading_settings = True
        self.default_minutes.setValue(int(self.settings["default_timer_minutes"]))
        self.short_minutes.setValue(int(self.settings["presets"]["short"]))
        self.normal_minutes.setValue(int(self.settings["presets"]["normal"]))
        self.long_minutes.setValue(int(self.settings["presets"]["long"]))
        self.volume_slider.setValue(int(self.settings["volume"]))
        self.fade_enabled.setChecked(bool(self.settings["fade_in_enabled"]))
        self.fade_seconds.setValue(int(self.settings["fade_in_seconds"]))
        self.play_mode.setCurrentIndex(max(0, self.play_mode.findData(self.settings["play_mode"])))
        self.play_duration.setValue(int(self.settings["play_duration_minutes"]))
        self.daily_limit_enabled.setChecked(bool(self.settings["daily_limit_enabled"]))
        self.daily_limit.setValue(int(self.settings["daily_limit"]))
        self.custom_minutes.setValue(int(self.settings["default_timer_minutes"]))
        self.preset_combo.setCurrentIndex(1)
        self._loading_settings = False
        self.update_audio_path_label()
        self.update_notification_image_path_label()

    def save_settings_from_controls(self) -> None:
        if self._loading_settings:
            return
        self.settings["default_timer_minutes"] = self.default_minutes.value()
        self.settings["presets"] = {
            "short": self.short_minutes.value(),
            "normal": self.normal_minutes.value(),
            "long": self.long_minutes.value(),
        }
        self.settings["volume"] = self.volume_slider.value()
        self.settings["fade_in_enabled"] = self.fade_enabled.isChecked()
        self.settings["fade_in_seconds"] = self.fade_seconds.value()
        self.settings["play_mode"] = self.play_mode.currentData()
        self.settings["play_duration_minutes"] = self.play_duration.value()
        self.settings["daily_limit_enabled"] = self.daily_limit_enabled.isChecked()
        self.settings["daily_limit"] = self.daily_limit.value()
        self.settings_store.save()
        self.audio.set_volume(self.settings["volume"])
        self.update_stats()

    def start_timer(self) -> None:
        self.break_popup.hide()
        self.stop_audio()
        self.set_notice("")
        self.finished_message.setText("")
        self.timer.start(self.custom_minutes.value())
        self.pages.setCurrentWidget(self.main_page)
        self.show_limit_warning_if_needed()

    def pause_resume_timer(self) -> None:
        if self.current_state == TimerState.RUNNING.value:
            self.timer.pause()
        elif self.current_state == TimerState.PAUSED.value:
            self.timer.resume()

    def reset_timer(self) -> None:
        self.break_popup.hide()
        self.stop_audio()
        self.set_notice("")
        self.finished_message.setText("")
        self.timer.reset(self.custom_minutes.value())
        self.pages.setCurrentWidget(self.main_page)

    def delay_timer(self, minutes: int) -> None:
        self.break_popup.hide()
        self.stop_audio()
        self.stats_store.increment("delay_count")
        self.update_stats()
        self.set_notice(f"Delay started for {minutes} minutes.")
        self.timer.start(minutes)
        self.pages.setCurrentWidget(self.main_page)

    def mark_took_break(self) -> None:
        self.break_popup.hide()
        self.stop_audio()
        self.stats_store.increment("took_break_count")
        self.update_stats()
        self.timer.reset(self.custom_minutes.value())
        self.set_notice("Took break recorded.")
        self.pages.setCurrentWidget(self.main_page)

    def mark_skipped(self) -> None:
        self.break_popup.hide()
        self.stop_audio()
        self.stats_store.increment("skipped_count")
        self.update_stats()
        self.timer.reset(self.custom_minutes.value())
        self.set_notice("Skipped recorded.")
        self.pages.setCurrentWidget(self.main_page)

    def stop_audio(self) -> None:
        self.audio.stop()
        if self.current_state == "Audio Playing":
            self.current_state = TimerState.FINISHED.value
            self.update_state_buttons()

    def choose_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose audio file", "", SUPPORTED_AUDIO_FILTER)
        if not path:
            return
        self.settings["selected_audio_path"] = path
        self.settings_store.save()
        self.update_audio_path_label()
        self.finished_message.setText("")
        self.set_notice("")

    def choose_notification_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose popup image", "", SUPPORTED_IMAGE_FILTER)
        if not path:
            return
        self.settings["selected_notification_image_path"] = path
        self.settings_store.save()
        self.update_notification_image_path_label()

    def reset_settings(self) -> None:
        response = QMessageBox.question(self, "Smoke Break", "Reset settings to defaults?")
        if response != QMessageBox.StandardButton.Yes:
            return
        self.settings_store.reset()
        self.settings = self.settings_store.data
        self.load_settings_into_controls()
        self.reset_timer()

    def on_preset_changed(self) -> None:
        if self._loading_settings:
            return
        presets = self.settings["presets"]
        value_by_label = {
            "Short Break Timer": presets["short"],
            "Normal Break Timer": presets["normal"],
            "Long Break Timer": presets["long"],
        }
        value = value_by_label.get(self.preset_combo.currentText())
        if value:
            self.custom_minutes.setValue(int(value))

    def on_custom_minutes_changed(self) -> None:
        if self._loading_settings:
            return
        expected = {
            "Short Break Timer": int(self.settings["presets"]["short"]),
            "Normal Break Timer": int(self.settings["presets"]["normal"]),
            "Long Break Timer": int(self.settings["presets"]["long"]),
        }.get(self.preset_combo.currentText())
        if expected is not None and expected != self.custom_minutes.value():
            self.preset_combo.setCurrentText("Custom")
        if self.current_state in {TimerState.IDLE.value, TimerState.FINISHED.value}:
            self.timer.reset(self.custom_minutes.value())

    def on_timer_tick(self, remaining: int, duration: int, state: str) -> None:
        self.current_state = state
        self.timer_ring.set_values(remaining, duration, state)
        self.finished_ring.set_values(remaining, duration, "Audio Playing" if self.audio.is_playing() else state)
        self.update_state_buttons()

    def on_timer_finished(self) -> None:
        self.current_state = TimerState.FINISHED.value
        self.pages.setCurrentWidget(self.finished_page)
        if self.audio.play(self.settings.get("selected_audio_path", ""), self.settings):
            self.current_state = "Audio Playing"
            self.finished_ring.set_values(0, max(1, self.timer.duration_seconds), "Audio Playing")
        self.break_popup.show_for_settings(self.settings)
        self.update_state_buttons()

    def on_audio_state_changed(self, playing: bool) -> None:
        if playing:
            self.current_state = "Audio Playing"
        elif self.current_state == "Audio Playing":
            self.current_state = TimerState.FINISHED.value
        self.update_state_buttons()

    def show_audio_error(self, message: str) -> None:
        self.finished_message.setText(message)
        self.set_notice(message)

    def update_state_buttons(self) -> None:
        self.pause_button.setText("Resume" if self.current_state == TimerState.PAUSED.value else "Pause")
        self.pause_button.setEnabled(self.current_state in {TimerState.RUNNING.value, TimerState.PAUSED.value})

    def update_stats(self) -> None:
        self.stats_store.ensure_today()
        data = self.stats_store.data
        self.took_label.setText(f"Took breaks: {data.get('took_break_count', 0)}")
        self.skipped_label.setText(f"Skipped: {data.get('skipped_count', 0)}")
        self.delays_label.setText(f"Delays: {data.get('delay_count', 0)}")
        self.show_limit_warning_if_needed()

    def show_limit_warning_if_needed(self) -> None:
        if not self.settings.get("daily_limit_enabled", False):
            if self.notice_label.text() == "Daily break limit reached.":
                self.set_notice("")
            return
        took = int(self.stats_store.data.get("took_break_count", 0))
        limit = int(self.settings.get("daily_limit", 5))
        if took >= limit:
            self.notice_label.setText("Daily break limit reached.")

    def update_audio_path_label(self) -> None:
        path = self.settings.get("selected_audio_path", "")
        self.audio_path_label.setText(path if path else "No audio selected")

    def update_notification_image_path_label(self) -> None:
        path = self.settings.get("selected_notification_image_path", "")
        self.notification_image_path_label.setText(path if path else "Using audio artwork or default image")

    def set_notice(self, text: str) -> None:
        self.notice_label.setText(text)

    def toggle_settings_page(self) -> None:
        if self.pages.currentWidget() == self.settings_page:
            self.pages.setCurrentWidget(self.main_page)
            return
        self.show_settings()

    def show_settings(self) -> None:
        self.pages.setCurrentWidget(self.settings_page)
        self.show_popover()

    def update_navigation_button(self) -> None:
        if not hasattr(self, "settings_page"):
            return
        if self.pages.currentWidget() == self.settings_page:
            self.settings_button.setText("Timer")
        else:
            self.settings_button.setText("Settings")

    def hide_to_tray(self) -> None:
        self.hide()

    def toggle_popover(self) -> None:
        if self.isVisible() and self.isActiveWindow():
            self.hide_to_tray()
        else:
            self.show_popover()

    def show_popover(self) -> None:
        self.break_popup.hide()
        self.position_near_tray()
        self.show()
        self.raise_()
        self.activateWindow()
        self.fade_in_window()

    def position_near_tray(self) -> None:
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        tray_geometry = self.tray.geometry() if hasattr(self, "tray") else None
        if tray_geometry and tray_geometry.isValid() and tray_geometry.width() > 0:
            x = tray_geometry.center().x() - self.width() + 24
            y = tray_geometry.top() - self.height() - 10
            if y < available.top():
                y = tray_geometry.bottom() + 10
        else:
            x = available.right() - self.width() - 16
            y = available.bottom() - self.height() - 16
        x = max(available.left() + 8, min(x, available.right() - self.width() - 8))
        y = max(available.top() + 8, min(y, available.bottom() - self.height() - 8))
        self.move(QPoint(x, y))

    def fade_in_window(self) -> None:
        self.setWindowOpacity(0.0)
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.opacity_animation.setDuration(130)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.opacity_animation.start()

    def start_window_drag(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def drag_window(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def end_window_drag(self, event) -> None:
        self._drag_offset = None
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._quitting:
            event.accept()
            return
        event.ignore()
        self.hide_to_tray()

    def quit_app(self) -> None:
        self._quitting = True
        self.audio.stop(immediate=True)
        self.break_popup.hide()
        self.tray.hide()
        QApplication.quit()


def spin_box(minimum: int, maximum: int, suffix: str) -> QSpinBox:
    box = QSpinBox()
    box.setRange(minimum, maximum)
    box.setSuffix(suffix)
    box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    box.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    box.setMinimumWidth(176)
    return box


def add_setting_row(layout: QVBoxLayout, label_text: str, widget: QWidget) -> None:
    row = QFrame()
    row.setObjectName("SettingRow")
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(14)
    label = QLabel(label_text)
    label.setObjectName("FormLabel")
    label.setFixedWidth(116)
    label.setMinimumHeight(38)
    widget.setMinimumHeight(38)
    row_layout.addWidget(label)
    row_layout.addWidget(widget, 1)
    layout.addWidget(row)


STYLE = """
QMainWindow {
    background: #0d141d;
}
#SettingsScroll {
    background: transparent;
    border: 0;
}
#SettingsScroll QWidget {
    background: transparent;
}
#TitleBar {
    background: #121d29;
    border-bottom: 1px solid #273343;
}
#TitleBarLabel {
    color: #dce5ef;
    font-size: 12px;
    font-weight: 600;
}
QWidget {
    color: #dce5ef;
    font-family: "Segoe UI";
    font-size: 13px;
}
#AppTitle {
    color: #f3f7fb;
    font-size: 20px;
    font-weight: 700;
}
#SectionTitle {
    color: #f3f7fb;
    font-size: 14px;
    font-weight: 700;
}
#EndedTitle {
    color: #f3f7fb;
    font-size: 22px;
    font-weight: 700;
}
#Notice {
    color: #ffd166;
    min-height: 20px;
}
#StatsCard {
    background: #121d29;
    border: 1px solid #273343;
    border-radius: 8px;
}
#SettingsCard {
    background: #101a26;
    border: 1px solid #263343;
    border-radius: 8px;
}
#SettingRow {
    background: transparent;
    min-height: 40px;
}
#CardTitle {
    color: #edf5ff;
    font-size: 12px;
    font-weight: 700;
}
#FormLabel {
    color: #97a8ba;
}
#PathLabel {
    color: #97a8ba;
    background: #121d29;
    border: 1px solid #273343;
    border-radius: 6px;
    padding: 7px;
}
QPushButton {
    background: #267555;
    border: 0;
    border-radius: 7px;
    color: #f6fbff;
    font-weight: 700;
    min-height: 34px;
    padding: 0 12px;
}
#TitleBarButton {
    background: #192433;
    border: 1px solid #2d3b4f;
    border-radius: 5px;
    color: #dce5ef;
    font-size: 11px;
    font-weight: 700;
    min-height: 24px;
    padding: 0 8px;
}
#TitleBarButton:hover {
    background: #233247;
}
#TitleBarCloseButton {
    background: transparent;
    border: 0;
    border-radius: 4px;
    color: #97a8ba;
    font-size: 12px;
    font-weight: 700;
    min-height: 24px;
    padding: 0;
}
#TitleBarCloseButton:hover {
    background: #3a2630;
    color: #ffb4b4;
}
QPushButton:hover {
    background: #2e8a66;
}
QPushButton:pressed {
    background: #1e6147;
}
QPushButton:disabled {
    background: #263241;
    color: #758393;
}
#SecondaryButton, #GhostButton {
    background: #192433;
    color: #dce5ef;
    border: 1px solid #2d3b4f;
}
#SecondaryButton:hover, #GhostButton:hover {
    background: #233247;
}
QComboBox, QSpinBox {
    background: #121d29;
    border: 1px solid #2d3b4f;
    border-radius: 6px;
    min-height: 36px;
    padding: 0 10px;
}
QComboBox::drop-down {
    width: 26px;
    border: 0;
}
QComboBox QAbstractItemView {
    background: #121d29;
    color: #dce5ef;
    border: 1px solid #2d3b4f;
    selection-background-color: #267555;
    selection-color: #f6fbff;
    outline: 0;
}
QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 4px 8px;
}
QCheckBox {
    color: #dce5ef;
    min-height: 30px;
    padding-top: 2px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #263241;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #56d482;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 2px 0;
}
QScrollBar::handle:vertical {
    background: #2d3b4f;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QMenu {
    background: #121d29;
    color: #dce5ef;
    border: 1px solid #2d3b4f;
}
QMenu::item {
    padding: 7px 22px;
}
QMenu::item:selected {
    background: #267555;
}
"""
