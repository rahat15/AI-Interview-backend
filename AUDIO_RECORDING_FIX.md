# Audio Recording Issue - Troubleshooting Guide

## Problem

The audio file is being sent to the backend but contains **no audio data** or is **empty**.

### Error Message
```
WARNING:interview.speech_to_text:No audio data received for transcription
🎤 TRANSCRIPTION - Text: 'None'
Speech recognition failed: No audio detected
```

## Root Cause

The **frontend is not properly recording audio** from the microphone. The file is created but has no actual audio content.

## Frontend Issues to Check

### 1. MediaRecorder Not Recording Audio

**Problem**: Video recorder might not be capturing audio track

**Solution**:
```javascript
// ❌ WRONG - May not capture audio
const stream = await navigator.mediaDevices.getUserMedia({ video: true });

// ✅ CORRECT - Explicitly request audio
const stream = await navigator.mediaDevices.getUserMedia({ 
  video: true, 
  audio: true  // ← Must be true!
});

// Verify audio tracks exist
console.log('Audio tracks:', stream.getAudioTracks().length);
if (stream.getAudioTracks().length === 0) {
  throw new Error('No audio track available');
}
```

### 2. Separate Audio Recording

**Problem**: Video file doesn't include audio, or audio extraction fails

**Solution**: Record audio separately
```javascript
// Get media stream with audio
const stream = await navigator.mediaDevices.getUserMedia({
  video: true,
  audio: {
    echoCancellation: true,
    noiseSuppression: true,
    sampleRate: 44100
  }
});

// Create VIDEO recorder
const videoRecorder = new MediaRecorder(stream, {
  mimeType: 'video/webm;codecs=vp9'
});

// Create AUDIO recorder (separate)
const audioStream = new MediaStream(stream.getAudioTracks());
const audioRecorder = new MediaRecorder(audioStream, {
  mimeType: 'audio/webm;codecs=opus'
});

// Start both
videoRecorder.start();
audioRecorder.start();

// Collect data
const videoChunks = [];
const audioChunks = [];

videoRecorder.ondataavailable = (e) => videoChunks.push(e.data);
audioRecorder.ondataavailable = (e) => audioChunks.push(e.data);

// Stop both
videoRecorder.stop();
audioRecorder.stop();

// Create blobs
const videoBlob = new Blob(videoChunks, { type: 'video/webm' });
const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

// Send both to backend
const formData = new FormData();
formData.append('user_id', userId);
formData.append('session_id', sessionId);
formData.append('video_file', videoBlob, 'answer.webm');
formData.append('audio_file', audioBlob, 'answer_audio.webm');

await fetch('/interview/answer', {
  method: 'POST',
  body: formData
});
```

### 3. Check Audio Permissions

**Problem**: Microphone permission not granted

**Solution**:
```javascript
// Check permissions before recording
const checkAudioPermission = async () => {
  try {
    const result = await navigator.permissions.query({ name: 'microphone' });
    
    if (result.state === 'denied') {
      alert('Microphone permission denied. Please enable it in browser settings.');
      return false;
    }
    
    if (result.state === 'prompt') {
      // Will prompt user
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
    }
    
    return true;
  } catch (error) {
    console.error('Permission check failed:', error);
    return false;
  }
};

// Use before starting interview
if (await checkAudioPermission()) {
  startRecording();
}
```

### 4. Verify Audio Data Before Sending

**Problem**: Sending empty blob

**Solution**:
```javascript
// Check blob size before sending
if (audioBlob.size < 1000) {
  console.error('Audio blob too small:', audioBlob.size, 'bytes');
  alert('Audio recording failed. Please try again.');
  return;
}

console.log('Audio blob size:', audioBlob.size, 'bytes');
console.log('Video blob size:', videoBlob.size, 'bytes');

// Verify audio is not silent
const audioContext = new AudioContext();
const arrayBuffer = await audioBlob.arrayBuffer();
try {
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
  console.log('Audio duration:', audioBuffer.duration, 'seconds');
  console.log('Audio channels:', audioBuffer.numberOfChannels);
  
  if (audioBuffer.duration < 0.5) {
    alert('Audio too short. Please speak for at least 1 second.');
    return;
  }
} catch (error) {
  console.error('Invalid audio data:', error);
  alert('Audio recording is corrupted. Please try again.');
  return;
}
```

### 5. Browser Compatibility

**Problem**: Some browsers don't support certain codecs

**Solution**:
```javascript
// Check supported MIME types
const getSupportedMimeType = () => {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
    'audio/wav'
  ];
  
  for (const type of types) {
    if (MediaRecorder.isTypeSupported(type)) {
      console.log('Using audio MIME type:', type);
      return type;
    }
  }
  
  return ''; // Use default
};

const audioRecorder = new MediaRecorder(audioStream, {
  mimeType: getSupportedMimeType()
});
```

## Complete Working Example

