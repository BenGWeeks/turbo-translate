"""API clients for backend services."""

from dataclasses import dataclass
from typing import Any

import httpx

from .config import Config


class APIError(Exception):
    """Base exception for API errors."""

    pass


@dataclass
class TranscriptionSegment:
    """A segment of transcribed speech."""

    text: str
    start: float
    end: float
    speaker: int | None = None


@dataclass
class DiarizedTranscription:
    """Transcription with speaker diarization."""

    segments: list[TranscriptionSegment]
    language: str
    duration: float


class WhisperClient:
    """Client for the Whisper speech-to-text service."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.whisper_url

    def transcribe(self, audio_data: bytes, language: str | None = None) -> DiarizedTranscription:
        """
        Transcribe audio data.

        Args:
            audio_data: WAV audio data
            language: Language code (e.g., 'hu', 'en')

        Returns:
            DiarizedTranscription with segments
        """
        url = f"{self.base_url}/v1/audio/transcriptions"

        files = {"file": ("audio.wav", audio_data, "audio/wav")}
        data: dict[str, Any] = {
            "model": "whisper-1",
            "response_format": "verbose_json",
        }
        if language:
            data["language"] = language

        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, files=files, data=data, headers=headers)
                response.raise_for_status()
                result = response.json()

                segments = []
                for seg in result.get("segments", []):
                    segments.append(
                        TranscriptionSegment(
                            text=seg.get("text", "").strip(),
                            start=seg.get("start", 0.0),
                            end=seg.get("end", 0.0),
                            speaker=None,  # Will be filled by diarization
                        )
                    )

                # If no segments, create one from the text
                if not segments and result.get("text"):
                    segments.append(
                        TranscriptionSegment(
                            text=result["text"].strip(),
                            start=0.0,
                            end=result.get("duration", 0.0),
                            speaker=None,
                        )
                    )

                return DiarizedTranscription(
                    segments=segments,
                    language=result.get("language", language or "unknown"),
                    duration=result.get("duration", 0.0),
                )

        except httpx.TimeoutException:
            raise APIError("Transcription request timed out")
        except httpx.HTTPStatusError as e:
            raise APIError(f"Transcription failed: {e.response.status_code}")
        except Exception as e:
            raise APIError(f"Transcription error: {e}")


class DiarizationClient:
    """Client for speaker diarization service."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.diarization_url

    def diarize(self, audio_data: bytes) -> list[dict]:
        """
        Perform speaker diarization on audio.

        Args:
            audio_data: WAV audio data

        Returns:
            List of speaker segments with start, end, speaker_id
        """
        url = f"{self.base_url}/diarize"

        files = {"file": ("audio.wav", audio_data, "audio/wav")}

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, files=files)
                response.raise_for_status()
                return response.json().get("segments", [])

        except httpx.TimeoutException:
            raise APIError("Diarization request timed out")
        except httpx.HTTPStatusError as e:
            raise APIError(f"Diarization failed: {e.response.status_code}")
        except Exception as e:
            raise APIError(f"Diarization error: {e}")

    def identify_speaker(self, audio_data: bytes) -> dict:
        """
        Identify a speaker from audio using enrolled profiles.

        Args:
            audio_data: WAV audio data

        Returns:
            Speaker identification result with speaker_id and confidence
        """
        url = f"{self.base_url}/identify"

        files = {"file": ("audio.wav", audio_data, "audio/wav")}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, files=files)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            raise APIError(f"Speaker identification error: {e}")

    def enroll_speaker(self, audio_data: bytes, speaker_name: str, is_user: bool = False) -> dict:
        """
        Enroll a new speaker profile.

        Args:
            audio_data: WAV audio data with speaker's voice
            speaker_name: Name for the speaker
            is_user: Whether this is the primary user

        Returns:
            Enrollment result with speaker_id
        """
        url = f"{self.base_url}/enroll"

        files = {"file": ("audio.wav", audio_data, "audio/wav")}
        data = {"name": speaker_name, "is_user": str(is_user).lower()}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, files=files, data=data)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            raise APIError(f"Speaker enrollment error: {e}")


class TranslationClient:
    """Client for translation service."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.translation_url

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text between languages.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text
        """
        url = f"{self.base_url}/translate"

        data = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
                return result.get("translatedText", text)

        except httpx.TimeoutException:
            raise APIError("Translation request timed out")
        except httpx.HTTPStatusError as e:
            raise APIError(f"Translation failed: {e.response.status_code}")
        except Exception as e:
            raise APIError(f"Translation error: {e}")

    def detect_language(self, text: str) -> str:
        """
        Detect the language of text.

        Args:
            text: Text to analyze

        Returns:
            Detected language code
        """
        url = f"{self.base_url}/detect"

        data = {"q": text}

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=data)
                response.raise_for_status()
                result = response.json()
                if result and len(result) > 0:
                    return result[0].get("language", "unknown")
                return "unknown"

        except Exception:
            return "unknown"


class TTSClient:
    """Client for text-to-speech service."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.tts_url

    def synthesize(self, text: str, language: str) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to speak
            language: Language code

        Returns:
            WAV audio data
        """
        url = f"{self.base_url}/api/tts"

        data = {
            "text": text,
            "language": language,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, json=data)
                response.raise_for_status()
                return response.content

        except httpx.TimeoutException:
            raise APIError("TTS request timed out")
        except httpx.HTTPStatusError as e:
            raise APIError(f"TTS failed: {e.response.status_code}")
        except Exception as e:
            raise APIError(f"TTS error: {e}")


class TranslationPipeline:
    """Combined pipeline for transcription, diarization, and translation."""

    def __init__(self, config: Config):
        self.config = config
        self.whisper = WhisperClient(config)
        self.diarization = DiarizationClient(config)
        self.translation = TranslationClient(config)
        self.tts = TTSClient(config)

    def process_audio(
        self, audio_data: bytes, source_language: str | None = None
    ) -> list[dict]:
        """
        Process audio through the full pipeline.

        Args:
            audio_data: WAV audio data
            source_language: Expected source language (optional)

        Returns:
            List of processed segments with text, translation, speaker info
        """
        # Step 1: Transcribe
        transcription = self.whisper.transcribe(audio_data, source_language)

        # Step 2: Diarize
        try:
            diarization_segments = self.diarization.diarize(audio_data)
        except APIError:
            # Fall back to single speaker if diarization fails
            diarization_segments = [
                {"start": 0, "end": transcription.duration, "speaker": 0}
            ]

        # Step 3: Merge transcription with diarization
        results = []
        for seg in transcription.segments:
            # Find the speaker for this segment
            speaker_id = 0
            for diar_seg in diarization_segments:
                seg_mid = (seg.start + seg.end) / 2
                if diar_seg["start"] <= seg_mid <= diar_seg["end"]:
                    speaker_id = diar_seg.get("speaker", 0)
                    break

            # Step 4: Translate
            detected_lang = transcription.language
            if detected_lang == self.config.target_language:
                # Already in target language, translate to source
                translation = self.translation.translate(
                    seg.text, detected_lang, self.config.source_language
                )
            else:
                # Translate to target language
                translation = self.translation.translate(
                    seg.text, detected_lang, self.config.target_language
                )

            results.append({
                "text": seg.text,
                "translation": translation,
                "start": seg.start,
                "end": seg.end,
                "speaker_id": speaker_id,
                "language": detected_lang,
            })

        return results

    def speak_translation(self, text: str, language: str) -> bytes:
        """
        Generate speech for translated text.

        Args:
            text: Text to speak
            language: Language code

        Returns:
            WAV audio data
        """
        return self.tts.synthesize(text, language)
