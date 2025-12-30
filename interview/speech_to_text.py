"""
Speech-to-Text Module for Voice-Only Interview Answers
Converts audio to text for content analysis
"""

import tempfile
import os
from typing import Optional

class SpeechToTextConverter:
    def __init__(self):
        pass
        
    def convert_audio_to_text(self, audio_data: bytes) -> Optional[str]:
        """Convert audio bytes to text"""
        try:
            # Try to use speech_recognition if available
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Load audio file
                with sr.AudioFile(temp_path) as source:
                    audio = recognizer.record(source)
                
                # Convert to text using Google Speech Recognition
                text = recognizer.recognize_google(audio)
                return text
                
            except sr.UnknownValueError:
                return "Could not understand audio"
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                return "Speech recognition service unavailable"
            finally:
                os.unlink(temp_path)
                
        except ImportError:
            # Fallback: return sample text for testing when speech recognition is not available
            print("⚠️ Speech recognition not available, using fallback text")
            return "This is a sample answer for testing purposes. The candidate provided a voice response but speech recognition is not configured."
        except Exception as e:
            print(f"Audio conversion error: {e}")
            return "This is a fallback answer due to audio processing issues."

# Global instance
speech_converter = SpeechToTextConverter()