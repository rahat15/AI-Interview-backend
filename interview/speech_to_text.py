# """
# Speech-to-Text Module for Voice-Only Interview Answers
# Converts audio to text using OpenAI Whisper (local whisper package)

# Improvements:
# - Converts any audio bytes to normalized WAV (16kHz mono) using ffmpeg (if available)
# - Avoids returning fake placeholder transcripts (returns None on failure)
# - Adds basic logging + safe temp file cleanup
# """

# from __future__ import annotations

# import os
# import tempfile
# import subprocess
# import logging
# from typing import Optional

# import whisper


# logger = logging.getLogger(__name__)
# if not logger.handlers:
#     logging.basicConfig(level=logging.INFO)


# class SpeechToTextConverter:
#     """
#     Local Whisper ASR wrapper.

#     Notes:
#     - Uses ffmpeg if installed to normalize audio into a 16k mono wav.
#     - Whisper's python package can also handle some formats, but normalization improves accuracy and consistency.
#     """

#     def __init__(self, model_name: str | None = None):
#         # Default to "base" as you had; you can change via env without code change.
#         self.model_name = model_name or os.getenv("WHISPER_MODEL_NAME", "base")
#         logger.info("Loading Whisper model: %s", self.model_name)
#         self.model = whisper.load_model(self.model_name)

#     def convert_audio_to_text(self, audio_data: bytes, language: Optional[str] = None) -> Optional[str]:
#         """
#         Convert audio bytes to text using Whisper.
#         Returns:
#             - transcript string on success
#             - None on failure / empty transcript
#         """
#         if not audio_data:
#             return None

#         temp_input_path = None
#         temp_wav_path = None

#         try:
#             # Write raw bytes as temp input (unknown container/codec)
#             with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
#                 f.write(audio_data)
#                 temp_input_path = f.name

#             # Normalize using ffmpeg -> wav 16k mono
#             temp_wav_path = self._normalize_to_wav_16k_mono(temp_input_path)

#             # Whisper transcription
#             # fp16=False is safer on CPU; if you run on GPU, Whisper may still handle fp16 internally.
#             result = self.model.transcribe(
#                 temp_wav_path,
#                 language=language,
#                 fp16=False,
#                 # You can tweak these for your domain:
#                 # initial_prompt="This is an interview answer.",
#                 # condition_on_previous_text=False,
#             )

#             text = (result.get("text") or "").strip()
#             return text if text else None

#         except Exception as e:
#             logger.exception("Whisper transcription failed: %s", e)
#             return None

#         finally:
#             # Cleanup
#             for p in (temp_input_path, temp_wav_path):
#                 if p and os.path.exists(p):
#                     try:
#                         os.unlink(p)
#                     except Exception:
#                         pass

#     def _normalize_to_wav_16k_mono(self, input_path: str) -> str:
#         """
#         Uses ffmpeg to decode input_path into a normalized WAV.
#         If ffmpeg isn't available, falls back to using input_path directly (less reliable).
#         """
#         # Create output temp wav path
#         out_fd, out_path = tempfile.mkstemp(suffix=".wav")
#         os.close(out_fd)

#         # If ffmpeg exists, normalize
#         if self._ffmpeg_available():
#             cmd = [
#                 "ffmpeg",
#                 "-y",
#                 "-i", input_path,
#                 "-ac", "1",
#                 "-ar", "16000",
#                 "-vn",
#                 out_path
#             ]
#             try:
#                 subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
#                 return out_path
#             except Exception:
#                 # If ffmpeg conversion fails, we keep out_path but it's invalid.
#                 # Remove and fallback to input path.
#                 try:
#                     os.unlink(out_path)
#                 except Exception:
#                     pass
#                 return input_path

#         # No ffmpeg: remove empty wav and fallback
#         try:
#             os.unlink(out_path)
#         except Exception:
#             pass
#         return input_path

#     @staticmethod
#     def _ffmpeg_available() -> bool:
#         try:
#             subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
#             return True
#         except Exception:
#             return False


# # Global instance
# speech_converter = SpeechToTextConverter()


"""
Speech-to-Text Module for Voice-Only Interview Answers

Uses Groq-hosted Whisper ASR (no local ML, no ffmpeg, no torch).

Behavior:
- Sends raw audio bytes to Groq
- Returns transcript string on success
- Returns None on failure
"""
from __future__ import annotations

import os
import logging
from typing import Optional

try:
    from groq import Groq
except ImportError as e:
    Groq = None


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def create_groq_client() -> "Groq":
    """
    Safely create a Groq client across SDK versions.

    IMPORTANT:
    - Do NOT pass proxies, timeout, or extra kwargs
    - Groq SDK auto-reads proxy settings from environment
    """
    if not Groq:
        raise RuntimeError("Groq SDK not installed. Run: pip install groq")

    api_key = os.getenv("GROQ_API_KEY")

    try:
        if api_key:
            try:
                # Preferred path (newer SDKs)
                return Groq(api_key=api_key)
            except TypeError:
                # Fallback for older SDKs
                client = Groq()
                if hasattr(client, "api_key"):
                    client.api_key = api_key
                return client

        # Final fallback (env-based auth)
        return Groq()

    except Exception as e:
        logger.error("❌ Failed to initialize Groq client", exc_info=True)
        raise RuntimeError("Groq client initialization failed") from e


class SpeechToTextConverter:
    """
    Groq-hosted Whisper ASR wrapper.

    Characteristics:
    - No local ML
    - No temp files
    - No ffmpeg
    - No proxy injection
    - Safe across Groq SDK versions
    """

    def __init__(self, model_name: Optional[str] = None):
        # Supported Groq Whisper models:
        # - whisper-large-v3
        # - whisper-large-v3-turbo (recommended if available)
        self.model_name = model_name or "whisper-large-v3"
        self.client = create_groq_client()

        logger.info(
            "🎤 Speech-to-text initialized using Groq Whisper model: %s",
            self.model_name
        )

    def convert_audio_to_text(self, audio_data: bytes, language: Optional[str] = None, ) -> Optional[str]:
        if not audio_data:
            logger.warning("No audio data received for transcription")
            return "No audio detected"
        
        if len(audio_data) < 100:  # Too small to be valid audio
            logger.warning(f"Audio data too small: {len(audio_data)} bytes")
            return "Audio file is empty or corrupted"

        try:
            logger.info(f"Processing audio: {len(audio_data)} bytes")
            response = self.client.audio.transcriptions.create(
                file=("audio.wav", audio_data),
                model=self.model_name,
                language=language,
                response_format="verbose_json",
            )

            logger.info("ASR response type: %s", type(response))

            text = None

            if isinstance(response, dict):
                text = response.get("text")

                if not text and "segments" in response:
                    text = " ".join(
                        seg.get("text", "") for seg in response.get("segments", [])
                    )
            else:
                text = getattr(response, "text", None)

            text = (text or "").strip()
            if not text:
                logger.warning("Transcription returned empty text")
                return "Could not understand audio"
            
            logger.info(f"✅ Transcription successful: {text[:100]}...")
            return text

        except Exception as e:
            logger.exception(f"Groq transcription failed: {e}")
            return "Speech recognition service unavailable"



# ── Global singleton (same API contract as before) ───────────
# Create instance lazily and fail-safe when GROQ API key isn't present or initialization fails
try:
    speech_converter = SpeechToTextConverter()
except Exception:
    logger.exception("Failed to initialize speech converter; ASR disabled")
    speech_converter = None  # Modules using this should handle None gracefully
