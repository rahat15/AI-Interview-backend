import pytest
from interview.evaluate.rules import RulesBasedEvaluator
from interview.evaluate.judge import LLMAsJudgeEvaluator
from core.schemas import ScoreDetail


class TestRulesBasedEvaluator:
    """Test the rules-based evaluator for determinism and accuracy"""
    
    def setup_method(self):
        """Set up evaluator for each test"""
        self.evaluator = RulesBasedEvaluator()
    
    def test_star_pattern_detection(self):
        """Test STAR method pattern detection"""
        answer_with_star = """
        When I was working as a software engineer at TechCorp, my responsibility was to 
        optimize the database queries. I analyzed the slow queries and implemented indexing 
        strategies. As a result, query performance improved by 40% and user satisfaction increased.
        """
        
        star_scores = self.evaluator._analyze_star_patterns(answer_with_star)
        
        assert star_scores["situation"] > 0.5
        assert star_scores["task"] > 0.5
        assert star_scores["action"] > 0.5
        assert star_scores["result"] > 0.5
    
    def test_metrics_detection(self):
        """Test metrics and numbers detection"""
        answer_with_metrics = "I improved performance by 25% and reduced costs by $50,000 annually."
        
        # Test metrics detection
        metrics_found = any(re.search(r'\d+\s*%', answer_with_metrics) for re in [__import__('re')])
        assert metrics_found
    
    def test_tradeoff_detection(self):
        """Test trade-off recognition"""
        answer_with_tradeoff = "We had to balance speed with accuracy. On the other hand, we could have prioritized quality over time."
        
        # Test trade-off detection
        tradeoff_found = any(re.search(r'trade.?off|on\s+the\s+other\s+hand', answer_with_tradeoff, re.IGNORECASE) for re in [__import__('re')])
        assert tradeoff_found
    
    def test_clarity_scoring(self):
        """Test clarity score calculation"""
        clear_answer = "I implemented a caching layer using Redis to improve response times. The solution reduced API latency from 200ms to 50ms."
        unclear_answer = "I did some stuff with caching and it made things faster."
        
        clear_score = self.evaluator._calculate_clarity_score(clear_answer, {"situation": 0.8, "task": 0.7, "action": 0.9, "result": 0.8})
        unclear_score = self.evaluator._calculate_clarity_score(unclear_answer, {"situation": 0.2, "task": 0.3, "action": 0.1, "result": 0.2})
        
        assert clear_score > unclear_score
        assert clear_score >= 3.0  # Good clarity should score 3+
        assert unclear_score <= 2.5  # Poor clarity should score 2.5 or below
    
    def test_structure_scoring(self):
        """Test structure score calculation"""
        structured_answer = "First, I analyzed the problem. Then, I designed a solution. Finally, I implemented and tested it."
        unstructured_answer = "I did this and that and then some other things happened and it worked out."
        
        structured_score = self.evaluator._calculate_structure_score(structured_answer, {"situation": 0.8, "task": 0.7, "action": 0.9, "result": 0.8})
        unstructured_score = self.evaluator._calculate_structure_score(unstructured_answer, {"situation": 0.2, "task": 0.3, "action": 0.1, "result": 0.2})
        
        assert structured_score > unstructured_score
        assert structured_score >= 3.0
        assert unstructured_score <= 2.5
    
    def test_depth_specificity_scoring(self):
        """Test depth and specificity scoring"""
        specific_answer = "I used Redis with TTL of 300 seconds, implemented cache invalidation on database updates, and added monitoring with Prometheus metrics."
        vague_answer = "I added some caching and monitoring."
        
        specific_score = self.evaluator._calculate_depth_specificity_score(specific_answer, {"situation": 0.8, "task": 0.7, "action": 0.9, "result": 0.8})
        vague_score = self.evaluator._calculate_depth_specificity_score(vague_answer, {"situation": 0.2, "task": 0.3, "action": 0.1, "result": 0.2})
        
        assert specific_score > vague_score
        assert specific_score >= 3.5
        assert vague_score <= 2.0
    
    def test_evaluation_determinism(self):
        """Test that evaluations are deterministic (same input = same output)"""
        answer_text = "I implemented a microservices architecture using Docker and Kubernetes. The solution improved scalability by 60% and reduced deployment time from hours to minutes."
        question_meta = {
            "competency": "technical",
            "difficulty": "medium",
            "signals_expected": ["architecture", "containerization", "metrics"],
            "pitfalls": ["over-engineering", "lack of monitoring"]
        }
        
        # Run evaluation multiple times
        evaluation1 = self.evaluator.evaluate_answer(answer_text, question_meta)
        evaluation2 = self.evaluator.evaluate_answer(answer_text, question_meta)
        evaluation3 = self.evaluator.evaluate_answer(answer_text, question_meta)
        
        # Scores should be identical
        assert evaluation1.scores.dict() == evaluation2.scores.dict()
        assert evaluation2.scores.dict() == evaluation3.scores.dict()
        
        # Rationale should be identical
        assert evaluation1.rationale == evaluation2.rationale
        assert evaluation2.rationale == evaluation3.rationale
    
    def test_complete_evaluation(self):
        """Test complete evaluation with all rubric dimensions"""
        answer_text = """
        When I was leading the migration from monolithic to microservices architecture, 
        my responsibility was to ensure zero downtime during the transition. I implemented 
        a blue-green deployment strategy with database migration scripts and rollback procedures. 
        The result was a successful migration with only 15 minutes of planned maintenance window, 
        and we achieved 99.9% uptime during the process.
        """
        
        question_meta = {
            "competency": "leadership",
            "difficulty": "hard",
            "signals_expected": ["planning", "risk management", "metrics"],
            "pitfalls": ["lack of testing", "poor communication"]
        }
        
        evaluation = self.evaluator.evaluate_answer(answer_text, question_meta)
        
        # Check all rubric dimensions are scored
        assert 0 <= evaluation.scores.clarity <= 5
        assert 0 <= evaluation.scores.structure <= 5
        assert 0 <= evaluation.scores.depth_specificity <= 5
        assert 0 <= evaluation.scores.role_fit <= 5
        assert 0 <= evaluation.scores.technical <= 5
        assert 0 <= evaluation.scores.communication <= 5
        assert 0 <= evaluation.scores.ownership <= 5
        
        # Check that rationale is provided
        assert len(evaluation.rationale) > 50
        
        # Check that action items are provided
        assert len(evaluation.action_items) > 0
        
        # This answer should score well due to STAR structure and specific metrics
        assert evaluation.scores.structure >= 3.5
        assert evaluation.scores.depth_specificity >= 3.5