```javascript
class InterviewRecorder {
  constructor() {
    this.stream = null;
    this.videoRecorder = null;
    this.audioRecorder = null;
    this.videoChunks = [];
    this.audioChunks = [];
  }

  async start() {
    // Request permissions
    this.stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 44100
      }
    });

    // Verify audio track
    if (this.stream.getAudioTracks().length === 0) {
      throw new Error('No audio track available');
    }

    console.log('✅ Audio tracks:', this.stream.getAudioTracks().length);
    console.log('✅ Video tracks:', this.stream.getVideoTracks().length);

    // Setup video recorder
    this.videoRecorder = new MediaRecorder(this.stream, {
      mimeType: 'video/webm;codecs=vp9'
    });

    // Setup audio recorder (separate)
    const audioStream = new MediaStream(this.stream.getAudioTracks());
    this.audioRecorder = new MediaRecorder(audioStream, {
      mimeType: 'audio/webm;codecs=opus'
    });

    // Collect video data
    this.videoRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this.videoChunks.push(e.data);
      }
    };

    // Collect audio data
    this.audioRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this.audioChunks.push(e.data);
      }
    };

    // Start recording
    this.videoRecorder.start(100); // Collect data every 100ms
    this.audioRecorder.start(100);

    console.log('🎬 Recording started');
  }

  async stop() {
    return new Promise((resolve) => {
      let videoStopped = false;
      let audioStopped = false;

      const checkBothStopped = () => {
        if (videoStopped && audioStopped) {
          // Create blobs
          const videoBlob = new Blob(this.videoChunks, { type: 'video/webm' });
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });

          console.log('📹 Video size:', videoBlob.size, 'bytes');
          console.log('🎤 Audio size:', audioBlob.size, 'bytes');

          // Validate
          if (audioBlob.size < 1000) {
            throw new Error('Audio recording failed - file too small');
          }

          // Stop stream
          this.stream.getTracks().forEach(track => track.stop());

          resolve({ videoBlob, audioBlob });
        }
      };

      this.videoRecorder.onstop = () => {
        videoStopped = true;
        checkBothStopped();
      };

      this.audioRecorder.onstop = () => {
        audioStopped = true;
        checkBothStopped();
      };

      this.videoRecorder.stop();
      this.audioRecorder.stop();
    });
  }

  async submit(userId, sessionId) {
    const { videoBlob, audioBlob } = await this.stop();

    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('session_id', sessionId);
    formData.append('video_file', videoBlob, 'answer.webm');
    formData.append('audio_file', audioBlob, 'answer.webm');

    const response = await fetch('http://localhost:8000/interview/answer', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.error || 'Submission failed');
    }

    return await response.json();
  }
}

// Usage
const recorder = new InterviewRecorder();

// Start recording
await recorder.start();

// ... user answers question ...

// Submit answer
const result = await recorder.submit(userId, sessionId);
console.log('✅ Answer submitted:', result);
```

## Testing Audio Recording

### Test 1: Check Microphone Access
```javascript
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    console.log('✅ Microphone access granted');
    console.log('Audio tracks:', stream.getAudioTracks());
    stream.getTracks().forEach(track => track.stop());
  })
  .catch(error => {
    console.error('❌ Microphone access denied:', error);
  });
```

### Test 2: Record and Play Back
```javascript
// Record 3 seconds of audio
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream);
const chunks = [];

recorder.ondataavailable = (e) => chunks.push(e.data);
recorder.onstop = () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  console.log('Recorded audio size:', blob.size);
  
  // Play back
  const audio = new Audio(URL.createObjectURL(blob));
  audio.play();
};

recorder.start();
setTimeout(() => recorder.stop(), 3000);
```

### Test 3: Send to Backend
```javascript
// Test audio upload
const testAudio = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const recorder = new MediaRecorder(stream);
  const chunks = [];

  recorder.ondataavailable = (e) => chunks.push(e.data);
  recorder.onstop = async () => {
    const blob = new Blob(chunks, { type: 'audio/webm' });
    
    const formData = new FormData();
    formData.append('audio_file', blob, 'test.webm');
    
    const response = await fetch('http://localhost:8000/v1/audio/analyze', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    console.log('Backend response:', result);
  };

  recorder.start();
  setTimeout(() => {
    recorder.stop();
    stream.getTracks().forEach(track => track.stop());
  }, 3000);
};

testAudio();
```

## Backend Improvements

The backend now provides better error messages:

- `"No audio detected"` - Audio file is empty
- `"Audio file is empty or corrupted"` - File too small (<100 bytes)
- `"Could not understand audio"` - Transcription returned empty
- `"Speech recognition service unavailable"` - Groq API error

## Summary

**The issue is in the frontend audio recording, not the backend.**

### Quick Checklist:
- [ ] Microphone permission granted
- [ ] Audio track included in MediaStream
- [ ] Separate audio recorder created
- [ ] Audio blob size > 1000 bytes
- [ ] Audio duration > 0.5 seconds
- [ ] Both audio and video files sent to backend

### Expected Behavior:
```
✅ Audio tracks: 1
✅ Video tracks: 1
📹 Video size: 245678 bytes
🎤 Audio size: 45678 bytes
✅ Transcription successful: I have been working as a developer...
```

Fix the frontend audio recording and the system will work perfectly!
