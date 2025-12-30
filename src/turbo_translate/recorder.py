"""Audio recording with voice activity detection."""

import io
import platform
import queue
import subprocess
import threading
import wave
from typing import Callable

import numpy as np


class AudioRecorder:
    """Records audio from microphone with voice activity detection."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        device_index: int | None = None,
        gain: float = 1.0,
        silence_threshold: float = 0.03,
        voice_timeout: float = 2.0,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.gain = gain
        self.silence_threshold = silence_threshold
        self.voice_timeout = voice_timeout

        self._pyaudio = None
        self._stream = None
        self._recording = False
        self._thread = None
        self._frames: list[bytes] = []
        self._level = 0.0
        self._level_lock = threading.Lock()

        # Voice activity detection
        self._voice_active = False
        self._silence_start = 0.0
        self._audio_queue: queue.Queue = queue.Queue()

        # Callbacks
        self._level_callback: Callable[[float], None] | None = None
        self._segment_callback: Callable[[bytes], None] | None = None

    def _init_pyaudio(self):
        """Initialize PyAudio."""
        if self._pyaudio is None:
            import pyaudio

            self._pyaudio = pyaudio.PyAudio()

    def get_devices(self) -> list[dict]:
        """Get available input devices."""
        self._init_pyaudio()
        devices = []

        # On Linux, prefer PipeWire sources
        if platform.system() == "Linux":
            pw_sources = self._get_pipewire_sources()
            if pw_sources:
                return pw_sources

        # Fall back to PyAudio enumeration
        for i in range(self._pyaudio.get_device_count()):
            info = self._pyaudio.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                devices.append({
                    "index": i,
                    "name": info["name"],
                    "channels": info["maxInputChannels"],
                    "sample_rate": int(info["defaultSampleRate"]),
                })

        return devices

    def _get_pipewire_sources(self) -> list[dict]:
        """Get PipeWire audio sources on Linux."""
        try:
            result = subprocess.run(
                ["pactl", "list", "sources", "short"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                return []

            sources = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    sources.append({
                        "index": int(parts[0]),
                        "name": parts[1],
                        "channels": 2,
                        "sample_rate": 48000,
                    })
            return sources
        except Exception:
            return []

    def start_continuous(
        self,
        level_callback: Callable[[float], None] | None = None,
        segment_callback: Callable[[bytes], None] | None = None,
    ):
        """
        Start continuous listening with voice activity detection.

        Args:
            level_callback: Called with audio level (0.0-1.0)
            segment_callback: Called with WAV data when speech segment ends
        """
        if self._recording:
            return

        self._init_pyaudio()
        self._level_callback = level_callback
        self._segment_callback = segment_callback
        self._recording = True
        self._frames = []
        self._voice_active = False

        import pyaudio

        try:
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
            )
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            self._recording = False
            return

        self._thread = threading.Thread(target=self._continuous_loop, daemon=True)
        self._thread.start()

    def _continuous_loop(self):
        """Continuous recording loop with VAD."""
        import time

        silence_frames = 0
        frames_for_timeout = int(self.voice_timeout * self.sample_rate / self.chunk_size)

        while self._recording:
            try:
                data = self._stream.read(self.chunk_size, exception_on_overflow=False)
            except Exception:
                continue

            # Calculate level
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            samples = samples * self.gain
            level = np.abs(samples).mean() / 32768.0

            with self._level_lock:
                self._level = level

            if self._level_callback:
                self._level_callback(level)

            # Voice activity detection
            is_voice = level > self.silence_threshold

            if is_voice:
                if not self._voice_active:
                    # Voice started
                    self._voice_active = True
                    self._frames = []
                silence_frames = 0
                self._frames.append(data)
            elif self._voice_active:
                # Voice was active, now silent
                silence_frames += 1
                self._frames.append(data)  # Keep some silence

                if silence_frames >= frames_for_timeout:
                    # Speech segment ended
                    self._voice_active = False
                    if len(self._frames) > frames_for_timeout:
                        # Remove trailing silence
                        self._frames = self._frames[:-frames_for_timeout]

                    if self._frames and self._segment_callback:
                        wav_data = self._frames_to_wav(self._frames)
                        self._segment_callback(wav_data)

                    self._frames = []
                    silence_frames = 0

    def _frames_to_wav(self, frames: list[bytes]) -> bytes:
        """Convert frames to WAV format."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))
        return buffer.getvalue()

    def stop(self):
        """Stop recording."""
        self._recording = False

        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def get_level(self) -> float:
        """Get current audio level."""
        with self._level_lock:
            return self._level

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None

    def record_for_enrollment(self, duration: float = 5.0) -> bytes:
        """
        Record audio for speaker enrollment.

        Args:
            duration: Recording duration in seconds

        Returns:
            WAV audio data
        """
        self._init_pyaudio()
        import pyaudio

        frames = []

        try:
            stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
            )

            num_chunks = int(duration * self.sample_rate / self.chunk_size)
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)

            stream.stop_stream()
            stream.close()

        except Exception as e:
            print(f"Enrollment recording error: {e}")
            return b""

        return self._frames_to_wav(frames)
