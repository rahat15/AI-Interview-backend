from typing import Dict, List, Any, Optional
from core.schemas import RubricScore, ScoreDetail
from interview.evaluate.rules import RulesBasedEvaluator


class LLMAsJudgeEvaluator:
    """LLM-as-judge evaluation with local baseline fallback"""
    
    def __init__(self):
        self.rules_evaluator = RulesBasedEvaluator()
        self.use_local_baseline = True  # Default to local for offline operation
    
    async def evaluate_answer(
        self, 
        answer_text: str, 
        question_meta: Dict[str, Any],
        question_text: str = ""
    ) -> ScoreDetail:
        """Evaluate an answer using LLM-as-judge or local baseline"""
        if self.use_local_baseline:
            return await self._local_baseline_evaluation(answer_text, question_meta, question_text)
        else:
            return await self._llm_evaluation(answer_text, question_meta, question_text)
    
    async def _local_baseline_evaluation(
        self, 
        answer_text: str, 
        question_meta: Dict[str, Any],
        question_text: str
    ) -> ScoreDetail:
        """Local baseline evaluation using rules and heuristics"""
        # Use rules-based evaluator as baseline
        base_evaluation = self.rules_evaluator.evaluate_answer(answer_text, question_meta)
        
        # Enhance with question-specific analysis
        enhanced_scores = self._enhance_scores_with_context(
            base_evaluation.scores, 
            answer_text, 
            question_text, 
            question_meta
        )
        
        # Generate enhanced rationale
        enhanced_rationale = self._generate_enhanced_rationale(
            base_evaluation, 
            answer_text, 
            question_text, 
            question_meta
        )
        
        # Generate enhanced action items
        enhanced_action_items = self._generate_enhanced_action_items(
            base_evaluation, 
            answer_text, 
            question_text, 
            question_meta
        )
        
        return ScoreDetail(
            scores=enhanced_scores,
            rationale=enhanced_rationale,
            action_items=enhanced_action_items,
            exemplar_snippet=base_evaluation.exemplar_snippet
        )
    
    async def _llm_evaluation(
        self, 
        answer_text: str, 
        question_meta: Dict[str, Any],
        question_text: str
    ) -> ScoreDetail:
        """LLM-based evaluation (placeholder for production)"""
        # TODO: Implement actual LLM evaluation
        # This would use OpenAI, Anthropic, or other LLM providers
        
        # For now, fall back to local baseline
        return await self._local_baseline_evaluation(answer_text, question_meta, question_text)
    
    def _enhance_scores_with_context(
        self, 
        base_scores: RubricScore, 
        answer_text: str, 
        question_text: str, 
        question_meta: Dict[str, Any]
    ) -> RubricScore:
        """Enhance base scores with question context analysis"""
        enhanced_scores = RubricScore(
            clarity=base_scores.clarity,
            structure=base_scores.structure,
            depth_specificity=base_scores.depth_specificity,
            role_fit=base_scores.role_fit,
            technical=base_scores.technical,
            communication=base_scores.communication,
            ownership=base_scores.ownership
        )
        
        # Question-specific enhancements
        if question_text:
            # Check if answer directly addresses the question
            question_keywords = self._extract_keywords(question_text.lower())
            answer_keywords = self._extract_keywords(answer_text.lower())
            
            keyword_overlap = len(question_keywords.intersection(answer_keywords))
            if keyword_overlap > 0:
                # Bonus for addressing question keywords
                relevance_bonus = min(0.5, keyword_overlap * 0.1)
                enhanced_scores.clarity = min(5.0, enhanced_scores.clarity + relevance_bonus)
        
        # Competency-specific enhancements
        if question_meta and "competency" in question_meta:
            competency = question_meta["competency"].lower()
            
            if competency == "technical":
                # Technical questions get technical score boost
                if enhanced_scores.technical < 4.0:
                    enhanced_scores.technical = min(4.0, enhanced_scores.technical + 0.5)
            
            elif competency == "leadership":
                # Leadership questions get ownership score boost
                if enhanced_scores.ownership < 4.0:
                    enhanced_scores.ownership = min(4.0, enhanced_scores.ownership + 0.5)
            
            elif competency == "communication":
                # Communication questions get communication score boost
                if enhanced_scores.communication < 4.0:
                    enhanced_scores.communication = min(4.0, enhanced_scores.communication + 0.5)
        
        return enhanced_scores
    
    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text"""
        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "this", "that", "these", "those"
        }
        
        # Extract words and filter
        words = text.split()
        keywords = set()
        
        for word in words:
            # Clean word
            clean_word = word.strip(".,!?;:()[]{}'\"")
            if clean_word and len(clean_word) > 2 and clean_word.lower() not in stop_words:
                keywords.add(clean_word.lower())
        
        return keywords
    
    def _generate_enhanced_rationale(
        self, 
        base_evaluation: ScoreDetail, 
        answer_text: str, 
        question_text: str, 
        question_meta: Dict[str, Any]
    ) -> str:
        """Generate enhanced rationale with question context"""
        rationale_parts = [base_evaluation.rationale]
        
        # Add question-specific insights
        if question_text and answer_text:
            # Check answer length appropriateness
            word_count = len(answer_text.split())
            if word_count < 30:
                rationale_parts.append("Answer is quite brief - consider providing more detail and examples.")
            elif word_count > 200:
                rationale_parts.append("Answer is comprehensive but could benefit from more concise structure.")
            else:
                rationale_parts.append("Answer length is appropriate for the question.")
        
        # Add competency-specific insights
        if question_meta and "competency" in question_meta:
            competency = question_meta["competency"].lower()
            
            if competency == "technical":
                if "api" in answer_text.lower() or "database" in answer_text.lower():
                    rationale_parts.append("Good use of technical terminology relevant to the role.")
                else:
                    rationale_parts.append("Consider using more technical terminology to demonstrate expertise.")
            
            elif competency == "behavioral":
                if "i" in answer_text.lower() and "result" in answer_text.lower():
                    rationale_parts.append("Strong behavioral response with personal ownership and outcomes.")
                else:
                    rationale_parts.append("Behavioral responses benefit from personal examples and specific outcomes.")
        
        return " ".join(rationale_parts)
    
    def _generate_enhanced_action_items(
        self, 
        base_evaluation: ScoreDetail, 
        answer_text: str, 
        question_text: str, 
        question_meta: Dict[str, Any]
    ) -> List[str]:
        """Generate enhanced action items with question context"""
        action_items = base_evaluation.action_items.copy()
        
        # Question-specific action items
        if question_text and answer_text:
            # Check for question-answer alignment
            question_keywords = self._extract_keywords(question_text.lower())
            answer_keywords = self._extract_keywords(answer_text.lower())
            
            if len(question_keywords.intersection(answer_keywords)) < 2:
                action_items.append("Ensure your answer directly addresses the key aspects of the question.")
        
        # Competency-specific action items
        if question_meta and "competency" in question_meta:
            competency = question_meta["competency"].lower()
            
            if competency == "technical":
                if "api" not in answer_text.lower() and "system" not in answer_text.lower():
                    action_items.append("Include technical architecture and system design details in technical responses.")
            
            elif competency == "leadership":
                if "team" not in answer_text.lower() and "lead" not in answer_text.lower():
                    action_items.append("Leadership responses should emphasize team management and guidance.")
            
            elif competency == "problem_solving":
                if "approach" not in answer_text.lower() and "method" not in answer_text.lower():
                    action_items.append("Problem-solving responses should outline your systematic approach.")
        
        # Answer quality action items
        word_count = len(answer_text.split())
        if word_count < 50:
            action_items.append("Expand your answers with more specific examples and details.")
        elif word_count > 300:
            action_items.append("Practice delivering concise, focused responses while maintaining detail.")
        
        return action_items
    
    def set_llm_provider(self, provider: str, api_key: str = None):
        """Set the LLM provider for evaluation"""
        if provider.lower() in ["openai", "anthropic", "cohere"]:
            self.use_local_baseline = False
            # TODO: Initialize LLM client
            print(f"LLM provider set to {provider}")
        else:
            self.use_local_baseline = True
            print(f"Unknown LLM provider {provider}, using local baseline")
    
    def enable_local_baseline(self):
        """Enable local baseline evaluation"""
        self.use_local_baseline = True
        print("Local baseline evaluation enabled")
    
    def disable_local_baseline(self):
        """Disable local baseline evaluation (requires LLM provider)"""
        if not self.use_local_baseline:
            self.use_local_baseline = True
            print("LLM provider not configured, keeping local baseline enabled")
        else:
            self.use_local_baseline = False
            print("Local baseline evaluation disabled")


# Factory function
def get_llm_judge_evaluator() -> LLMAsJudgeEvaluator:
    """Get an LLM-as-judge evaluator instance"""
    return LLMAsJudgeEvaluator()
