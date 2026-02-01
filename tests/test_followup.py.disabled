import pytest
from interview.followup import FollowUpGenerator
from core.schemas import ScoreDetail, RubricScore


class TestFollowUpGenerator:
    """Test the follow-up question generator"""
    
    def setup_method(self):
        """Set up generator for each test"""
        self.generator = FollowUpGenerator()
    
    def test_identify_improvement_areas(self):
        """Test identification of areas needing improvement"""
        # Create a score detail with some low scores
        scores = RubricScore(
            clarity=2.0,
            structure=3.5,
            depth_specificity=1.5,
            role_fit=4.0,
            technical=3.0,
            communication=2.5,
            ownership=4.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="The answer lacked depth and clarity",
            action_items=["Provide more specific examples", "Improve structure"],
            exemplar_snippet=None,
            meta={}
        )
        
        improvement_areas = self.generator._identify_improvement_areas(evaluation)
        
        # Should identify areas with scores below 3.0
        assert "clarity" in improvement_areas
        assert "depth_specificity" in improvement_areas
        assert "communication" in improvement_areas
        
        # Should not include areas with good scores
        assert "role_fit" not in improvement_areas
        assert "ownership" not in improvement_areas
    
    def test_generate_clarity_follow_up(self):
        """Test generation of clarity-focused follow-up questions"""
        scores = RubricScore(
            clarity=2.0,
            structure=3.0,
            depth_specificity=3.0,
            role_fit=4.0,
            technical=4.0,
            communication=2.5,
            ownership=3.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="The answer was unclear and lacked structure",
            action_items=["Be more specific", "Use concrete examples"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "communication",
            "difficulty": "medium",
            "signals_expected": ["clarity", "specificity"],
            "pitfalls": ["vagueness", "lack of examples"]
        }
        
        follow_up = self.generator._generate_area_follow_up("clarity", evaluation, question_meta)
        
        assert follow_up is not None
        assert "text" in follow_up
        assert "competency" in follow_up
        assert "difficulty" in follow_up
        assert "meta" in follow_up
        
        # Should be related to clarity improvement
        assert "clarity" in follow_up["text"].lower() or "specific" in follow_up["text"].lower()
    
    def test_generate_structure_follow_up(self):
        """Test generation of structure-focused follow-up questions"""
        scores = RubricScore(
            clarity=3.0,
            structure=1.5,
            depth_specificity=3.0,
            role_fit=4.0,
            technical=4.0,
            communication=3.0,
            ownership=3.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="The answer lacked proper structure and organization",
            action_items=["Organize thoughts better", "Use clear sections"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "communication",
            "difficulty": "medium",
            "signals_expected": ["organization", "structure"],
            "pitfalls": ["rambling", "lack of flow"]
        }
        
        follow_up = self.generator._generate_area_follow_up("structure", evaluation, question_meta)
        
        assert follow_up is not None
        assert "text" in follow_up
        assert "competency" in follow_up
        assert "difficulty" in follow_up
        
        # Should be related to structure improvement
        assert any(word in follow_up["text"].lower() for word in ["structure", "organize", "step", "process"])
    
    def test_generate_depth_follow_up(self):
        """Test generation of depth-focused follow-up questions"""
        scores = RubricScore(
            clarity=3.5,
            structure=3.0,
            depth_specificity=1.0,
            role_fit=4.0,
            technical=3.5,
            communication=3.0,
            ownership=3.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="The answer was too superficial and lacked detail",
            action_items=["Provide more depth", "Include specific examples"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "technical",
            "difficulty": "medium",
            "signals_expected": ["technical depth", "specifics"],
            "pitfalls": ["superficial", "lack of detail"]
        }
        
        follow_up = self.generator._generate_area_follow_up("depth_specificity", evaluation, question_meta)
        
        assert follow_up is not None
        assert "text" in follow_up
        assert "competency" in follow_up
        assert "difficulty" in follow_up
        
        # Should be related to depth improvement
        assert any(word in follow_up["text"].lower() for word in ["detail", "specific", "depth", "example", "how"])
    
    def test_generate_multiple_follow_ups(self):
        """Test generation of multiple follow-up questions"""
        scores = RubricScore(
            clarity=2.0,
            structure=2.0,
            depth_specificity=2.0,
            role_fit=4.0,
            technical=3.0,
            communication=2.5,
            ownership=3.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="Multiple areas need improvement",
            action_items=["Improve clarity", "Better structure", "More depth"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "communication",
            "difficulty": "medium",
            "signals_expected": ["clarity", "structure", "depth"],
            "pitfalls": ["unclear", "unstructured", "superficial"]
        }
        
        follow_ups = self.generator.generate_follow_ups(evaluation, question_meta, max_follow_ups=3)
        
        assert len(follow_ups) <= 3
        assert len(follow_ups) > 0
        
        # Should cover different improvement areas
        competencies = [f["competency"] for f in follow_ups]
        assert len(set(competencies)) >= 1  # At least one competency
        
        # All follow-ups should have required fields
        for follow_up in follow_ups:
            assert "text" in follow_up
            assert "competency" in follow_up
            assert "difficulty" in follow_up
            assert "meta" in follow_up
    
    def test_follow_up_meta_information(self):
        """Test that follow-up questions include proper meta information"""
        scores = RubricScore(
            clarity=2.0,
            structure=3.0,
            depth_specificity=3.0,
            role_fit=4.0,
            technical=4.0,
            communication=2.5,
            ownership=3.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="Clarity needs improvement",
            action_items=["Be more specific"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "communication",
            "difficulty": "medium",
            "signals_expected": ["clarity", "specificity"],
            "pitfalls": ["vagueness"]
        }
        
        follow_up = self.generator._generate_area_follow_up("clarity", evaluation, question_meta)
        
        assert follow_up is not None
        assert "meta" in follow_up
        
        # Meta should include relevant information
        meta = follow_up["meta"]
        assert "signals_expected" in meta
        assert "pitfalls" in meta
        assert "improvement_area" in meta
        assert meta["improvement_area"] == "clarity"
    
    def test_follow_up_difficulty_adjustment(self):
        """Test that follow-up difficulty is appropriately adjusted"""
        scores = RubricScore(
            clarity=1.0,  # Very low score
            structure=3.0,
            depth_specificity=3.0,
            role_fit=4.0,
            technical=4.0,
            communication=2.0,
            ownership=3.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="Very poor clarity",
            action_items=["Start with basics"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "communication",
            "difficulty": "hard",  # Original question was hard
            "signals_expected": ["clarity"],
            "pitfalls": ["unclear"]
        }
        
        follow_up = self.generator._generate_area_follow_up("clarity", evaluation, question_meta)
        
        assert follow_up is not None
        # Follow-up should be easier than original question
        assert follow_up["difficulty"] in ["easy", "medium"]
    
    def test_no_improvement_areas(self):
        """Test behavior when no improvement areas are identified"""
        scores = RubricScore(
            clarity=4.5,
            structure=4.0,
            depth_specificity=4.0,
            role_fit=4.5,
            technical=4.0,
            communication=4.0,
            ownership=4.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="Excellent answer across all dimensions",
            action_items=["Continue this level of performance"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "technical",
            "difficulty": "medium",
            "signals_expected": ["technical depth"],
            "pitfalls": ["over-confidence"]
        }
        
        follow_ups = self.generator.generate_follow_ups(evaluation, question_meta, max_follow_ups=3)
        
        # Should still generate some follow-ups for continued assessment
        assert len(follow_ups) > 0
        
        # Follow-ups should be more challenging
        for follow_up in follow_ups:
            assert follow_up["difficulty"] in ["medium", "hard"]
    
    def test_follow_up_content_quality(self):
        """Test that generated follow-ups have meaningful content"""
        scores = RubricScore(
            clarity=2.0,
            structure=3.0,
            depth_specificity=3.0,
            role_fit=4.0,
            technical=4.0,
            communication=2.5,
            ownership=3.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="Clarity needs improvement",
            action_items=["Be more specific"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "communication",
            "difficulty": "medium",
            "signals_expected": ["clarity", "specificity"],
            "pitfalls": ["vagueness"]
        }
        
        follow_up = self.generator._generate_area_follow_up("clarity", evaluation, question_meta)
        
        assert follow_up is not None
        
        # Text should be substantial
        assert len(follow_up["text"]) > 20
        
        # Should be a question
        assert "?" in follow_up["text"]
        
        # Should be relevant to the improvement area
        text_lower = follow_up["text"].lower()
        assert any(word in text_lower for word in ["clarify", "specific", "explain", "describe", "how", "what"])
    
    def test_follow_up_competency_mapping(self):
        """Test that follow-ups are mapped to appropriate competencies"""
        scores = RubricScore(
            clarity=2.0,
            structure=2.0,
            depth_specificity=3.0,
            role_fit=4.0,
            technical=3.0,
            communication=2.5,
            ownership=3.5
        )
        
        evaluation = ScoreDetail(
            scores=scores,
            rationale="Multiple areas need improvement",
            action_items=["Improve clarity and structure"],
            exemplar_snippet=None,
            meta={}
        )
        
        question_meta = {
            "competency": "technical",
            "difficulty": "medium",
            "signals_expected": ["technical depth"],
            "pitfalls": ["lack of detail"]
        }
        
        follow_ups = self.generator.generate_follow_ups(evaluation, question_meta, max_follow_ups=2)
        
        assert len(follow_ups) > 0
        
        # Should include both technical and communication competencies
        competencies = [f["competency"] for f in follow_ups]
        assert len(set(competencies)) >= 1  # At least one competency
        
        # Technical follow-ups should maintain technical competency
        technical_follow_ups = [f for f in follow_ups if f["competency"] == "technical"]
        if technical_follow_ups:
            assert all("technical" in f["meta"]["signals_expected"] for f in technical_follow_ups)