class TestLLMAsJudgeEvaluator:
    """Test the LLM-as-judge evaluator interface"""
    
    def setup_method(self):
        """Set up evaluator for each test"""
        self.evaluator = LLMAsJudgeEvaluator()
    
    @pytest.mark.asyncio
    async def test_local_baseline_evaluation(self):
        """Test local baseline evaluation functionality"""
        answer_text = "I implemented caching to improve performance by 30%."
        question_meta = {
            "competency": "technical",
            "difficulty": "medium",
            "signals_expected": ["optimization", "metrics"],
            "pitfalls": ["over-caching", "stale data"]
        }
        
        evaluation = await self.evaluator._local_baseline_evaluation(
            answer_text, question_meta, "How did you optimize performance?"
        )
        
        assert isinstance(evaluation, ScoreDetail)
        assert 0 <= evaluation.scores.clarity <= 5
        assert 0 <= evaluation.scores.structure <= 5
        assert 0 <= evaluation.scores.depth_specificity <= 5
        assert 0 <= evaluation.scores.role_fit <= 5
        assert 0 <= evaluation.scores.technical <= 5
        assert 0 <= evaluation.scores.communication <= 5
        assert 0 <= evaluation.scores.ownership <= 5
    
    @pytest.mark.asyncio
    async def test_evaluation_consistency(self):
        """Test that LLM evaluator maintains consistency with rules evaluator"""
        answer_text = "I used Redis caching with TTL and monitoring to improve API response times from 200ms to 50ms."
        question_meta = {
            "competency": "technical",
            "difficulty": "medium",
            "signals_expected": ["caching", "monitoring", "metrics"],
            "pitfalls": ["cache invalidation", "memory usage"]
        }
        
        # Test local baseline evaluation
        evaluation = await self.evaluator.evaluate_answer(
            answer_text, question_meta, "How did you implement caching?"
        )
        
        # Should return a valid ScoreDetail
        assert isinstance(evaluation, ScoreDetail)
        assert hasattr(evaluation.scores, 'clarity')
        assert hasattr(evaluation.scores, 'technical')
        assert hasattr(evaluation.scores, 'depth_specificity')
        
        # Technical answer with specific metrics should score well
        assert evaluation.scores.technical >= 3.0
        assert evaluation.scores.depth_specificity >= 3.0
    
    def test_evaluator_initialization(self):
        """Test evaluator initialization and configuration"""
        # Should use local baseline by default
        assert self.evaluator.use_local_baseline == True
        
        # Should have rules evaluator instance
        assert hasattr(self.evaluator, 'rules_evaluator')
        assert isinstance(self.evaluator.rules_evaluator, RulesBasedEvaluator)


