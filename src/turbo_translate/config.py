"""Configuration management for Turbo Translate."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict


class HistoryEntry(TypedDict):
    """A single transcription history entry."""

    text: str
    translation: str
    timestamp: str
    speaker: str
    speaker_id: int
    wav_filename: str | None


class SpeakerProfile(TypedDict):
    """Speaker profile for voice recognition."""

    name: str
    embedding_file: str
    color: str
    is_user: bool


@dataclass
class Config:
    """Application configuration."""

    # Server settings (black-panther)
    server_host: str = "192.168.1.89"
    whisper_port: int = 8100
    diarization_port: int = 8101
    translation_port: int = 8102
    tts_port: int = 8103

    # API settings
    api_key: str = ""

    # Language settings
    source_language: str = "hu"  # Language being spoken (Hungarian)
    target_language: str = "en"  # Language to translate to (English)
    user_language: str = "en"  # Language the user speaks (English)

    # Hotkey settings
    hotkey: str = "alt+space"
    enroll_hotkey: str = "ctrl+shift+e"

    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    input_device_index: int | None = None
    input_device_name: str = ""
    gain: float = 1.0
    silence_threshold: float = 0.03
    voice_activity_timeout: float = 2.0  # seconds of silence before processing

    # UI settings
    waveform_color: str = "#3b82f6"  # Blue
    waveform_glow_color: str = "#60a5fa"  # Light blue
    background_color: str = "#0f172a"  # Dark blue
    window_width: int = 800
    window_height: int = 600

    # Speaker colors for diarization
    speaker_colors: list[str] = field(
        default_factory=lambda: [
            "#3b82f6",  # Blue (user)
            "#ef4444",  # Red
            "#22c55e",  # Green
            "#f59e0b",  # Orange
            "#8b5cf6",  # Purple
            "#ec4899",  # Pink
            "#14b8a6",  # Teal
            "#f97316",  # Deep orange
        ]
    )

    # History settings
    max_history: int = 100
    save_recordings: bool = True
    history: list[HistoryEntry] = field(default_factory=list)

    # Speaker profiles
    speaker_profiles: list[SpeakerProfile] = field(default_factory=list)

    # Feature flags
    auto_translate: bool = True
    tts_enabled: bool = True
    continuous_listening: bool = True

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get the configuration directory."""
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home()))
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        config_dir = base / "turbo-translate"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the configuration file path."""
        return cls.get_config_dir() / "config.json"

    @classmethod
    def get_recordings_dir(cls) -> Path:
        """Get the recordings directory."""
        recordings_dir = cls.get_config_dir() / "recordings"
        recordings_dir.mkdir(parents=True, exist_ok=True)
        return recordings_dir

    @classmethod
    def get_embeddings_dir(cls) -> Path:
        """Get the speaker embeddings directory."""
        embeddings_dir = cls.get_config_dir() / "embeddings"
        embeddings_dir.mkdir(parents=True, exist_ok=True)
        return embeddings_dir

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from file."""
        config_path = cls.get_config_path()
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                # Handle nested fields
                history = data.pop("history", [])
                speaker_profiles = data.pop("speaker_profiles", [])
                speaker_colors = data.pop("speaker_colors", None)

                config = cls(**{k: v for k, v in data.items() if hasattr(cls, k)})
                config.history = history
                config.speaker_profiles = speaker_profiles
                if speaker_colors:
                    config.speaker_colors = speaker_colors
                return config
            except Exception as e:
                print(f"Error loading config: {e}")
        return cls()

    def save(self) -> None:
        """Save configuration to file."""
        config_path = self.get_config_path()
        data = {
            "server_host": self.server_host,
            "whisper_port": self.whisper_port,
            "diarization_port": self.diarization_port,
            "translation_port": self.translation_port,
            "tts_port": self.tts_port,
            "api_key": self.api_key,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "user_language": self.user_language,
            "hotkey": self.hotkey,
            "enroll_hotkey": self.enroll_hotkey,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_size": self.chunk_size,
            "input_device_index": self.input_device_index,
            "input_device_name": self.input_device_name,
            "gain": self.gain,
            "silence_threshold": self.silence_threshold,
            "voice_activity_timeout": self.voice_activity_timeout,
            "waveform_color": self.waveform_color,
            "waveform_glow_color": self.waveform_glow_color,
            "background_color": self.background_color,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "speaker_colors": self.speaker_colors,
            "max_history": self.max_history,
            "save_recordings": self.save_recordings,
            "history": self.history,
            "speaker_profiles": self.speaker_profiles,
            "auto_translate": self.auto_translate,
            "tts_enabled": self.tts_enabled,
            "continuous_listening": self.continuous_listening,
        }
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_to_history(
        self,
        text: str,
        translation: str,
        speaker: str,
        speaker_id: int,
        wav_filename: str | None = None,
    ) -> None:
        """Add a transcription to history."""
        from datetime import datetime

        entry: HistoryEntry = {
            "text": text,
            "translation": translation,
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "speaker_id": speaker_id,
            "wav_filename": wav_filename,
        }

        # Check for duplicates
        if self.history and self.history[-1]["text"] == text:
            return

        self.history.append(entry)

        # Trim history
        while len(self.history) > self.max_history:
            old_entry = self.history.pop(0)
            if old_entry.get("wav_filename"):
                wav_path = self.get_recordings_dir() / old_entry["wav_filename"]
                if wav_path.exists():
                    wav_path.unlink()

        self.save()

    def get_speaker_color(self, speaker_id: int) -> str:
        """Get color for a speaker ID."""
        return self.speaker_colors[speaker_id % len(self.speaker_colors)]

    def get_speaker_name(self, speaker_id: int) -> str:
        """Get name for a speaker ID."""
        for profile in self.speaker_profiles:
            # Check if this profile matches the speaker
            if profile.get("is_user") and speaker_id == 0:
                return profile["name"]
        return f"Speaker {speaker_id + 1}"

    @property
    def whisper_url(self) -> str:
        """Get the Whisper API URL."""
        return f"http://{self.server_host}:{self.whisper_port}"

    @property
    def diarization_url(self) -> str:
        """Get the diarization API URL."""
        return f"http://{self.server_host}:{self.diarization_port}"

    @property
    def translation_url(self) -> str:
        """Get the translation API URL."""
        return f"http://{self.server_host}:{self.translation_port}"

    @property
    def tts_url(self) -> str:
        """Get the TTS API URL."""
        return f"http://{self.server_host}:{self.tts_port}"
