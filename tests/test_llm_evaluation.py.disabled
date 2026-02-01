import pytest
import json
from unittest.mock import Mock, patch
from cv_eval.engine import CVEvaluationEngine
from cv_eval.llm_scorer import LLMScorer
from cv_eval.schemas import CVEvaluationRequest, ScoreResult, SubScore


class TestLLMScorer:
    """Test LLM scorer functionality"""
    
    def test_llm_scorer_initialization(self):
        """Test LLM scorer initialization with Groq"""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            scorer = LLMScorer()
            assert scorer.model == "llama3-8b-8192"
    
    def test_llm_scorer_initialization_failure(self):
        """Test LLM scorer initialization failure without API key"""
        with pytest.raises(ValueError, match="GROQ_API_KEY environment variable not set"):
            LLMScorer()
    
    def test_extract_json_from_response(self):
        """Test JSON extraction from LLM response"""
        scorer = LLMScorer()
        
        # Test with markdown code blocks
        response = "Here's the result:\n```json\n{\"test\": \"value\"}\n```\nEnd"
        result = scorer._extract_json_from_response(response)
        assert result == '{"test": "value"}'
        
        # Test with plain JSON
        response = '{"test": "value"}'
        result = scorer._extract_json_from_response(response)
        assert result == '{"test": "value"}'
        
        # Test with extra content
        response = "Some text {\"test\": \"value\"} more text"
        result = scorer._extract_json_from_response(response)
        assert result == '{"test": "value"}'
    
    def test_parse_llm_response(self):
        """Test LLM response parsing"""
        scorer = LLMScorer()
        
        # Valid response
        response = '{"cv_quality": {"overall_score": 85.0, "band": "Strong", "subscores": []}}'
        result = scorer._parse_llm_response(response, "cv_quality")
        assert "cv_quality" in result
        assert result["cv_quality"]["overall_score"] == 85.0
        
        # Invalid JSON
        with pytest.raises(ValueError):
            scorer._parse_llm_response("invalid json", "cv_quality")
        
        # Missing expected key
        with pytest.raises(ValueError):
            scorer._parse_llm_response('{"wrong_key": {}}', "cv_quality")
    
    def test_convert_to_score_result(self):
        """Test conversion of LLM response to ScoreResult"""
        scorer = LLMScorer()
        
        data = {
            "overall_score": 85.0,
            "band": "Strong",
            "subscores": [
                {
                    "dimension": "ats_structure",
                    "score": 8.0,
                    "max_score": 10.0,
                    "evidence": ["email present", "phone present"]
                }
            ]
        }
        
        result = scorer._convert_to_score_result(data)
        assert isinstance(result, ScoreResult)
        assert result.overall_score == 85.0
        assert result.band == "Strong"
        assert len(result.subscores) == 1
        assert result.subscores[0].dimension == "ats_structure"
        assert result.subscores[0].score == 8.0


