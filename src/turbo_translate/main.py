"""Main application entry point."""

import sys
import threading
from typing import Optional

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QSlider,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .api import APIError, TranslationPipeline
from .audio_player import AudioPlayer
from .config import Config
from .hotkey import create_hotkey_manager
from .icons import get_clear_icon, get_settings_icon, get_tray_icon
from .recorder import AudioRecorder
from .transcript_panel import StatusBar, TranscriptPanel
from .waveform import WaveformWidget


class SignalBridge(QObject):
    """Thread-safe signal emitter."""

    level_changed = pyqtSignal(float)
    segment_ready = pyqtSignal(bytes)
    transcription_done = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    status_changed = pyqtSignal(str)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.signals = SignalBridge()

        # Components
        self.recorder: Optional[AudioRecorder] = None
        self.pipeline: Optional[TranslationPipeline] = None
        self.player: Optional[AudioPlayer] = None
        self.hotkey_manager = None

        # State
        self._listening = False
        self._processing = False

        self._setup_ui()
        self._setup_connections()
        self._setup_tray()
        self._init_components()

    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("Turbo Translate")
        self.setMinimumSize(800, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left panel - Waveform and controls
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_panel.setStyleSheet("background-color: #0f172a;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(16)

        # Waveform orb
        self.waveform = WaveformWidget()
        self.waveform.setFixedSize(200, 200)
        self.waveform.set_colors(
            self.config.waveform_color,
            self.config.waveform_glow_color,
            self.config.background_color,
        )
        left_layout.addWidget(self.waveform, alignment=Qt.AlignmentFlag.AlignCenter)

        # Listen button
        self.listen_btn = QPushButton("Start Listening")
        self.listen_btn.setFixedHeight(40)
        self.listen_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #3b82f6;"
            "  color: white;"
            "  border: none;"
            "  border-radius: 8px;"
            "  font-size: 14px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  background-color: #2563eb;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #1d4ed8;"
            "}"
        )
        self.listen_btn.clicked.connect(self._toggle_listening)
        left_layout.addWidget(self.listen_btn)

        # Language selector
        lang_group = QGroupBox("Languages")
        lang_group.setStyleSheet(
            "QGroupBox {"
            "  color: #e2e8f0;"
            "  font-weight: bold;"
            "  border: 1px solid #334155;"
            "  border-radius: 8px;"
            "  margin-top: 8px;"
            "  padding-top: 8px;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  left: 8px;"
            "}"
        )
        lang_layout = QGridLayout(lang_group)

        lang_layout.addWidget(QLabel("Source:"), 0, 0)
        self.source_lang = QComboBox()
        self.source_lang.addItems(["Hungarian (hu)", "English (en)", "German (de)", "Spanish (es)"])
        self.source_lang.setCurrentText("Hungarian (hu)")
        self.source_lang.setStyleSheet(self._combo_style())
        lang_layout.addWidget(self.source_lang, 0, 1)

        lang_layout.addWidget(QLabel("Target:"), 1, 0)
        self.target_lang = QComboBox()
        self.target_lang.addItems(["English (en)", "Hungarian (hu)", "German (de)", "Spanish (es)"])
        self.target_lang.setCurrentText("English (en)")
        self.target_lang.setStyleSheet(self._combo_style())
        lang_layout.addWidget(self.target_lang, 1, 1)

        # Style labels
        for label in lang_group.findChildren(QLabel):
            label.setStyleSheet("color: #94a3b8; font-size: 12px;")

        left_layout.addWidget(lang_group)

        # TTS toggle
        self.tts_btn = QPushButton("TTS: ON")
        self.tts_btn.setCheckable(True)
        self.tts_btn.setChecked(self.config.tts_enabled)
        self.tts_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #1e293b;"
            "  color: #94a3b8;"
            "  border: 1px solid #334155;"
            "  border-radius: 6px;"
            "  padding: 8px;"
            "}"
            "QPushButton:checked {"
            "  background-color: #22c55e;"
            "  color: white;"
            "  border-color: #22c55e;"
            "}"
        )
        self.tts_btn.clicked.connect(self._toggle_tts)
        left_layout.addWidget(self.tts_btn)

        left_layout.addStretch()

        # Settings button
        settings_btn = QPushButton("Settings")
        settings_btn.setIcon(get_settings_icon("#94a3b8"))
        settings_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: transparent;"
            "  color: #94a3b8;"
            "  border: 1px solid #334155;"
            "  border-radius: 6px;"
            "  padding: 8px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #1e293b;"
            "}"
        )
        settings_btn.clicked.connect(self._show_settings)
        left_layout.addWidget(settings_btn)

        main_layout.addWidget(left_panel)

        # Right panel - Transcript
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #0f172a;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Transcript panel
        self.transcript = TranscriptPanel()
        self.transcript.set_speaker_colors(self.config.speaker_colors)
        right_layout.addWidget(self.transcript)

        # Status bar
        self.status_bar = StatusBar()
        self.status_bar.set_languages(
            self.config.source_language, self.config.target_language
        )
        right_layout.addWidget(self.status_bar)

        main_layout.addWidget(right_panel)

        # Apply dark theme
        self.setStyleSheet(
            "QMainWindow {"
            "  background-color: #0f172a;"
            "}"
            "QLabel {"
            "  color: #e2e8f0;"
            "}"
        )

    def _combo_style(self) -> str:
        """Get combo box style."""
        return (
            "QComboBox {"
            "  background-color: #1e293b;"
            "  color: #e2e8f0;"
            "  border: 1px solid #334155;"
            "  border-radius: 4px;"
            "  padding: 4px 8px;"
            "}"
            "QComboBox:hover {"
            "  border-color: #3b82f6;"
            "}"
            "QComboBox::drop-down {"
            "  border: none;"
            "}"
            "QComboBox QAbstractItemView {"
            "  background-color: #1e293b;"
            "  color: #e2e8f0;"
            "  selection-background-color: #3b82f6;"
            "}"
        )

    def _setup_connections(self):
        """Set up signal connections."""
        self.signals.level_changed.connect(self._on_level_changed)
        self.signals.segment_ready.connect(self._on_segment_ready)
        self.signals.transcription_done.connect(self._on_transcription_done)
        self.signals.error_occurred.connect(self._on_error)

    def _setup_tray(self):
        """Set up system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(get_tray_icon(False))

        # Context menu
        menu = QMenu()

        toggle_action = QAction("Toggle Listening", self)
        toggle_action.triggered.connect(self._toggle_listening)
        menu.addAction(toggle_action)

        menu.addSeparator()

        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show)
        menu.addAction(show_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _init_components(self):
        """Initialize application components."""
        # Recorder
        self.recorder = AudioRecorder(
            sample_rate=self.config.sample_rate,
            channels=self.config.channels,
            chunk_size=self.config.chunk_size,
            device_index=self.config.input_device_index,
            gain=self.config.gain,
            silence_threshold=self.config.silence_threshold,
            voice_timeout=self.config.voice_activity_timeout,
        )

        # Pipeline
        self.pipeline = TranslationPipeline(self.config)

        # Audio player
        self.player = AudioPlayer()

        # Hotkey
        self.hotkey_manager = create_hotkey_manager(
            self.config.hotkey, self._toggle_listening
        )
        self.hotkey_manager.start()

    def _toggle_listening(self):
        """Toggle listening state."""
        if self._listening:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self):
        """Start listening for speech."""
        if self._listening:
            return

        self._listening = True
        self.waveform.set_listening(True)
        self.status_bar.set_listening(True)
        self.listen_btn.setText("Stop Listening")
        self.tray_icon.setIcon(get_tray_icon(True))

        # Update language settings
        source = self.source_lang.currentText().split("(")[-1].rstrip(")")
        target = self.target_lang.currentText().split("(")[-1].rstrip(")")
        self.config.source_language = source
        self.config.target_language = target
        self.status_bar.set_languages(source, target)

        # Start recording
        self.recorder.start_continuous(
            level_callback=lambda level: self.signals.level_changed.emit(level),
            segment_callback=lambda data: self.signals.segment_ready.emit(data),
        )

    def _stop_listening(self):
        """Stop listening."""
        if not self._listening:
            return

        self._listening = False
        self.waveform.set_listening(False)
        self.status_bar.set_listening(False)
        self.listen_btn.setText("Start Listening")
        self.tray_icon.setIcon(get_tray_icon(False))

        self.recorder.stop()

    def _on_level_changed(self, level: float):
        """Handle audio level change."""
        self.waveform.set_level(level)

    def _on_segment_ready(self, audio_data: bytes):
        """Handle speech segment ready for processing."""
        if self._processing:
            return

        self._processing = True
        self.waveform.set_processing(True)
        self.status_bar.set_processing(True)

        # Process in background thread
        def process():
            try:
                results = self.pipeline.process_audio(
                    audio_data, self.config.source_language
                )
                self.signals.transcription_done.emit(results)
            except APIError as e:
                self.signals.error_occurred.emit(str(e))
            finally:
                self._processing = False
                self.waveform.set_processing(False)

        threading.Thread(target=process, daemon=True).start()

    def _on_transcription_done(self, results: list):
        """Handle transcription results."""
        self.status_bar.set_listening(self._listening)

        for result in results:
            speaker_id = result.get("speaker_id", 0)
            speaker_name = self.config.get_speaker_name(speaker_id)
            is_user = speaker_id == 0  # Assume speaker 0 is user for now

            self.transcript.add_entry(
                original_text=result["text"],
                translated_text=result["translation"],
                speaker_id=speaker_id,
                speaker_name=speaker_name,
                language=result["language"],
                is_user=is_user,
            )

            # TTS for user's speech translated to target language
            if is_user and self.config.tts_enabled and result["translation"]:
                self._speak_translation(
                    result["translation"], self.config.source_language
                )

    def _speak_translation(self, text: str, language: str):
        """Speak the translation."""
        def speak():
            try:
                audio = self.pipeline.speak_translation(text, language)
                self.player.play_wav(audio)
            except APIError as e:
                print(f"TTS error: {e}")

        threading.Thread(target=speak, daemon=True).start()

    def _on_error(self, error: str):
        """Handle error."""
        self.status_bar.set_status(f"Error: {error}", "#ef4444")
        QTimer.singleShot(5000, lambda: self.status_bar.set_listening(self._listening))

    def _toggle_tts(self):
        """Toggle TTS."""
        self.config.tts_enabled = self.tts_btn.isChecked()
        self.tts_btn.setText("TTS: ON" if self.config.tts_enabled else "TTS: OFF")

    def _show_settings(self):
        """Show settings dialog."""
        from .settings_dialog import SettingsDialog

        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # Reload configuration
            self.config = dialog.config
            self._apply_settings()

    def _apply_settings(self):
        """Apply settings changes."""
        self.waveform.set_colors(
            self.config.waveform_color,
            self.config.waveform_glow_color,
            self.config.background_color,
        )
        self.transcript.set_speaker_colors(self.config.speaker_colors)

        # Reinit recorder with new settings
        was_listening = self._listening
        if was_listening:
            self._stop_listening()

        self.recorder = AudioRecorder(
            sample_rate=self.config.sample_rate,
            channels=self.config.channels,
            chunk_size=self.config.chunk_size,
            device_index=self.config.input_device_index,
            gain=self.config.gain,
            silence_threshold=self.config.silence_threshold,
            voice_timeout=self.config.voice_activity_timeout,
        )

        # Reinit pipeline
        self.pipeline = TranslationPipeline(self.config)

        if was_listening:
            self._start_listening()

        self.config.save()

    def _on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def _quit(self):
        """Quit the application."""
        self._stop_listening()
        if self.recorder:
            self.recorder.cleanup()
        if self.player:
            self.player.cleanup()
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        self.config.save()
        QApplication.quit()

    def closeEvent(self, event):
        """Handle window close - minimize to tray instead."""
        event.ignore()
        self.hide()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Set application info
    app.setApplicationName("Turbo Translate")
    app.setOrganizationName("KnowAll AI")

    # Load config
    config = Config.load()

    # Create main window
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
