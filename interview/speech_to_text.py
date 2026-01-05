"""
Speech-to-Text Module for Voice-Only Interview Answers
Converts audio to text using OpenAI Whisper (local whisper package)

Improvements:
- Converts any audio bytes to normalized WAV (16kHz mono) using ffmpeg (if available)
- Avoids returning fake placeholder transcripts (returns None on failure)
- Adds basic logging + safe temp file cleanup
"""

from __future__ import annotations

import os
import tempfile
import subprocess
import logging
from typing import Optional

import whisper


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class SpeechToTextConverter:
    """
    Local Whisper ASR wrapper.

    Notes:
    - Uses ffmpeg if installed to normalize audio into a 16k mono wav.
    - Whisper's python package can also handle some formats, but normalization improves accuracy and consistency.
    """

    def __init__(self, model_name: str | None = None):
        # Default to "base" as you had; you can change via env without code change.
        self.model_name = model_name or os.getenv("WHISPER_MODEL_NAME", "base")
        logger.info("Loading Whisper model: %s", self.model_name)
        self.model = whisper.load_model(self.model_name)

    def convert_audio_to_text(self, audio_data: bytes, language: Optional[str] = None) -> Optional[str]:
        """
        Convert audio bytes to text using Whisper.
        Returns:
            - transcript string on success
            - None on failure / empty transcript
        """
        if not audio_data:
            return None

        temp_input_path = None
        temp_wav_path = None

        try:
            # Write raw bytes as temp input (unknown container/codec)
            with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
                f.write(audio_data)
                temp_input_path = f.name

            # Normalize using ffmpeg -> wav 16k mono
            temp_wav_path = self._normalize_to_wav_16k_mono(temp_input_path)

            # Whisper transcription
            # fp16=False is safer on CPU; if you run on GPU, Whisper may still handle fp16 internally.
            result = self.model.transcribe(
                temp_wav_path,
                language=language,
                fp16=False,
                # You can tweak these for your domain:
                # initial_prompt="This is an interview answer.",
                # condition_on_previous_text=False,
            )

            text = (result.get("text") or "").strip()
            return text if text else None

        except Exception as e:
            logger.exception("Whisper transcription failed: %s", e)
            return None

        finally:
            # Cleanup
            for p in (temp_input_path, temp_wav_path):
                if p and os.path.exists(p):
                    try:
                        os.unlink(p)
                    except Exception:
                        pass

    def _normalize_to_wav_16k_mono(self, input_path: str) -> str:
        """
        Uses ffmpeg to decode input_path into a normalized WAV.
        If ffmpeg isn't available, falls back to using input_path directly (less reliable).
        """
        # Create output temp wav path
        out_fd, out_path = tempfile.mkstemp(suffix=".wav")
        os.close(out_fd)

        # If ffmpeg exists, normalize
        if self._ffmpeg_available():
            cmd = [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-ac", "1",
                "-ar", "16000",
                "-vn",
                out_path
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return out_path
            except Exception:
                # If ffmpeg conversion fails, we keep out_path but it's invalid.
                # Remove and fallback to input path.
                try:
                    os.unlink(out_path)
                except Exception:
                    pass
                return input_path

        # No ffmpeg: remove empty wav and fallback
        try:
            os.unlink(out_path)
        except Exception:
            pass
        return input_path

    @staticmethod
    def _ffmpeg_available() -> bool:
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception:
            return False


# Global instance
speech_converter = SpeechToTextConverter()