class TestCVEvaluationEngine:
    """Test CV evaluation engine with LLM integration"""
    
    def test_engine_initialization_with_llm(self):
        """Test engine initialization with LLM enabled"""
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            engine = CVEvaluationEngine(use_llm=True)
            assert engine.use_llm is True
            assert engine.llm_scorer is not None
    
    def test_engine_initialization_without_llm(self):
        """Test engine initialization without LLM"""
        engine = CVEvaluationEngine(use_llm=False)
        assert engine.use_llm is False
        assert engine.llm_scorer is None
    
    def test_engine_initialization_llm_failure(self):
        """Test engine initialization when LLM fails"""
        engine = CVEvaluationEngine(use_llm=True)
        assert engine.use_llm is False  # Should fall back to heuristic
    
    @patch('evaluation.llm_scorer.LLMScorer')
    def test_evaluate_cv_quality_llm_success(self, mock_llm_scorer_class):
        """Test CV quality evaluation with successful LLM call"""
        # Mock LLM scorer
        mock_scorer = Mock()
        mock_scorer.score_cv_quality.return_value = ScoreResult(
            overall_score=85.0,
            band="Strong",
            subscores=[]
        )
        mock_llm_scorer_class.return_value = mock_scorer
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            engine = CVEvaluationEngine(use_llm=True)
            
            cv_text = "Test CV content"
            result = engine.evaluate_cv_quality(cv_text)
            
            assert result.overall_score == 85.0
            assert result.band == "Strong"
            mock_scorer.score_cv_quality.assert_called_once_with(cv_text)
    
    @patch('evaluation.llm_scorer.LLMScorer')
    def test_evaluate_cv_quality_llm_failure_fallback(self, mock_llm_scorer_class):
        """Test CV quality evaluation with LLM failure and heuristic fallback"""
        # Mock LLM scorer to raise exception
        mock_scorer = Mock()
        mock_scorer.score_cv_quality.side_effect = Exception("LLM API error")
        mock_llm_scorer_class.return_value = mock_scorer
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            engine = CVEvaluationEngine(use_llm=True)
            
            cv_text = "JOHN DOE\nSoftware Engineer\njohn.doe@email.com"
            result = engine.evaluate_cv_quality(cv_text)
            
            # Should fall back to heuristic scoring
            assert isinstance(result, ScoreResult)
            assert result.overall_score >= 0
            assert result.band in ["Excellent", "Strong", "Partial", "Weak"]
    
    @patch('evaluation.llm_scorer.LLMScorer')
    def test_evaluate_jd_match_llm_success(self, mock_llm_scorer_class):
        """Test JD match evaluation with successful LLM call"""
        # Mock LLM scorer
        mock_scorer = Mock()
        mock_scorer.score_jd_match.return_value = ScoreResult(
            overall_score=80.0,
            band="Strong",
            subscores=[]
        )
        mock_llm_scorer_class.return_value = mock_scorer
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
            engine = CVEvaluationEngine(use_llm=True)
            
            cv_text = "Test CV content"
            jd_text = "Test JD content"
            result = engine.evaluate_jd_match(cv_text, jd_text, include_constraints=True)
            
            assert result.overall_score == 80.0
            assert result.band == "Strong"
            mock_scorer.score_jd_match.assert_called_once_with(cv_text, jd_text, True)
    
    def test_calculate_fit_index(self):
        """Test fit index calculation"""
        engine = CVEvaluationEngine(use_llm=False)
        
        # Test with constraints included
        fit_index = engine.calculate_fit_index(80.0, 85.0, include_constraints=True)
        expected = 0.6 * 85.0 + 0.4 * 80.0
        assert abs(fit_index - expected) < 1e-6
        
        # Test with constraints excluded
        fit_index = engine.calculate_fit_index(80.0, 85.0, include_constraints=False)
        expected = 0.6 * 85.0 + 0.4 * 80.0
        assert abs(fit_index - expected) < 1e-6
    
    def test_get_score_band(self):
        """Test score band calculation"""
        engine = CVEvaluationEngine(use_llm=False)
        
        assert engine._get_score_band(95.0) == "Excellent"
        assert engine._get_score_band(85.0) == "Strong"
        assert engine._get_score_band(70.0) == "Partial"
        assert engine._get_score_band(50.0) == "Weak"
    
    def test_full_evaluation_workflow(self):
        """Test complete evaluation workflow"""
        engine = CVEvaluationEngine(use_llm=False)  # Use heuristic for testing
        
        request = CVEvaluationRequest(
            cv_text="JOHN DOE\nSoftware Engineer\njohn.doe@email.com",
            jd_text="Senior Software Engineer\nRequirements: Python, AWS",
            include_constraints=True
        )
        
        result = engine.evaluate(request)
        
        assert isinstance(result.cv_quality, ScoreResult)
        assert isinstance(result.jd_match, ScoreResult)
        assert isinstance(result.fit_index, float)
        assert result.fit_index >= 0 and result.fit_index <= 100
        assert result.band in ["Excellent", "Strong", "Partial", "Weak"]
        
        # Verify fit index calculation
        expected_fit_index = 0.6 * result.jd_match.overall_score + 0.4 * result.cv_quality.overall_score
        assert abs(result.fit_index - expected_fit_index) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__])
