#!/usr/bin/env python3
"""
Test plagiarism detection functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_plagiarism_detection():
    print("🔍 Testing Plagiarism Detection...")
    
    try:
        from interview.plagiarism_detector import plagiarism_detector
        
        # Test cases
        test_cases = [
            {
                "text": "I am a passionate software engineer with experience in backend development",
                "expected_risk": "HIGH",
                "description": "Generic template response"
            },
            {
                "text": "nothing",
                "expected_risk": "LOW", 
                "description": "Very short response"
            },
            {
                "text": "I don't want to answer this question",
                "expected_risk": "LOW",
                "description": "Refusal to answer"
            },
            {
                "text": "Fuck off.",
                "expected_risk": "LOW",
                "description": "Inappropriate response"
            },
            {
                "text": "I have worked on several challenging projects including building a microservices architecture using Docker and Kubernetes. One specific example was when I led a team to migrate our monolithic application to a distributed system, which improved our scalability by 300% and reduced deployment time from 2 hours to 15 minutes.",
                "expected_risk": "LOW",
                "description": "Detailed original response"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: '{test_case['text'][:50]}...'")
            print(f"   Description: {test_case['description']}")
            
            result = plagiarism_detector.detect_plagiarism(test_case["text"])
            
            print(f"   Analysis OK: {result.get('analysis_ok', False)}")
            print(f"   Risk Level: {result.get('risk_level', 'UNKNOWN')}")
            print(f"   Risk Score: {result.get('risk_score', 0.0)}")
            print(f"   Plagiarism Detected: {result.get('plagiarism_detected', False)}")
            
            if result.get('indicators'):
                print(f"   Indicators: {result['indicators']}")
        
        print("\n✅ Plagiarism detection test completed!")
        
    except Exception as e:
        print(f"❌ Plagiarism detection test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_plagiarism_detection()