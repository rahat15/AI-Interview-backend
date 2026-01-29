#!/usr/bin/env python3
"""
Quick test script to verify voice analyzer functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from interview.voice_analyzer import VoiceAnalyzer
import numpy as np
import soundfile as sf
import io

def create_test_audio():
    """Create a simple test audio signal"""
    # Generate 3 seconds of sine wave at 440Hz (A4 note)
    sample_rate = 16000
    duration = 3.0
    frequency = 440.0
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Add some variation to make it more realistic
    audio = np.sin(2 * np.pi * frequency * t) * 0.5
    audio += np.sin(2 * np.pi * frequency * 1.5 * t) * 0.2  # Add harmonics
    
    # Convert to bytes (WAV format)
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format='WAV')
    return buffer.getvalue()

def test_voice_analyzer():
    print("🎤 Testing Voice Analyzer...")
    
    # Create analyzer
    analyzer = VoiceAnalyzer()
    
    # Test with no audio
    print("\n1. Testing with no audio data:")
    result = analyzer.analyze_voice(audio_data=None)
    print(f"   Result: {result.get('analysis_ok', False)}")
    print(f"   Error: {result.get('error', 'None')}")
    
    # Test with synthetic audio
    print("\n2. Testing with synthetic audio:")
    test_audio = create_test_audio()
    print(f"   Generated audio: {len(test_audio)} bytes")
    
    result = analyzer.analyze_voice(audio_data=test_audio)
    print(f"   Analysis OK: {result.get('analysis_ok', False)}")
    
    if result.get('analysis_ok'):
        voice_scores = result.get('voice_scores', {})
        voice_metrics = result.get('voice_metrics', {})
        
        print(f"   Voice Scores: {voice_scores}")
        print(f"   Voice Metrics: {voice_metrics}")
    else:
        print(f"   Error: {result.get('error', 'Unknown')}")
    
    # Test with empty bytes
    print("\n3. Testing with empty audio bytes:")
    result = analyzer.analyze_voice(audio_data=b"")
    print(f"   Result: {result.get('analysis_ok', False)}")
    print(f"   Error: {result.get('error', 'None')}")

if __name__ == "__main__":
    test_voice_analyzer()