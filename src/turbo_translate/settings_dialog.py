"""Settings dialog for application configuration."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .config import Config
from .recorder import AudioRecorder


class SettingsDialog(QDialog):
    """Settings configuration dialog."""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self._recorder = AudioRecorder()
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self.setStyleSheet(
            "QDialog {"
            "  background-color: #0f172a;"
            "}"
            "QLabel {"
            "  color: #e2e8f0;"
            "}"
            "QGroupBox {"
            "  color: #e2e8f0;"
            "  font-weight: bold;"
            "  border: 1px solid #334155;"
            "  border-radius: 8px;"
            "  margin-top: 8px;"
            "  padding-top: 12px;"
            "}"
            "QGroupBox::title {"
            "  subcontrol-origin: margin;"
            "  left: 8px;"
            "}"
            "QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {"
            "  background-color: #1e293b;"
            "  color: #e2e8f0;"
            "  border: 1px solid #334155;"
            "  border-radius: 4px;"
            "  padding: 6px;"
            "}"
            "QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {"
            "  border-color: #3b82f6;"
            "}"
            "QTabWidget::pane {"
            "  border: 1px solid #334155;"
            "  border-radius: 8px;"
            "  background-color: #0f172a;"
            "}"
            "QTabBar::tab {"
            "  background-color: #1e293b;"
            "  color: #94a3b8;"
            "  padding: 8px 16px;"
            "  margin-right: 2px;"
            "  border-top-left-radius: 4px;"
            "  border-top-right-radius: 4px;"
            "}"
            "QTabBar::tab:selected {"
            "  background-color: #3b82f6;"
            "  color: white;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Tabs
        tabs = QTabWidget()

        # Server tab
        server_tab = QWidget()
        server_layout = QVBoxLayout(server_tab)

        server_group = QGroupBox("Backend Server")
        server_form = QFormLayout(server_group)

        self.server_host = QLineEdit()
        server_form.addRow("Server Host:", self.server_host)

        self.whisper_port = QSpinBox()
        self.whisper_port.setRange(1, 65535)
        server_form.addRow("Whisper Port:", self.whisper_port)

        self.diarization_port = QSpinBox()
        self.diarization_port.setRange(1, 65535)
        server_form.addRow("Diarization Port:", self.diarization_port)

        self.translation_port = QSpinBox()
        self.translation_port.setRange(1, 65535)
        server_form.addRow("Translation Port:", self.translation_port)

        self.tts_port = QSpinBox()
        self.tts_port.setRange(1, 65535)
        server_form.addRow("TTS Port:", self.tts_port)

        server_layout.addWidget(server_group)
        server_layout.addStretch()

        tabs.addTab(server_tab, "Server")

        # Audio tab
        audio_tab = QWidget()
        audio_layout = QVBoxLayout(audio_tab)

        audio_group = QGroupBox("Audio Input")
        audio_form = QFormLayout(audio_group)

        self.input_device = QComboBox()
        devices = self._recorder.get_devices()
        for dev in devices:
            self.input_device.addItem(dev["name"], dev["index"])
        audio_form.addRow("Input Device:", self.input_device)

        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(0, 200)
        self.gain_slider.setValue(100)
        self.gain_label = QLabel("100%")
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(self.gain_slider)
        gain_layout.addWidget(self.gain_label)
        self.gain_slider.valueChanged.connect(
            lambda v: self.gain_label.setText(f"{v}%")
        )
        audio_form.addRow("Gain:", gain_layout)

        self.silence_threshold = QDoubleSpinBox()
        self.silence_threshold.setRange(0.01, 0.5)
        self.silence_threshold.setSingleStep(0.01)
        self.silence_threshold.setDecimals(2)
        audio_form.addRow("Silence Threshold:", self.silence_threshold)

        self.voice_timeout = QDoubleSpinBox()
        self.voice_timeout.setRange(0.5, 10.0)
        self.voice_timeout.setSingleStep(0.5)
        self.voice_timeout.setDecimals(1)
        self.voice_timeout.setSuffix(" sec")
        audio_form.addRow("Voice Timeout:", self.voice_timeout)

        audio_layout.addWidget(audio_group)
        audio_layout.addStretch()

        tabs.addTab(audio_tab, "Audio")

        # Hotkeys tab
        hotkey_tab = QWidget()
        hotkey_layout = QVBoxLayout(hotkey_tab)

        hotkey_group = QGroupBox("Hotkeys")
        hotkey_form = QFormLayout(hotkey_group)

        self.hotkey = QLineEdit()
        self.hotkey.setPlaceholderText("e.g., alt+space")
        hotkey_form.addRow("Toggle Listening:", self.hotkey)

        self.enroll_hotkey = QLineEdit()
        self.enroll_hotkey.setPlaceholderText("e.g., ctrl+shift+e")
        hotkey_form.addRow("Enroll Speaker:", self.enroll_hotkey)

        hotkey_layout.addWidget(hotkey_group)
        hotkey_layout.addStretch()

        tabs.addTab(hotkey_tab, "Hotkeys")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #1e293b;"
            "  color: #e2e8f0;"
            "  border: 1px solid #334155;"
            "  border-radius: 6px;"
            "  padding: 8px 24px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #334155;"
            "}"
        )
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #3b82f6;"
            "  color: white;"
            "  border: none;"
            "  border-radius: 6px;"
            "  padding: 8px 24px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "  background-color: #2563eb;"
            "}"
        )
        save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _load_values(self):
        """Load current config values into UI."""
        self.server_host.setText(self.config.server_host)
        self.whisper_port.setValue(self.config.whisper_port)
        self.diarization_port.setValue(self.config.diarization_port)
        self.translation_port.setValue(self.config.translation_port)
        self.tts_port.setValue(self.config.tts_port)

        # Find and select current device
        for i in range(self.input_device.count()):
            if self.input_device.itemData(i) == self.config.input_device_index:
                self.input_device.setCurrentIndex(i)
                break

        self.gain_slider.setValue(int(self.config.gain * 100))
        self.silence_threshold.setValue(self.config.silence_threshold)
        self.voice_timeout.setValue(self.config.voice_activity_timeout)

        self.hotkey.setText(self.config.hotkey)
        self.enroll_hotkey.setText(self.config.enroll_hotkey)

    def _save_and_close(self):
        """Save settings and close dialog."""
        self.config.server_host = self.server_host.text()
        self.config.whisper_port = self.whisper_port.value()
        self.config.diarization_port = self.diarization_port.value()
        self.config.translation_port = self.translation_port.value()
        self.config.tts_port = self.tts_port.value()

        self.config.input_device_index = self.input_device.currentData()
        self.config.input_device_name = self.input_device.currentText()
        self.config.gain = self.gain_slider.value() / 100.0
        self.config.silence_threshold = self.silence_threshold.value()
        self.config.voice_activity_timeout = self.voice_timeout.value()

        self.config.hotkey = self.hotkey.text()
        self.config.enroll_hotkey = self.enroll_hotkey.text()

        self.config.save()
        self.accept()
