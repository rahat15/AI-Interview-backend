"""Mock CV Evaluation Engine"""

class CVEvaluationEngine:
    def evaluate(self, cv_text: str, jd_text: str = ""):
        """Evaluate CV against JD"""
        result = {
            "cv_quality": {
                "overall_score": 85.0,
                "band": "Good",
                "subscores": [
                    {
                        "dimension": "Structure & Format",
                        "score": 4.2,
                        "max_score": 5.0,
                        "evidence": ["Clear sections", "Professional formatting", "Good use of whitespace"]
                    },
                    {
                        "dimension": "Content Quality",
                        "score": 4.0,
                        "max_score": 5.0,
                        "evidence": ["Relevant experience", "Quantified achievements", "Clear descriptions"]
                    },
                    {
                        "dimension": "Skills & Keywords",
                        "score": 4.5,
                        "max_score": 5.0,
                        "evidence": ["Technical skills listed", "Industry keywords", "Relevant certifications"]
                    }
                ]
            }
        }
        
        if jd_text:
            result.update({
                "jd_match": {
                    "overall_score": 78.0,
                    "band": "Good",
                    "subscores": [
                        {
                            "dimension": "Skills Match",
                            "score": 4.1,
                            "max_score": 5.0,
                            "evidence": ["80% skill overlap", "Core competencies aligned"]
                        },
                        {
                            "dimension": "Experience Match",
                            "score": 3.8,
                            "max_score": 5.0,
                            "evidence": ["Relevant industry experience", "Similar role responsibilities"]
                        }
                    ]
                },
                "fit_index": {
                    "score": 81.5,
                    "band": "Good",
                    "explanation": "Strong candidate with good alignment to role requirements"
                },
                "key_takeaways": {
                    "strengths": ["Strong technical background", "Relevant experience", "Good presentation"],
                    "gaps": ["Could highlight leadership experience", "Missing some preferred skills"],
                    "recommendations": ["Add more quantified achievements", "Include relevant projects"]
                }
            })
        
        return result