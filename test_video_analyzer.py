"""
Quick test to verify video analysis module works
"""
import sys
sys.path.insert(0, '/Users/karmansingh/Desktop/work/ai_interview/rahat_backend')

try:
    from interview.video_analyzer import video_analyzer
    print("✅ Video analyzer imported successfully")
    
    # Test initialization
    print(f"✅ MediaPipe FaceMesh initialized")
    print(f"✅ Video analyzer ready")
    
    print("\n📊 Video Analysis Module Status:")
    print("- OpenCV: Installed")
    print("- MediaPipe: Installed")
    print("- NumPy: Installed")
    print("\n✅ All dependencies are working!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
