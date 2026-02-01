#!/usr/bin/env python3
"""
Test script for optimized interview engine
Validates performance improvements
"""

import asyncio
import time
import sys

# Add parent directory to path
sys.path.insert(0, '/Users/karmansingh/Desktop/work/ai_interview/rahat_backend')

from interview.optimized_engine import optimized_engine
from interview.performance import monitor


async def test_session_creation():
    """Test creating a session and generating first question"""
    print("\n" + "="*60)
    print("TEST 1: Session Creation & First Question")
    print("="*60)
    
    sample_cv = """
John Doe
Senior Software Engineer

Experience:
- 5 years Python development
- Expert in FastAPI, Django
- Built microservices at scale
- Led team of 4 engineers

Skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes
    """
    
    sample_jd = """
Senior Backend Engineer

Requirements:
- 5+ years Python experience
- Strong FastAPI knowledge
- Microservices architecture
- Team leadership experience
- Cloud platforms (AWS/GCP)
    """
    
    start = time.time()
    
    try:
        result = await optimized_engine.create_session(
            session_id="test_sess_001",
            user_id="test_user_001",
            role="Senior Backend Engineer",
            company="TechCorp",
            cv_text=sample_cv,
            jd_text=sample_jd
        )
        
        elapsed = time.time() - start
        
        print(f"\n✅ Session created successfully")
        print(f"⏱️  Time taken: {elapsed:.2f}s")
        print(f"📝 First question: {result.get('question')}")
        
        return True, elapsed
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False, 0


async def test_answer_submission():
    """Test submitting an answer and getting next question"""
    print("\n" + "="*60)
    print("TEST 2: Answer Submission & Next Question")
    print("="*60)
    
    sample_answer = """
    I have 5 years of experience working with Python, primarily in backend development. 
    I've built several microservices using FastAPI and deployed them on Kubernetes clusters. 
    At my current company, I lead a team of 4 engineers and we handle millions of requests daily.
    """
    
    start = time.time()
    
    try:
        result = await optimized_engine.submit_answer(
            session_id="test_sess_001",
            answer=sample_answer
        )
        
        elapsed = time.time() - start
        
        print(f"\n✅ Answer submitted successfully")
        print(f"⏱️  Time taken: {elapsed:.2f}s")
        print(f"📝 Next question: {result.get('question')}")
        
        if result.get('evaluation'):
            print(f"📊 Evaluation: {result.get('evaluation')}")
        
        return True, elapsed
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False, 0


async def test_cached_session():
    """Test creating another session with same CV (should be cached)"""
    print("\n" + "="*60)
    print("TEST 3: Cached CV Analysis")
    print("="*60)
    
    sample_cv = """
John Doe
Senior Software Engineer

Experience:
- 5 years Python development
- Expert in FastAPI, Django
- Built microservices at scale
- Led team of 4 engineers

Skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes
    """
    
    sample_jd = """
Senior Backend Engineer

Requirements:
- 5+ years Python experience
- Strong FastAPI knowledge
    """
    
    start = time.time()
    
    try:
        result = await optimized_engine.create_session(
            session_id="test_sess_002",
            user_id="test_user_001",
            role="Senior Backend Engineer",
            company="AnotherCorp",
            cv_text=sample_cv,
            jd_text=sample_jd
        )
        
        elapsed = time.time() - start
        
        print(f"\n✅ Cached session created successfully")
        print(f"⏱️  Time taken: {elapsed:.2f}s (should be faster!)")
        print(f"📝 First question: {result.get('question')}")
        
        return True, elapsed
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False, 0


async def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "🚀"*30)
    print("OPTIMIZED INTERVIEW ENGINE - PERFORMANCE TESTS")
    print("🚀"*30)
    
    results = []
    
    # Test 1: First session (uncached)
    success1, time1 = await test_session_creation()
    results.append(("Session Creation (uncached)", success1, time1))
    
    # Test 2: Answer submission
    if success1:
        await asyncio.sleep(1)  # Small delay
        success2, time2 = await test_answer_submission()
        results.append(("Answer Submission", success2, time2))
    
    # Test 3: Second session (cached CV)
    await asyncio.sleep(1)
    success3, time3 = await test_cached_session()
    results.append(("Session Creation (cached)", success3, time3))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, success, elapsed in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name:30s} {elapsed:6.2f}s")
    
    # Performance metrics
    print("\n" + "="*60)
    print("PERFORMANCE METRICS")
    print("="*60)
    
    stats = monitor.get_stats()
    
    print(f"\n📊 LLM Calls:")
    print(f"   Total: {stats['llm_calls']['total']}")
    print(f"   Avg Duration: {stats['llm_calls']['avg_duration']:.2f}s")
    print(f"   Min/Max: {stats['llm_calls']['min_duration']:.2f}s / {stats['llm_calls']['max_duration']:.2f}s")
    
    print(f"\n📊 Cache Performance:")
    print(f"   Hits: {stats['cache']['hits']}")
    print(f"   Misses: {stats['cache']['misses']}")
    print(f"   Hit Rate: {stats['cache']['hit_rate_percentage']}")
    
    # Performance comparison
    if len(results) >= 3 and results[0][1] and results[2][1]:
        improvement = ((results[0][2] - results[2][2]) / results[0][2]) * 100
        print(f"\n🎯 Performance Improvement:")
        print(f"   First session: {results[0][2]:.2f}s")
        print(f"   Cached session: {results[2][2]:.2f}s")
        print(f"   Improvement: {improvement:.1f}% faster")
    
    print("\n" + "="*60)
    
    # Check if improvements are significant
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        
        # Check performance targets
        if results[2][2] < results[0][2]:
            print("✅ Caching is working - cached session is faster!")
        else:
            print("⚠️  Warning: Cached session not faster. Check cache implementation.")
        
        if stats['cache']['hit_rate'] > 0.3:
            print(f"✅ Good cache hit rate: {stats['cache']['hit_rate_percentage']}")
        else:
            print(f"⚠️  Low cache hit rate: {stats['cache']['hit_rate_percentage']}")
    else:
        print("❌ SOME TESTS FAILED")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
