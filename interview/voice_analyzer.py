"""
Voice Analysis Module for Interview Evaluation
Analyzes speech patterns, fluency, confidence proxies, and delivery characteristics.

Improvements:
- Uses librosa.pyin for robust pitch estimation
- Speech rate uses transcript-based WPM when provided
- Confidence scoring based on stability/control
- Explicit analysis_ok + error fields
- NEW: Scores are rescaled and reported out of 10 (weights unchanged)
"""

from __future__ import annotations

import io
import os
import logging
from typing import Dict, Optional, Any

import librosa
import numpy as np
import requests
import soundfile as sf


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class VoiceAnalyzer:
    """
    VoiceAnalyzer computes delivery-related metrics from audio and
    produces both raw (weighted) scores and scaled scores out of 10.
    """

    # ------------------------- SCORE METADATA -------------------------

    SCORE_MAX = {
        "fluency": 2.0,
        "clarity": 1.5,
        "confidence": 1.5,
        "pace": 1.0,
        "total": 6.0,
    }

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    # ------------------------- PUBLIC API -------------------------

    def analyze_voice(
        self,
        audio_data: bytes = None,
        audio_url: str = None,
        transcript: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            if audio_url:
                audio_data = self._download_audio(audio_url)

            if not audio_data:
                return self._fail("no_audio_data")

            logger.info(f"Processing audio data: {len(audio_data)} bytes")

            # -------- IN-MEMORY AUDIO DECODE (NO TEMP FILES) --------
            try:
                audio_buffer = io.BytesIO(audio_data)
                y, sr = sf.read(audio_buffer, dtype="float32")
            except Exception as e:
                logger.warning(f"Failed to read audio with soundfile: {e}")
                # Try alternative approach - save to temp file and read
                import tempfile
                try:
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                        tmp_file.write(audio_data)
                        tmp_path = tmp_file.name
                    
                    y, sr = sf.read(tmp_path, dtype="float32")
                    os.unlink(tmp_path)
                except Exception as e2:
                    logger.error(f"Failed to read audio from temp file: {e2}")
                    return self._fail("audio_decode_failed")

            if y is None or len(y) == 0:
                return self._fail("empty_audio_after_decode")

            logger.info(f"Audio decoded successfully: {len(y)} samples at {sr}Hz")

            # Convert to mono if needed
            if y.ndim > 1:
                y = np.mean(y, axis=1)

            # Resample if needed
            if sr != self.sample_rate:
                y = librosa.resample(y, orig_sr=sr, target_sr=self.sample_rate)
                sr = self.sample_rate

            analysis = self._analyze_audio_features(y, sr, transcript)
            
            # Add plagiarism detection if transcript is available
            if transcript and transcript.strip():
                try:
                    from interview.plagiarism_detector import plagiarism_detector
                    plagiarism_result = plagiarism_detector.detect_plagiarism(transcript)
                    analysis["plagiarism_analysis"] = plagiarism_result
                except Exception as e:
                    logger.warning(f"Plagiarism detection failed: {e}")
                    analysis["plagiarism_analysis"] = {
                        "plagiarism_detected": False,
                        "risk_score": 0.0,
                        "analysis_ok": False,
                        "error": "Detection unavailable"
                    }
            
            analysis["analysis_ok"] = True
            return analysis

        except Exception as e:
            logger.exception("Voice analysis error: %s", e)
            return self._fail("voice_analysis_exception")

    # ------------------------- AUDIO INGEST -------------------------

    def _download_audio(self, url: str) -> Optional[bytes]:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
        except Exception:
            pass
        return None

    # ------------------------- FEATURE EXTRACTION -------------------------

    def _analyze_audio_features(
        self,
        y: np.ndarray,
        sr: int,
        transcript: Optional[str],
    ) -> Dict[str, Any]:

        duration = float(len(y) / sr)

        intervals = librosa.effects.split(y, top_db=25)
        speech_duration = float(sum((e - s) / sr for s, e in intervals)) if len(intervals) else 0.0
        pause_ratio = float(1.0 - (speech_duration / duration)) if duration > 0 else 1.0
        speech_segments = int(len(intervals))

        speech_rate_wpm = self._speech_rate_wpm(duration, transcript, intervals, sr)
        pitch_stats = self._analyze_pitch_pyin(y, sr)
        energy_stats = self._analyze_energy(y)

        score_block = self._calculate_voice_scores(
            speech_rate_wpm,
            pause_ratio,
            pitch_stats,
            energy_stats,
            duration,
        )

        return {
            "voice_scores": score_block,
            "voice_metrics": {
                "duration": round(duration, 2),
                "speech_rate": round(speech_rate_wpm, 1),
                "avg_pitch": round(pitch_stats["mean"], 1),
                "pitch_variation": round(pitch_stats["std"], 1),
                "avg_energy": round(energy_stats["mean"], 4),
                "pause_ratio": round(pause_ratio, 3),
                "speech_segments": speech_segments,
                "speech_duration": round(speech_duration, 2),
                "wpm_source": "transcript" if transcript and transcript.strip() else "estimated",
            },
        }

    def _speech_rate_wpm(
        self,
        duration: float,
        transcript: Optional[str],
        intervals: np.ndarray,
        sr: int,
    ) -> float:
        if transcript:
            words = [w for w in transcript.split() if w.strip()]
            return float((len(words) / duration) * 60.0) if duration > 0 else 0.0

        if len(intervals) == 0 or duration <= 0:
            return 0.0

        speech_duration = sum((e - s) / sr for s, e in intervals)
        est_words = 2.2 * speech_duration
        return float((est_words / duration) * 60.0)

    def _analyze_pitch_pyin(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        try:
            f0, _, _ = librosa.pyin(
                y,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
            )
            voiced_f0 = f0[~np.isnan(f0)] if f0 is not None else np.array([])
            if voiced_f0.size == 0:
                return {"mean": 0.0, "std": 0.0, "range": 0.0}

            return {
                "mean": float(np.mean(voiced_f0)),
                "std": float(np.std(voiced_f0)),
                "range": float(np.ptp(voiced_f0)),
            }
        except Exception:
            return {"mean": 0.0, "std": 0.0, "range": 0.0}

    def _analyze_energy(self, y: np.ndarray) -> Dict[str, float]:
        rms = librosa.feature.rms(y=y)[0]
        return {
            "mean": float(np.mean(rms)) if rms.size else 0.0,
            "std": float(np.std(rms)) if rms.size else 0.0,
            "max": float(np.max(rms)) if rms.size else 0.0,
        }

    # ------------------------- SCORING (UNCHANGED LOGIC) -------------------------

    def _calculate_voice_scores(
        self,
        speech_rate_wpm: float,
        pause_ratio: float,
        pitch_stats: Dict[str, float],
        energy_stats: Dict[str, float],
        duration: float,
    ) -> Dict[str, Any]:

        fluency = self._score_fluency(speech_rate_wpm, pause_ratio)
        clarity = self._score_clarity(energy_stats, duration)
        confidence = self._score_confidence(pitch_stats, energy_stats, speech_rate_wpm)
        pace = self._score_pace(speech_rate_wpm, duration)

        total = fluency + clarity + confidence + pace

        raw = {
            "fluency": round(fluency, 2),
            "clarity": round(clarity, 2),
            "confidence": round(confidence, 2),
            "pace": round(pace, 2),
            "total": round(total, 2),
        }

        scaled_out_of_10 = {
            k: round((raw[k] / self.SCORE_MAX[k]) * 10.0, 2)
            for k in raw
        }

        return {
            "raw": raw,
            "scaled_out_of_10": scaled_out_of_10,
            "weights": {
                "fluency": round(self.SCORE_MAX["fluency"] / self.SCORE_MAX["total"], 3),
                "clarity": round(self.SCORE_MAX["clarity"] / self.SCORE_MAX["total"], 3),
                "confidence": round(self.SCORE_MAX["confidence"] / self.SCORE_MAX["total"], 3),
                "pace": round(self.SCORE_MAX["pace"] / self.SCORE_MAX["total"], 3),
            },
        }

    # ------------------------- INDIVIDUAL SCORE FUNCTIONS -------------------------

    def _score_fluency(self, wpm: float, pause_ratio: float) -> float:
        score = 1.0
        if 120 <= wpm <= 175:
            score += 0.5
        elif 105 <= wpm <= 190:
            score += 0.3
        elif wpm < 90 or wpm > 210:
            score -= 0.3

        if 0.12 <= pause_ratio <= 0.28:
            score += 0.5
        elif 0.08 <= pause_ratio <= 0.35:
            score += 0.3
        elif pause_ratio > 0.45:
            score -= 0.4
        elif pause_ratio < 0.05:
            score -= 0.2

        return float(max(0.0, min(2.0, score)))

    def _score_clarity(self, energy_stats: Dict[str, float], duration: float) -> float:
        score = 0.6
        mean_e = energy_stats.get("mean", 0.0)
        std_e = energy_stats.get("std", 0.0)

        if mean_e > 0 and std_e <= mean_e * 0.6:
            score += 0.4
        elif mean_e > 0 and std_e <= mean_e * 0.9:
            score += 0.2

        if mean_e >= 0.01:
            score += 0.3
        elif mean_e >= 0.006:
            score += 0.15
        else:
            score -= 0.2

        if duration >= 8:
            score += 0.2
        elif duration >= 4:
            score += 0.1

        return float(max(0.0, min(1.5, score)))

    def _score_confidence(self, pitch_stats: Dict[str, float], energy_stats: Dict[str, float], wpm: float) -> float:
        score = 0.6
        pitch_std = pitch_stats.get("std", 0.0)
        pitch_mean = pitch_stats.get("mean", 0.0)
        mean_e = energy_stats.get("mean", 0.0)

        if pitch_mean > 0:
            if pitch_std <= 25:
                score += 0.4
            elif pitch_std <= 40:
                score += 0.2
            else:
                score -= 0.2

        if mean_e >= 0.01:
            score += 0.2
        elif mean_e < 0.004:
            score -= 0.1

        if 115 <= wpm <= 190:
            score += 0.3
        elif wpm < 90 or wpm > 210:
            score -= 0.2

        return float(max(0.0, min(1.5, score)))

    def _score_pace(self, wpm: float, duration: float) -> float:
        score = 0.4
        if 125 <= wpm <= 175:
            score += 0.5
        elif 105 <= wpm <= 195:
            score += 0.3
        elif wpm < 90 or wpm > 210:
            score -= 0.2

        if duration >= 6:
            score += 0.1

        return float(max(0.0, min(1.0, score)))

    # ------------------------- FAILURE -------------------------

    def _fail(self, code: str) -> Dict[str, Any]:
        logger.warning(f"Voice analysis failed with code: {code}")
        return {
            "analysis_ok": False,
            "error": code,
            "voice_scores": {
                "fluency": 0.0,
                "clarity": 0.0,
                "confidence": 0.0,
                "pace": 0.0,
                "total": 0.0
            },
            "voice_metrics": {
                "duration": 0.0,
                "speech_rate": 0.0,
                "avg_pitch": 0.0,
                "pitch_variation": 0.0,
                "avg_energy": 0.0,
                "pause_ratio": 1.0,
                "speech_segments": 0,
                "speech_duration": 0.0,
                "wpm_source": "none",
            },
        }
