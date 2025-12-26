# Simple mock evaluation engine to avoid import errors
class MockCVEvaluationEngine:
    def evaluate(self, cv_text: str, jd_text: str = ""):
        return {
            "cv_quality": {
                "overall_score": 85.0,
                "band": "Good",
                "subscores": [
                    {
                        "dimension": "Structure",
                        "score": 4.2,
                        "max_score": 5.0,
                        "evidence": ["Clear sections", "Good formatting"]
                    }
                ]
            },
            "jd_match": {
                "overall_score": 78.0,
                "band": "Good",
                "subscores": []
            } if jd_text else {},
            "fit_index": {
                "score": 81.5,
                "band": "Good"
            } if jd_text else {}
        }

# Create a global instance
evaluation_engine = MockCVEvaluationEngine()