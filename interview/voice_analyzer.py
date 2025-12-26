"""
Voice Analysis Module for Interview Evaluation
Analyzes speech patterns, fluency, confidence, and communication skills
"""

import librosa
import numpy as np
from typing import Dict, Optional, Any
import tempfile
import os
import requests
from io import BytesIO

class VoiceAnalyzer:
    def __init__(self):
        self.sample_rate = 22050
        
    def analyze_voice(self, audio_data: bytes = None, audio_url: str = None) -> Dict[str, Any]:
        """Analyze voice from audio data or URL"""
        try:
            # Load audio
            if audio_url:
                audio_data = self._download_audio(audio_url)
            
            if not audio_data:
                return self._get_default_voice_scores()
            
            # Save to temp file and analyze
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                y, sr = librosa.load(temp_path, sr=self.sample_rate)
                analysis = self._analyze_audio_features(y, sr)
                return analysis
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            print(f"Voice analysis error: {e}")
            return self._get_default_voice_scores()
    
    def _download_audio(self, url: str) -> Optional[bytes]:
        """Download audio from URL"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
        except:
            pass
        return None
    
    def _analyze_audio_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract voice features and calculate scores"""
        
        # Basic audio properties
        duration = len(y) / sr
        
        # Speech rate (words per minute estimate)
        speech_rate = self._estimate_speech_rate(y, sr, duration)
        
        # Pitch analysis
        pitch_stats = self._analyze_pitch(y, sr)
        
        # Energy and volume
        energy_stats = self._analyze_energy(y)
        
        # Pauses and fluency
        fluency_stats = self._analyze_fluency(y, sr)
        
        # Calculate composite scores
        scores = self._calculate_voice_scores(
            speech_rate, pitch_stats, energy_stats, fluency_stats, duration
        )
        
        return {
            "voice_scores": scores,
            "voice_metrics": {
                "duration": round(duration, 2),
                "speech_rate": round(speech_rate, 1),
                "avg_pitch": round(pitch_stats["mean"], 1),
                "pitch_variation": round(pitch_stats["std"], 1),
                "avg_energy": round(energy_stats["mean"], 3),
                "pause_ratio": round(fluency_stats["pause_ratio"], 2),
                "speech_segments": fluency_stats["segments"]
            }
        }
    
    def _estimate_speech_rate(self, y: np.ndarray, sr: int, duration: float) -> float:
        """Estimate words per minute"""
        # Detect speech segments
        intervals = librosa.effects.split(y, top_db=20)
        speech_duration = sum([(end - start) / sr for start, end in intervals])
        
        if speech_duration == 0:
            return 0
        
        # Rough estimate: 4-6 syllables per second = 120-180 WPM
        # Use energy-based estimation
        syllable_rate = len(intervals) / speech_duration * 2.5  # Rough conversion
        return min(200, syllable_rate * 60 / 2.5)  # Cap at 200 WPM
    
    def _analyze_pitch(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """Analyze pitch characteristics"""
        try:
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr, threshold=0.1)
            pitch_values = []
            
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                return {
                    "mean": np.mean(pitch_values),
                    "std": np.std(pitch_values),
                    "range": np.max(pitch_values) - np.min(pitch_values)
                }
        except:
            pass
        
        return {"mean": 150.0, "std": 20.0, "range": 50.0}
    
    def _analyze_energy(self, y: np.ndarray) -> Dict[str, float]:
        """Analyze energy/volume characteristics"""
        rms = librosa.feature.rms(y=y)[0]
        return {
            "mean": np.mean(rms),
            "std": np.std(rms),
            "max": np.max(rms)
        }
    
    def _analyze_fluency(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Analyze speech fluency and pauses"""
        # Detect speech/silence segments
        intervals = librosa.effects.split(y, top_db=20)
        
        if len(intervals) == 0:
            return {"pause_ratio": 1.0, "segments": 0}
        
        speech_duration = sum([(end - start) / sr for start, end in intervals])
        total_duration = len(y) / sr
        pause_ratio = 1 - (speech_duration / total_duration) if total_duration > 0 else 1.0
        
        return {
            "pause_ratio": pause_ratio,
            "segments": len(intervals)
        }
    
    def _calculate_voice_scores(self, speech_rate: float, pitch_stats: Dict, 
                               energy_stats: Dict, fluency_stats: Dict, duration: float) -> Dict[str, float]:
        """Calculate voice quality scores"""
        
        # Fluency score (0-2 points)
        fluency_score = self._score_fluency(speech_rate, fluency_stats["pause_ratio"])
        
        # Clarity score (0-1.5 points)
        clarity_score = self._score_clarity(energy_stats, duration)
        
        # Confidence score (0-1.5 points)
        confidence_score = self._score_confidence(pitch_stats, energy_stats, speech_rate)
        
        # Pace score (0-1 point)
        pace_score = self._score_pace(speech_rate, duration)
        
        return {
            "fluency": round(fluency_score, 2),
            "clarity": round(clarity_score, 2),
            "confidence": round(confidence_score, 2),
            "pace": round(pace_score, 2),
            "total": round(fluency_score + clarity_score + confidence_score + pace_score, 2)
        }
    
    def _score_fluency(self, speech_rate: float, pause_ratio: float) -> float:
        """Score speech fluency (0-2 points)"""
        score = 1.0  # Base score
        
        # Optimal speech rate: 140-180 WPM
        if 140 <= speech_rate <= 180:
            score += 0.5
        elif 120 <= speech_rate <= 200:
            score += 0.3
        elif speech_rate < 100 or speech_rate > 220:
            score -= 0.3
        
        # Pause analysis
        if pause_ratio < 0.15:  # Very few pauses
            score += 0.5
        elif pause_ratio < 0.25:  # Normal pauses
            score += 0.3
        elif pause_ratio > 0.4:  # Too many pauses
            score -= 0.4
        
        return max(0, min(2.0, score))
    
    def _score_clarity(self, energy_stats: Dict, duration: float) -> float:
        """Score speech clarity (0-1.5 points)"""
        score = 0.5  # Base score
        
        # Energy consistency
        if energy_stats["std"] < energy_stats["mean"] * 0.5:
            score += 0.4  # Consistent volume
        
        # Adequate volume
        if energy_stats["mean"] > 0.01:
            score += 0.3
        
        # Duration bonus (longer answers tend to be clearer)
        if duration > 10:
            score += 0.3
        elif duration > 5:
            score += 0.2
        
        return max(0, min(1.5, score))
    
    def _score_confidence(self, pitch_stats: Dict, energy_stats: Dict, speech_rate: float) -> float:
        """Score confidence indicators (0-1.5 points)"""
        score = 0.5  # Base score
        
        # Pitch variation (confident speakers vary pitch)
        if pitch_stats["std"] > 15:
            score += 0.4
        elif pitch_stats["std"] > 10:
            score += 0.2
        
        # Energy level (confident speakers have good energy)
        if energy_stats["mean"] > 0.02:
            score += 0.3
        elif energy_stats["mean"] > 0.01:
            score += 0.2
        
        # Speech rate confidence
        if 130 <= speech_rate <= 190:
            score += 0.3
        
        return max(0, min(1.5, score))
    
    def _score_pace(self, speech_rate: float, duration: float) -> float:
        """Score speaking pace (0-1 point)"""
        score = 0.3  # Base score
        
        # Optimal pace
        if 140 <= speech_rate <= 170:
            score += 0.4
        elif 120 <= speech_rate <= 190:
            score += 0.3
        
        # Duration appropriateness
        if 15 <= duration <= 120:  # 15 seconds to 2 minutes
            score += 0.3
        elif 10 <= duration <= 180:
            score += 0.2
        
        return max(0, min(1.0, score))
    
    def _get_default_voice_scores(self) -> Dict[str, Any]:
        """Return default scores when voice analysis fails"""
        return {
            "voice_scores": {
                "fluency": 1.0,
                "clarity": 0.8,
                "confidence": 0.8,
                "pace": 0.6,
                "total": 3.2
            },
            "voice_metrics": {
                "duration": 0,
                "speech_rate": 0,
                "avg_pitch": 0,
                "pitch_variation": 0,
                "avg_energy": 0,
                "pause_ratio": 0,
                "speech_segments": 0
            }
        }

# Global instance
voice_analyzer = VoiceAnalyzer()