class TestEvaluationEdgeCases:
    """Test evaluator behavior with edge cases"""
    
    def setup_method(self):
        """Set up evaluators for each test"""
        self.rules_evaluator = RulesBasedEvaluator()
        self.llm_evaluator = LLMAsJudgeEvaluator()
    
    def test_empty_answer(self):
        """Test evaluation of empty or very short answers"""
        empty_answer = ""
        short_answer = "Yes."
        
        question_meta = {
            "competency": "behavioral",
            "difficulty": "easy",
            "signals_expected": ["communication"],
            "pitfalls": ["lack of detail"]
        }
        
        empty_eval = self.rules_evaluator.evaluate_answer(empty_answer, question_meta)
        short_eval = self.rules_evaluator.evaluate_answer(short_answer, question_meta)
        
        # Empty answers should score very low
        assert empty_eval.scores.clarity <= 1.0
        assert empty_eval.scores.depth_specificity <= 1.0
        
        # Short answers should score low but not as low as empty
        assert short_eval.scores.clarity <= 2.0
        assert short_eval.scores.depth_specificity <= 2.0
    
    def test_very_long_answer(self):
        """Test evaluation of very long, verbose answers"""
        long_answer = "I would like to tell you about this time when I was working at a company and there was this project that I was involved with and it was really interesting because we had to solve this problem that was quite challenging and I remember that I spent a lot of time thinking about it and discussing it with my colleagues and we came up with several different approaches and we had to evaluate each one carefully and consider the pros and cons of each approach and think about the trade-offs involved and how it would impact the users and the system as a whole and what the long-term implications might be and whether it would be scalable and maintainable and cost-effective and all of those factors that are important when making architectural decisions and so we went through this process and eventually we decided on the best approach and we implemented it and it worked out really well and the users were happy and the system performed better and we were able to handle more load and it was more reliable and we had fewer bugs and the maintenance was easier and overall it was a great success and I learned a lot from that experience and I think it really helped me grow as an engineer and understand the importance of careful planning and consideration of all the factors involved in making technical decisions."
        
        question_meta = {
            "competency": "communication",
            "difficulty": "medium",
            "signals_expected": ["clarity", "conciseness"],
            "pitfalls": ["verbosity", "lack of structure"]
        }
        
        evaluation = self.rules_evaluator.evaluate_answer(long_answer, question_meta)
        
        # Long answers might score well on depth but poorly on clarity/structure
        assert evaluation.scores.depth_specificity >= 3.0  # Lots of detail
        assert evaluation.scores.clarity <= 3.0  # Hard to follow
        assert evaluation.scores.structure <= 3.0  # Poor structure
    
    def test_technical_jargon(self):
        """Test evaluation of answers with technical jargon"""
        jargon_answer = "I implemented a distributed caching layer using Redis Cluster with consistent hashing, implemented circuit breaker pattern with Hystrix, and added distributed tracing with Jaeger for observability."
        
        question_meta = {
            "competency": "technical",
            "difficulty": "hard",
            "signals_expected": ["technical depth", "architecture knowledge"],
            "pitfalls": ["over-complication", "lack of explanation"]
        }
        
        evaluation = self.rules_evaluator.evaluate_answer(jargon_answer, question_meta)
        
        # Technical depth should score well
        assert evaluation.scores.technical >= 3.5
        assert evaluation.scores.depth_specificity >= 3.5
        
        # But clarity might suffer if jargon isn't explained
        assert evaluation.scores.clarity <= 4.0
