import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Any, Optional
import tempfile
import os

class VideoAnalyzer:
    """Analyze video for interview behavior and cheating detection"""
    
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
    def analyze_video(self, video_data: bytes) -> Dict[str, Any]:
        """Main analysis function"""
        # Save video temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(video_data)
            video_path = tmp.name
        
        try:
            results = self._process_video(video_path)
            return results
        finally:
            if os.path.exists(video_path):
                os.remove(video_path)
    
    def _process_video(self, video_path: str) -> Dict[str, Any]:
        """Process video and extract metrics"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        # Metrics
        face_detected_frames = 0
        multiple_faces_frames = 0
        looking_away_frames = 0
        blink_count = 0
        head_movements = []
        eye_contact_scores = []
        
        prev_ear = None
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                num_faces = len(results.multi_face_landmarks)
                face_detected_frames += 1
                
                if num_faces > 1:
                    multiple_faces_frames += 1
                
                # Analyze first face
                landmarks = results.multi_face_landmarks[0]
                
                # Eye contact
                eye_score = self._calculate_eye_contact(landmarks)
                eye_contact_scores.append(eye_score)
                
                if eye_score < 0.5:
                    looking_away_frames += 1
                
                # Blink detection
                ear = self._calculate_ear(landmarks)
                if prev_ear and prev_ear > 0.2 and ear < 0.2:
                    blink_count += 1
                prev_ear = ear
                
                # Head movement
                head_pose = self._calculate_head_pose(landmarks)
                head_movements.append(head_pose)
        
        cap.release()
        
        # Calculate metrics
        face_presence = (face_detected_frames / frame_count) * 100 if frame_count > 0 else 0
        multiple_faces_pct = (multiple_faces_frames / frame_count) * 100 if frame_count > 0 else 0
        looking_away_pct = (looking_away_frames / face_detected_frames) * 100 if face_detected_frames > 0 else 0
        avg_eye_contact = np.mean(eye_contact_scores) if eye_contact_scores else 0
        blink_rate = (blink_count / duration) * 60 if duration > 0 else 0
        
        # Head movement analysis
        head_stability = self._analyze_head_stability(head_movements)
        
        # Cheating detection
        cheating_indicators = self._detect_cheating(
            multiple_faces_pct, looking_away_pct, head_stability, face_presence
        )
        
        return {
            "duration_seconds": round(duration, 2),
            "total_frames": frame_count,
            "fps": round(fps, 2),
            "face_metrics": {
                "face_presence_percentage": round(face_presence, 2),
                "multiple_faces_detected_percentage": round(multiple_faces_pct, 2),
                "face_detected_frames": face_detected_frames
            },
            "eye_contact": {
                "average_score": round(avg_eye_contact, 2),
                "looking_away_percentage": round(looking_away_pct, 2),
                "rating": self._rate_eye_contact(avg_eye_contact)
            },
            "blink_analysis": {
                "total_blinks": blink_count,
                "blinks_per_minute": round(blink_rate, 2),
                "rating": self._rate_blink_rate(blink_rate)
            },
            "head_movement": {
                "stability_score": round(head_stability, 2),
                "rating": self._rate_head_stability(head_stability)
            },
            "cheating_detection": cheating_indicators,
            "overall_behavior_score": self._calculate_overall_score(
                avg_eye_contact, head_stability, face_presence, cheating_indicators
            )
        }
    
    def _calculate_eye_contact(self, landmarks) -> float:
        """Calculate eye contact score based on iris position"""
        # Left eye iris (468-473) and right eye iris (473-478)
        left_iris = landmarks.landmark[468]
        right_iris = landmarks.landmark[473]
        
        # Eye corners for reference
        left_eye_left = landmarks.landmark[33]
        left_eye_right = landmarks.landmark[133]
        right_eye_left = landmarks.landmark[362]
        right_eye_right = landmarks.landmark[263]
        
        # Calculate iris center position relative to eye
        left_center = (left_iris.x - left_eye_left.x) / (left_eye_right.x - left_eye_left.x)
        right_center = (right_iris.x - right_eye_left.x) / (right_eye_right.x - right_eye_left.x)
        
        # Score: 1.0 = looking straight, 0.0 = looking away
        left_score = 1.0 - abs(left_center - 0.5) * 2
        right_score = 1.0 - abs(right_center - 0.5) * 2
        
        return (left_score + right_score) / 2
    
    def _calculate_ear(self, landmarks) -> float:
        """Calculate Eye Aspect Ratio for blink detection"""
        # Left eye landmarks
        left_eye = [landmarks.landmark[i] for i in [33, 160, 158, 133, 153, 144]]
        
        # Vertical distances
        v1 = np.linalg.norm(np.array([left_eye[1].x, left_eye[1].y]) - 
                           np.array([left_eye[5].x, left_eye[5].y]))
        v2 = np.linalg.norm(np.array([left_eye[2].x, left_eye[2].y]) - 
                           np.array([left_eye[4].x, left_eye[4].y]))
        
        # Horizontal distance
        h = np.linalg.norm(np.array([left_eye[0].x, left_eye[0].y]) - 
                          np.array([left_eye[3].x, left_eye[3].y]))
        
        ear = (v1 + v2) / (2.0 * h) if h > 0 else 0
        return ear
    
    def _calculate_head_pose(self, landmarks) -> Dict[str, float]:
        """Calculate head pose angles"""
        # Key points for head pose
        nose = landmarks.landmark[1]
        left_eye = landmarks.landmark[33]
        right_eye = landmarks.landmark[263]
        
        # Simple yaw calculation (left-right rotation)
        eye_center_x = (left_eye.x + right_eye.x) / 2
        yaw = (nose.x - eye_center_x) * 100  # Normalized
        
        # Simple pitch calculation (up-down rotation)
        pitch = (nose.y - ((left_eye.y + right_eye.y) / 2)) * 100
        
        return {"yaw": yaw, "pitch": pitch}
    
    def _analyze_head_stability(self, head_movements: List[Dict]) -> float:
        """Analyze head movement stability"""
        if len(head_movements) < 2:
            return 1.0
        
        yaws = [m["yaw"] for m in head_movements]
        pitches = [m["pitch"] for m in head_movements]
        
        yaw_std = np.std(yaws)
        pitch_std = np.std(pitches)
        
        # Lower std = more stable (score closer to 1.0)
        stability = 1.0 / (1.0 + (yaw_std + pitch_std) / 20)
        return min(1.0, max(0.0, stability))
    
    def _detect_cheating(self, multiple_faces_pct: float, looking_away_pct: float, 
                        head_stability: float, face_presence: float) -> Dict[str, Any]:
        """Detect potential cheating indicators"""
        indicators = []
        risk_score = 0
        
        # Multiple faces detected
        if multiple_faces_pct > 5:
            indicators.append("Multiple faces detected frequently")
            risk_score += 30
        
        # Looking away too much
        if looking_away_pct > 40:
            indicators.append("Excessive looking away from camera")
            risk_score += 25
        
        # Unstable head movement (reading from screen)
        if head_stability < 0.4:
            indicators.append("Unusual head movement patterns")
            risk_score += 20
        
        # Face not visible enough
        if face_presence < 70:
            indicators.append("Face not consistently visible")
            risk_score += 15
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        elif risk_score >= 15:
            risk_level = "LOW"
        else:
            risk_level = "NONE"
        
        return {
            "risk_level": risk_level,
            "risk_score": min(100, risk_score),
            "indicators": indicators,
            "is_suspicious": risk_score >= 30
        }
    
    def _rate_eye_contact(self, score: float) -> str:
        if score >= 0.7: return "Excellent"
        if score >= 0.5: return "Good"
        if score >= 0.3: return "Fair"
        return "Poor"
    
    def _rate_blink_rate(self, rate: float) -> str:
        # Normal: 15-20 blinks/min
        if 12 <= rate <= 25: return "Normal"
        if rate < 12: return "Low (possible stress)"
        return "High (possible nervousness)"
    
    def _rate_head_stability(self, score: float) -> str:
        if score >= 0.7: return "Stable"
        if score >= 0.5: return "Moderate"
        return "Unstable"
    
    def _calculate_overall_score(self, eye_contact: float, head_stability: float,
                                 face_presence: float, cheating: Dict) -> Dict[str, Any]:
        """Calculate overall behavior score"""
        # Weighted scoring
        base_score = (
            eye_contact * 0.3 +
            head_stability * 0.3 +
            (face_presence / 100) * 0.2
        )
        
        # Penalty for cheating indicators
        cheating_penalty = cheating["risk_score"] / 100 * 0.2
        
        final_score = max(0, (base_score - cheating_penalty) * 100)
        
        return {
            "score": round(final_score, 2),
            "rating": self._get_score_rating(final_score),
            "confidence": "High" if face_presence > 80 else "Medium" if face_presence > 60 else "Low"
        }
    
    def _get_score_rating(self, score: float) -> str:
        if score >= 80: return "Excellent"
        if score >= 60: return "Good"
        if score >= 40: return "Fair"
        return "Poor"


# Global instance
video_analyzer = VideoAnalyzer()
