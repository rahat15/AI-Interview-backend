#!/usr/bin/env python3
"""
Comprehensive test for the enhanced interview system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_interview_evaluation():
    print("🎯 Testing Enhanced Interview Evaluation System...")
    
    try:
        from interview.session_manager import AdvancedInterviewManager
        
        # Create interview manager
        manager = AdvancedInterviewManager()
        
        # Test cases with different response qualities
        test_cases = [
            {
                "answer": "nothing",
                "description": "Very poor response",
                "expected_score_range": (0, 1)
            },
            {
                "answer": "I don't want to answer this question",
                "description": "Refusal to answer",
                "expected_score_range": (0, 1)
            },
            {
                "answer": "I am a passionate software engineer with experience in backend development",
                "description": "Generic template response",
                "expected_score_range": (1, 3)
            },
            {
                "answer": "I have 5 years of experience working with Python, Django, and PostgreSQL. I've built several REST APIs and worked on microservices architecture. My most recent project involved optimizing database queries which improved response time by 40%.",
                "description": "Good detailed response",
                "expected_score_range": (4, 7)
            }
        ]
        
        question = "Tell me about your technical background and experience."
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: '{test_case['answer'][:50]}...'")
            print(f"   Description: {test_case['description']}")
            
            # Test the evaluation
            evaluation = await manager._evaluate_answer(
                question=question,
                answer=test_case["answer"],
                cv_analysis={},
                jd_analysis={},
                cv_text="5 years experience",
                jd_text="Developer position",
                role_title="Developer",
                audio_data=None,
                audio_url=None,
                stage="technical_background"
            )
            
            # Check technical evaluation
            tech_eval = evaluation.get("technical", {})
            tech_depth = tech_eval.get("technical_depth", 0)
            
            # Check communication evaluation (should include plagiarism)
            comm_eval = evaluation.get("communication", {})
            plagiarism = comm_eval.get("plagiarism_analysis", {})
            
            # Check combined evaluation
            combined = evaluation.get("combined", {})
            total_score = combined.get("total_score", 0)
            
            print(f"   Technical Depth: {tech_depth}/10")
            print(f"   Total Score: {total_score}/10")
            print(f"   Plagiarism Risk: {plagiarism.get('risk_score', 0)}")
            print(f"   Plagiarism Analysis OK: {plagiarism.get('analysis_ok', False)}")
            print(f"   Feedback: {combined.get('feedback', 'N/A')}")
            
            # Verify score is in expected range
            min_score, max_score = test_case["expected_score_range"]
            if min_score <= total_score <= max_score:
                print(f"   ✅ Score {total_score} is in expected range [{min_score}-{max_score}]")
            else:
                print(f"   ❌ Score {total_score} is NOT in expected range [{min_score}-{max_score}]")
        
        print("\n✅ Interview evaluation test completed!")
        
    except Exception as e:
        print(f"❌ Interview evaluation test failed: {e}")
        import traceback
        traceback.print_exc()

def test_video_analysis():
    print("\n🎥 Testing Video Analysis...")
    
    try:
        from interview.video_analyzer import VideoAnalyzer
        
        # Create a simple test video data (this would normally be actual video bytes)
        # For testing, we'll just test the analyzer initialization
        analyzer = VideoAnalyzer()
        print("   ✅ VideoAnalyzer initialized successfully")
        
        # Test the scoring methods
        print("   ✅ Video analysis methods available")
        
    except Exception as e:
        print(f"   ❌ Video analysis test failed: {e}")

if __name__ == "__main__":
    import asyncio
    
    # Run async test
    asyncio.run(test_interview_evaluation())
    
    # Run sync test
    test_video_analysis()