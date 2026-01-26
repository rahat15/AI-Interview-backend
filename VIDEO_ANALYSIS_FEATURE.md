# Video Analysis & Cheating Detection

## Overview

The AI Interview Coach now supports video analysis with advanced cheating detection using OpenCV and MediaPipe. This feature analyzes candidate behavior during interviews to ensure integrity and provide behavioral insights.

## Features

### 🎥 Video Analysis
- **Face Detection**: Tracks face presence throughout the interview
- **Eye Contact Tracking**: Monitors where the candidate is looking
- **Blink Detection**: Analyzes blink rate for stress/nervousness indicators
- **Head Movement**: Tracks head stability and unusual movements
- **Multiple Face Detection**: Identifies if others are present

### 🚨 Cheating Detection
- **Multiple Faces**: Detects if someone else is helping
- **Looking Away**: Identifies excessive off-camera gazing (reading answers)
- **Head Movement Patterns**: Detects unusual head movements (reading from screen)
- **Face Visibility**: Ensures candidate remains visible

## Technology Stack

- **OpenCV (`opencv-python`)**: Video processing and frame extraction
- **MediaPipe FaceMesh**: Face landmark detection and tracking
- **NumPy**: Mathematical calculations and analysis

## API Endpoints

### 1. Submit Audio/Video Answer (Session-based)

**Endpoint**: `POST /v1/audio/{session_id}/answer`

**Description**: Submit audio and/or video answer for interview question with full analysis.

**Request**:
```bash
curl -X POST "http://localhost:8000/v1/audio/{session_id}/answer" \
  -F "question_id=q123" \
  -F "audio_file=@answer.mp3" \
  -F "video_file=@answer.mp4"
```

**Form Data**:
- `question_id` (required): Question identifier
- `audio_file` (optional): Audio file (MP3, WAV, etc.)
- `video_file` (optional): Video file (MP4, AVI, etc.)

**Response**:
```json
{
  "evaluation": {
    "score": 8.5,
    "feedback": "Strong technical answer..."
  },
  "technical": {...},
  "communication": {...},
  "voice_analysis": {
    "pitch": {...},
    "energy": {...},
    "speaking_rate": {...}
  },
  "video_analysis": {
    "duration_seconds": 45.2,
    "face_metrics": {
      "face_presence_percentage": 98.5,
      "multiple_faces_detected_percentage": 0.0
    },
    "eye_contact": {
      "average_score": 0.82,
      "looking_away_percentage": 12.3,
      "rating": "Excellent"
    },
    "blink_analysis": {
      "total_blinks": 15,
      "blinks_per_minute": 19.9,
      "rating": "Normal"
    },
    "head_movement": {
      "stability_score": 0.78,
      "rating": "Stable"
    },
    "cheating_detection": {
      "risk_level": "NONE",
      "risk_score": 5,
      "indicators": [],
      "is_suspicious": false
    },
    "overall_behavior_score": {
      "score": 85.4,
      "rating": "Excellent",
      "confidence": "High"
    }
  },
  "next_question": "Tell me about a time...",
  "state": {...}
}
```

### 2. Analyze Audio/Video Only (No Session)

**Endpoint**: `POST /v1/audio/analyze`

**Description**: Analyze audio/video without session context for testing.

**Request**:
```bash
curl -X POST "http://localhost:8000/v1/audio/analyze" \
  -F "audio_file=@test.mp3" \
  -F "video_file=@test.mp4"
```

**Response**:
```json
{
  "transcribed_text": "My answer is...",
  "voice_analysis": {...},
  "video_analysis": {...}
}
```

### 3. Interview Answer (Live Interview)

**Endpoint**: `POST /v1/interview/answer`

**Description**: Submit answer in live interview flow with video analysis.

**Request**:
```bash
curl -X POST "http://localhost:8000/v1/interview/answer" \
  -F "user_id=user123" \
  -F "session_id=session456" \
  -F "audio_file=@answer.mp3" \
  -F "video_file=@answer.mp4"
```

## Video Analysis Metrics

### Face Metrics
- **Face Presence %**: Percentage of frames where face is detected
- **Multiple Faces %**: Percentage of frames with >1 face detected
- **Threshold**: Face should be visible >70% of the time

### Eye Contact
- **Average Score**: 0.0-1.0 (1.0 = perfect eye contact)
- **Looking Away %**: Percentage of time looking away from camera
- **Rating**: Excellent (>0.7), Good (>0.5), Fair (>0.3), Poor (<0.3)

