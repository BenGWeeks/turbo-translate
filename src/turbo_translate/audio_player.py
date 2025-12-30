"""Audio playback for TTS output."""

import io
import threading
import wave

import numpy as np


class AudioPlayer:
    """Plays audio data through speakers."""

    def __init__(self):
        self._pyaudio = None
        self._playing = False
        self._thread = None

    def _init_pyaudio(self):
        """Initialize PyAudio."""
        if self._pyaudio is None:
            import pyaudio

            self._pyaudio = pyaudio.PyAudio()

    def play_wav(self, wav_data: bytes, blocking: bool = False):
        """
        Play WAV audio data.

        Args:
            wav_data: WAV format audio data
            blocking: If True, wait for playback to complete
        """
        if blocking:
            self._play_wav_sync(wav_data)
        else:
            self._thread = threading.Thread(
                target=self._play_wav_sync, args=(wav_data,), daemon=True
            )
            self._thread.start()

    def _play_wav_sync(self, wav_data: bytes):
        """Play WAV data synchronously."""
        self._init_pyaudio()
        import pyaudio

        try:
            buffer = io.BytesIO(wav_data)
            with wave.open(buffer, "rb") as wf:
                stream = self._pyaudio.open(
                    format=self._pyaudio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                )

                self._playing = True
                chunk_size = 1024
                data = wf.readframes(chunk_size)

                while data and self._playing:
                    stream.write(data)
                    data = wf.readframes(chunk_size)

                stream.stop_stream()
                stream.close()

        except Exception as e:
            print(f"Audio playback error: {e}")
        finally:
            self._playing = False

    def stop(self):
        """Stop playback."""
        self._playing = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None
