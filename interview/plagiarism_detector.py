"""
Plagiarism Detection Module for Interview Voice Analysis
Detects potential plagiarism in spoken responses using semantic similarity
"""

import logging
from typing import Dict, List, Optional, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

logger = logging.getLogger(__name__)

class PlagiarismDetector:
    """
    Detects plagiarism in interview responses using semantic similarity
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with a lightweight sentence transformer model"""
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded plagiarism detection model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            self.model = None
    
    def detect_plagiarism(self, text: str, reference_texts: List[str] = None) -> Dict[str, Any]:
        """
        Detect plagiarism in the given text
        
        Args:
            text: The text to check for plagiarism
            reference_texts: Optional list of reference texts to compare against
            
        Returns:
            Dict containing plagiarism analysis results
        """
        if not self.model or not text or len(text.strip()) < 10:
            return self._get_default_result()
        
        try:
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Check against common interview responses
            if not reference_texts:
                reference_texts = self._get_common_responses()
            
            # Calculate semantic similarities
            similarities = self._calculate_similarities(cleaned_text, reference_texts)
            
            # Detect repetitive patterns
            repetition_score = self._detect_repetition(cleaned_text)
            
            # Check for generic phrases
            generic_score = self._detect_generic_phrases(cleaned_text)
            
            # Calculate overall plagiarism risk
            max_similarity = max(similarities) if similarities else 0.0
            plagiarism_risk = self._calculate_risk_score(
                max_similarity, repetition_score, generic_score
            )
            
            return {
                "plagiarism_detected": plagiarism_risk > 0.7,
                "risk_score": round(plagiarism_risk, 3),
                "risk_level": self._get_risk_level(plagiarism_risk),
                "max_similarity": round(max_similarity, 3),
                "repetition_score": round(repetition_score, 3),
                "generic_score": round(generic_score, 3),
                "indicators": self._get_risk_indicators(
                    max_similarity, repetition_score, generic_score
                ),
                "analysis_ok": True
            }
            
        except Exception as e:
            logger.exception(f"Plagiarism detection failed: {e}")
            return self._get_default_result()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip().lower())
        # Remove filler words
        filler_words = ['um', 'uh', 'like', 'you know', 'basically', 'actually']
        for filler in filler_words:
            text = re.sub(rf'\b{filler}\b', '', text)
        return text.strip()
    
    def _get_common_responses(self) -> List[str]:
        """Get common interview response templates for comparison"""
        return [
            "I am a passionate software engineer with experience in backend development",
            "I have strong problem-solving skills and work well in teams",
            "I am excited about this opportunity and believe I would be a great fit",
            "My experience includes working with various technologies and frameworks",
            "I enjoy learning new technologies and staying up to date with industry trends",
            "I have worked on several projects that demonstrate my technical abilities",
            "I am a quick learner and adapt well to new environments",
            "I believe my skills and experience make me an ideal candidate",
            "I am passionate about technology and love solving complex problems",
            "I have experience working in agile development environments"
        ]
    
    def _calculate_similarities(self, text: str, reference_texts: List[str]) -> List[float]:
        """Calculate semantic similarities with reference texts"""
        try:
            # Encode the input text and reference texts
            text_embedding = self.model.encode([text])
            reference_embeddings = self.model.encode(reference_texts)
            
            # Calculate cosine similarities
            similarities = cosine_similarity(text_embedding, reference_embeddings)[0]
            return similarities.tolist()
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            return []
    
    def _detect_repetition(self, text: str) -> float:
        """Detect repetitive patterns in text"""
        words = text.split()
        if len(words) < 5:
            return 0.0
        
        # Count word repetitions
        word_counts = {}
        for word in words:
            if len(word) > 3:  # Only count meaningful words
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Calculate repetition score
        total_words = len([w for w in words if len(w) > 3])
        repeated_words = sum(count - 1 for count in word_counts.values() if count > 1)
        
        return repeated_words / max(total_words, 1)
    
    def _detect_generic_phrases(self, text: str) -> float:
        """Detect generic/template phrases"""
        generic_phrases = [
            "passionate about",
            "strong background in",
            "extensive experience",
            "proven track record",
            "excellent communication skills",
            "team player",
            "quick learner",
            "detail oriented",
            "results driven",
            "self motivated"
        ]
        
        found_phrases = sum(1 for phrase in generic_phrases if phrase in text)
        return min(found_phrases / 3.0, 1.0)  # Normalize to 0-1
    
    def _calculate_risk_score(self, similarity: float, repetition: float, generic: float) -> float:
        """Calculate overall plagiarism risk score"""
        # Weighted combination of different factors
        weights = {
            'similarity': 0.5,
            'repetition': 0.3,
            'generic': 0.2
        }
        
        risk_score = (
            similarity * weights['similarity'] +
            repetition * weights['repetition'] +
            generic * weights['generic']
        )
        
        return min(risk_score, 1.0)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to categorical level"""
        if risk_score >= 0.8:
            return "HIGH"
        elif risk_score >= 0.6:
            return "MEDIUM"
        elif risk_score >= 0.3:
            return "LOW"
        else:
            return "NONE"
    
    def _get_risk_indicators(self, similarity: float, repetition: float, generic: float) -> List[str]:
        """Get list of risk indicators based on scores"""
        indicators = []
        
        if similarity > 0.7:
            indicators.append("High semantic similarity to common responses")
        elif similarity > 0.5:
            indicators.append("Moderate similarity to template answers")
        
        if repetition > 0.4:
            indicators.append("Excessive word repetition detected")
        elif repetition > 0.2:
            indicators.append("Some repetitive patterns found")
        
        if generic > 0.6:
            indicators.append("Multiple generic phrases detected")
        elif generic > 0.3:
            indicators.append("Some template phrases found")
        
        if not indicators:
            indicators.append("No significant plagiarism indicators")
        
        return indicators
    
    def _get_default_result(self) -> Dict[str, Any]:
        """Return default result when analysis fails"""
        return {
            "plagiarism_detected": False,
            "risk_score": 0.0,
            "risk_level": "UNKNOWN",
            "max_similarity": 0.0,
            "repetition_score": 0.0,
            "generic_score": 0.0,
            "indicators": ["Analysis unavailable"],
            "analysis_ok": False
        }

# Global instance
plagiarism_detector = PlagiarismDetector()