### Blink Analysis
- **Total Blinks**: Count of blinks detected
- **Blinks per Minute**: Normalized blink rate
- **Normal Range**: 12-25 blinks/minute
- **Indicators**: 
  - Low (<12): Possible stress/concentration
  - High (>25): Possible nervousness

### Head Movement
- **Stability Score**: 0.0-1.0 (1.0 = very stable)
- **Tracks**: Yaw (left-right) and Pitch (up-down) movements
- **Rating**: Stable (>0.7), Moderate (>0.5), Unstable (<0.5)

## Cheating Detection

### Risk Levels
- **NONE**: No suspicious behavior (score <15)
- **LOW**: Minor concerns (score 15-29)
- **MEDIUM**: Moderate concerns (score 30-49)
- **HIGH**: Serious concerns (score ≥50)

### Indicators

#### Multiple Faces (30 points)
- **Trigger**: >5% of frames have multiple faces
- **Meaning**: Someone else may be helping

#### Excessive Looking Away (25 points)
- **Trigger**: Looking away >40% of the time
- **Meaning**: May be reading answers from screen/notes

#### Unusual Head Movement (20 points)
- **Trigger**: Head stability score <0.4
- **Meaning**: Frequent head movements suggest reading

#### Poor Face Visibility (15 points)
- **Trigger**: Face visible <70% of time
- **Meaning**: Candidate may be avoiding camera

### Example Cheating Detection Response

```json
{
  "cheating_detection": {
    "risk_level": "MEDIUM",
    "risk_score": 45,
    "indicators": [
      "Excessive looking away from camera",
      "Unusual head movement patterns"
    ],
    "is_suspicious": true
  }
}
```

## Overall Behavior Score

Combines all metrics into a single score (0-100):

**Formula**:
```
base_score = (eye_contact * 0.3) + (head_stability * 0.3) + (face_presence * 0.2)
cheating_penalty = (risk_score / 100) * 0.2
final_score = (base_score - cheating_penalty) * 100
```

**Ratings**:
- **Excellent**: ≥80
- **Good**: 60-79
- **Fair**: 40-59
- **Poor**: <40

## Installation

```bash
# Install required packages
pip install opencv-python==4.10.0.84
pip install mediapipe==0.10.14
pip install numpy>=2.1.0
```

## Usage Examples

### Python Client

```python
import requests

# Submit video answer
with open('answer.mp4', 'rb') as video, open('answer.mp3', 'rb') as audio:
    response = requests.post(
        'http://localhost:8000/v1/audio/session123/answer',
        files={
            'video_file': video,
            'audio_file': audio
        },
        data={'question_id': 'q1'}
    )
    
result = response.json()
print(f"Cheating Risk: {result['video_analysis']['cheating_detection']['risk_level']}")
print(f"Behavior Score: {result['video_analysis']['overall_behavior_score']['score']}")
```

### JavaScript/TypeScript

```javascript
const formData = new FormData();
formData.append('question_id', 'q1');
formData.append('audio_file', audioBlob, 'answer.mp3');
formData.append('video_file', videoBlob, 'answer.mp4');

const response = await fetch('/v1/audio/session123/answer', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Video Analysis:', result.video_analysis);
```

## Best Practices

### For Candidates
1. **Maintain Eye Contact**: Look at the camera, not the screen
2. **Stay Visible**: Keep face in frame throughout
3. **Minimize Movement**: Avoid excessive head movements
4. **Solo Interview**: Ensure no one else is visible

### For Interviewers
1. **Review Metrics**: Check all video analysis metrics
2. **Context Matters**: Consider technical issues (poor lighting, camera quality)
3. **Combine Signals**: Use video analysis with other evaluation criteria
4. **Privacy**: Inform candidates about video analysis

## Limitations

- **Lighting**: Poor lighting affects face detection accuracy
- **Camera Quality**: Low-quality cameras may impact tracking
- **Network**: Large video files require good bandwidth
- **False Positives**: Technical issues may trigger false alerts

## Future Enhancements

- [ ] Audio extraction from video (eliminate need for separate audio file)
- [ ] Real-time streaming analysis
- [ ] Emotion detection
- [ ] Gaze tracking improvements
- [ ] Screen sharing detection
- [ ] Background analysis
- [ ] Multi-camera support

## Troubleshooting

### Face Not Detected
- Ensure good lighting
- Position face in center of frame
- Check camera is working

### High False Positive Rate
- Adjust thresholds in `video_analyzer.py`
- Consider environment factors
- Review video quality

### Performance Issues
- Reduce video resolution
- Limit video duration
- Use async processing

## Support

For issues or questions:
- Check logs for detailed error messages
- Ensure all dependencies are installed
- Verify video file format is supported (MP4, AVI, MOV)
