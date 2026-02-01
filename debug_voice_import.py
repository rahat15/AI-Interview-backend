
import sys
import os
import traceback

print(f"Python executable: {sys.executable}")
try:
    print("Attempting to import interview.voice_analyzer...")
    from interview.voice_analyzer import voice_analyzer
    print(f"Successfully imported voice_analyzer: {voice_analyzer}")
except ImportError:
    print("Caught ImportError!")
    traceback.print_exc()
except Exception:
    print("Caught unexpected exception!")
    traceback.print_exc()
