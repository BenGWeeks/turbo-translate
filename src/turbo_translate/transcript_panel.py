"""Transcript panel widget showing conversation with speaker colors."""

from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


@dataclass
class TranscriptEntry:
    """A single transcript entry."""

    original_text: str
    translated_text: str
    speaker_id: int
    speaker_name: str
    speaker_color: str
    timestamp: datetime
    language: str
    is_user: bool = False


class TranscriptBubble(QFrame):
    """A single message bubble in the transcript."""

    def __init__(self, entry: TranscriptEntry, parent=None):
        super().__init__(parent)
        self.entry = entry
        self._setup_ui()

    def _setup_ui(self):
        """Set up the bubble UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Speaker header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Speaker indicator dot
        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(
            f"background-color: {self.entry.speaker_color}; "
            f"border-radius: 6px;"
        )
        header_layout.addWidget(dot)

        # Speaker name
        name_label = QLabel(self.entry.speaker_name)
        name_label.setStyleSheet(
            f"color: {self.entry.speaker_color}; "
            f"font-weight: bold; "
            f"font-size: 12px;"
        )
        header_layout.addWidget(name_label)

        # Language indicator
        lang_label = QLabel(f"[{self.entry.language.upper()}]")
        lang_label.setStyleSheet("color: #64748b; font-size: 10px;")
        header_layout.addWidget(lang_label)

        header_layout.addStretch()

        # Timestamp
        time_str = self.entry.timestamp.strftime("%H:%M:%S")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #64748b; font-size: 10px;")
        header_layout.addWidget(time_label)

        layout.addLayout(header_layout)

        # Original text
        original_label = QLabel(self.entry.original_text)
        original_label.setWordWrap(True)
        original_label.setStyleSheet(
            "color: #e2e8f0; "
            "font-size: 14px; "
            "padding: 4px 0;"
        )
        layout.addWidget(original_label)

        # Translation (if different)
        if self.entry.translated_text and self.entry.translated_text != self.entry.original_text:
            translation_label = QLabel(self.entry.translated_text)
            translation_label.setWordWrap(True)
            translation_label.setStyleSheet(
                "color: #94a3b8; "
                "font-size: 13px; "
                "font-style: italic; "
                "padding: 4px 0; "
                "border-left: 2px solid #334155; "
                "padding-left: 8px;"
            )
            layout.addWidget(translation_label)

        # Style the bubble
        self.setStyleSheet(
            f"TranscriptBubble {{"
            f"  background-color: #1e293b;"
            f"  border-radius: 8px;"
            f"  border-left: 3px solid {self.entry.speaker_color};"
            f"}}"
        )


class TranscriptPanel(QWidget):
    """Panel showing the conversation transcript with speaker diarization."""

    cleared = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[TranscriptEntry] = []
        self._speaker_colors: list[str] = [
            "#3b82f6",  # Blue (user)
            "#ef4444",  # Red
            "#22c55e",  # Green
            "#f59e0b",  # Orange
            "#8b5cf6",  # Purple
            "#ec4899",  # Pink
            "#14b8a6",  # Teal
            "#f97316",  # Deep orange
        ]
        self._setup_ui()

    def _setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(40)
        header.setStyleSheet("background-color: #0f172a;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        title = QLabel("Conversation")
        title.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        layout.addWidget(header)

        # Scroll area for messages
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea {"
            "  background-color: #0f172a;"
            "  border: none;"
            "}"
            "QScrollBar:vertical {"
            "  background-color: #1e293b;"
            "  width: 8px;"
            "}"
            "QScrollBar::handle:vertical {"
            "  background-color: #334155;"
            "  border-radius: 4px;"
            "}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {"
            "  height: 0px;"
            "}"
        )

        # Container for messages
        self._container = QWidget()
        self._container.setStyleSheet("background-color: #0f172a;")
        self._messages_layout = QVBoxLayout(self._container)
        self._messages_layout.setContentsMargins(16, 16, 16, 16)
        self._messages_layout.setSpacing(12)
        self._messages_layout.addStretch()

        scroll.setWidget(self._container)
        layout.addWidget(scroll)

        self._scroll = scroll

    def set_speaker_colors(self, colors: list[str]):
        """Set the speaker color palette."""
        self._speaker_colors = colors

    def get_speaker_color(self, speaker_id: int) -> str:
        """Get color for a speaker ID."""
        return self._speaker_colors[speaker_id % len(self._speaker_colors)]

    def add_entry(
        self,
        original_text: str,
        translated_text: str,
        speaker_id: int,
        speaker_name: str,
        language: str,
        is_user: bool = False,
    ):
        """Add a new transcript entry."""
        entry = TranscriptEntry(
            original_text=original_text,
            translated_text=translated_text,
            speaker_id=speaker_id,
            speaker_name=speaker_name,
            speaker_color=self.get_speaker_color(speaker_id),
            timestamp=datetime.now(),
            language=language,
            is_user=is_user,
        )
        self._entries.append(entry)

        # Add bubble widget
        bubble = TranscriptBubble(entry)
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, bubble)

        # Scroll to bottom
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def clear(self):
        """Clear all entries."""
        self._entries.clear()

        # Remove all bubbles
        while self._messages_layout.count() > 1:
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.cleared.emit()


class StatusBar(QWidget):
    """Status bar showing listening state and language info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the status bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)

        # Status indicator
        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(
            "background-color: #64748b; border-radius: 4px;"
        )
        layout.addWidget(self._status_dot)

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self._status_label)

        layout.addStretch()

        # Language display
        self._lang_label = QLabel("HU → EN")
        self._lang_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self._lang_label)

        self.setStyleSheet("background-color: #0f172a; border-top: 1px solid #1e293b;")

    def set_status(self, status: str, color: str = "#64748b"):
        """Set the status text and color."""
        self._status_label.setText(status)
        self._status_dot.setStyleSheet(
            f"background-color: {color}; border-radius: 4px;"
        )

    def set_listening(self, listening: bool):
        """Set listening state."""
        if listening:
            self.set_status("Listening...", "#22c55e")
        else:
            self.set_status("Ready", "#64748b")

    def set_processing(self, processing: bool):
        """Set processing state."""
        if processing:
            self.set_status("Processing...", "#f59e0b")

    def set_languages(self, source: str, target: str):
        """Set the language display."""
        self._lang_label.setText(f"{source.upper()} → {target.upper()}")
