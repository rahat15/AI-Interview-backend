import re
from typing import Dict, List, Any, Tuple
from core.schemas import RubricScore, ScoreDetail


class RulesBasedEvaluator:
    """Rule-based evaluation of interview answers"""
    
    def __init__(self):
        self.star_patterns = {
            "situation": [
                r"when\s+i\s+was",
                r"in\s+my\s+role\s+as",
                r"during\s+my\s+time\s+at",
                r"while\s+working\s+on",
                r"the\s+challenge\s+was",
                r"the\s+problem\s+involved"
            ],
            "task": [
                r"my\s+responsibility\s+was",
                r"i\s+needed\s+to",
                r"the\s+goal\s+was\s+to",
                r"i\s+was\s+tasked\s+with",
                r"my\s+role\s+was\s+to"
            ],
            "action": [
                r"i\s+started\s+by",
                r"first,\s+i",
                r"then\s+i",
                r"i\s+decided\s+to",
                r"i\s+implemented",
                r"i\s+created",
                r"i\s+worked\s+with"
            ],
            "result": [
                r"as\s+a\s+result",
                r"the\s+outcome\s+was",
                r"this\s+led\s+to",
                r"we\s+achieved",
                r"the\s+impact\s+was",
                r"this\s+resulted\s+in"
            ]
        }
        
        self.metrics_patterns = [
            r"\d+\s*%",
            r"\d+\s*percent",
            r"\$\d+",
            r"\d+\s*users?",
            r"\d+\s*customers?",
            r"\d+\s*employees?",
            r"reduced\s+by\s+\d+",
            r"increased\s+by\s+\d+",
            r"improved\s+by\s+\d+"
        ]
        
        self.tradeoff_patterns = [
            r"trade.?off",
            r"on\s+the\s+other\s+hand",
            r"however",
            r"but\s+the\s+downside",
            r"the\s+challenge\s+was",
            r"we\s+had\s+to\s+balance",
            r"we\s+weighed\s+the\s+options"
        ]
    
    def evaluate_answer(self, answer_text: str, question_meta: Dict[str, Any]) -> ScoreDetail:
        """Evaluate an answer using rule-based scoring"""
        # Clean and normalize text
        clean_text = self._clean_text(answer_text)
        
        # Analyze STAR components
        star_scores = self._analyze_star_patterns(clean_text)
        
        # Analyze metrics usage
        metrics_score = self._analyze_metrics(clean_text)
        
        # Analyze trade-off recognition
        tradeoff_score = self._analyze_tradeoffs(clean_text)
        
        # Analyze structure and clarity
        structure_score = self._analyze_structure(clean_text)
        
        # Analyze depth and specificity
        depth_score = self._analyze_depth(clean_text)
        
        # Calculate rubric scores
        rubric_scores = RubricScore(
            clarity=self._calculate_clarity_score(clean_text, star_scores),
            structure=structure_score,
            depth_specificity=depth_score,
            role_fit=self._calculate_role_fit_score(clean_text, question_meta),
            technical=self._calculate_technical_score(clean_text, question_meta),
            communication=self._calculate_communication_score(clean_text, star_scores),
            ownership=self._calculate_ownership_score(clean_text, star_scores)
        )
        
        # Generate rationale
        rationale = self._generate_rationale(
            star_scores, metrics_score, tradeoff_score, 
            structure_score, depth_score, rubric_scores
        )
        
        # Generate action items
        action_items = self._generate_action_items(
            star_scores, metrics_score, tradeoff_score, 
            structure_score, depth_score
        )
        
        # Find exemplar snippet
        exemplar_snippet = self._find_exemplar_snippet(clean_text, star_scores)
        
        return ScoreDetail(
            scores=rubric_scores,
            rationale=rationale,
            action_items=action_items,
            exemplar_snippet=exemplar_snippet
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase for pattern matching
        text_lower = text.lower()
        
        return text_lower
    
    def _analyze_star_patterns(self, text: str) -> Dict[str, float]:
        """Analyze STAR (Situation, Task, Action, Result) patterns"""
        scores = {}
        
        for component, patterns in self.star_patterns.items():
            component_score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    component_score += len(matches) * 0.25  # 0.25 points per match
            
            # Cap at 1.0
            scores[component] = min(1.0, component_score)
        
        return scores
    
    def _analyze_metrics(self, text: str) -> float:
        """Analyze usage of metrics and quantifiable data"""
        metrics_count = 0
        
        for pattern in self.metrics_patterns:
            matches = re.findall(pattern, text)
            metrics_count += len(matches)
        
        # Score based on metrics usage (0-1 scale)
        if metrics_count == 0:
            return 0.0
        elif metrics_count == 1:
            return 0.3
        elif metrics_count == 2:
            return 0.6
        elif metrics_count == 3:
            return 0.8
        else:
            return 1.0
    
    def _analyze_tradeoffs(self, text: str) -> float:
        """Analyze recognition of trade-offs and complexity"""
        tradeoff_count = 0
        
        for pattern in self.tradeoff_patterns:
            matches = re.findall(pattern, text)
            tradeoff_count += len(matches)
        
        # Score based on trade-off recognition (0-1 scale)
        if tradeoff_count == 0:
            return 0.0
        elif tradeoff_count == 1:
            return 0.5
        else:
            return 1.0
    
    def _analyze_structure(self, text: str) -> float:
        """Analyze answer structure and organization"""
        # Check for clear paragraph breaks or bullet points
        structure_indicators = [
            r"first",
            r"second",
            r"third",
            r"finally",
            r"in\s+conclusion",
            r"to\s+summarize",
            r"the\s+key\s+points\s+are"
        ]
        
        structure_score = 0
        for pattern in structure_indicators:
            if re.search(pattern, text):
                structure_score += 0.2
        
        # Check for logical flow
        if len(text.split()) > 100:  # Longer answers get structure bonus
            structure_score += 0.3
        
        return min(1.0, structure_score)
    
    def _analyze_depth(self, text: str) -> float:
        """Analyze depth and specificity of the answer"""
        # Count technical terms and specific details
        technical_terms = [
            r"api",
            r"database",
            r"algorithm",
            r"architecture",
            r"framework",
            r"protocol",
            r"infrastructure",
            r"deployment",
            r"monitoring",
            r"testing"
        ]
        
        depth_score = 0
        for term in technical_terms:
            if re.search(term, text):
                depth_score += 0.1
        
        # Bonus for specific examples
        if re.search(r"for\s+example", text) or re.search(r"specifically", text):
            depth_score += 0.2
        
        # Bonus for time references
        if re.search(r"\d+\s*(days?|weeks?|months?)", text):
            depth_score += 0.1
        
        return min(1.0, depth_score)
    
    def _calculate_clarity_score(self, text: str, star_scores: Dict[str, float]) -> float:
        """Calculate clarity score based on STAR components and text quality"""
        # Base score from STAR analysis
        star_score = sum(star_scores.values()) / len(star_scores)
        
        # Text quality factors
        word_count = len(text.split())
        if word_count < 20:
            clarity_bonus = 0.0
        elif word_count < 50:
            clarity_bonus = 0.1
        elif word_count < 100:
            clarity_bonus = 0.2
        else:
            clarity_bonus = 0.3
        
        # Check for filler words
        filler_words = ["um", "uh", "like", "you know", "basically", "actually"]
        filler_penalty = 0
        for filler in filler_words:
            if filler in text:
                filler_penalty += 0.1
        
        clarity_score = (star_score * 0.7) + clarity_bonus - filler_penalty
        return max(0.0, min(5.0, clarity_score * 5))  # Scale to 0-5
    
    def _calculate_role_fit_score(self, text: str, question_meta: Dict[str, Any]) -> float:
        """Calculate role fit score based on question context"""
        # Default score
        role_fit_score = 3.0
        
        # Check for role-specific terminology
        if question_meta and "competency" in question_meta:
            competency = question_meta["competency"].lower()
            
            if competency == "technical":
                technical_terms = ["code", "system", "architecture", "design", "implementation"]
                if any(term in text for term in technical_terms):
                    role_fit_score += 1.0
            
            elif competency == "leadership":
                leadership_terms = ["team", "lead", "manage", "coach", "mentor"]
                if any(term in text for term in leadership_terms):
                    role_fit_score += 1.0
        
        return min(5.0, role_fit_score)
    
    def _calculate_technical_score(self, text: str, question_meta: Dict[str, Any]) -> float:
        """Calculate technical score based on technical depth"""
        technical_score = 0.0
        
        # Technical terminology usage
        technical_terms = [
            "api", "database", "algorithm", "architecture", "framework",
            "protocol", "infrastructure", "deployment", "monitoring", "testing",
            "scalability", "performance", "security", "optimization"
        ]
        
        for term in technical_terms:
            if term in text:
                technical_score += 0.3
        
        # Specific technical details
        if re.search(r"\d+\s*ms", text) or re.search(r"\d+\s*seconds?", text):
            technical_score += 0.5
        
        if re.search(r"aws|azure|gcp|kubernetes|docker", text):
            technical_score += 0.5
        
        return min(5.0, technical_score)
    
    def _calculate_communication_score(self, text: str, star_scores: Dict[str, float]) -> float:
        """Calculate communication score based on STAR structure and clarity"""
        # Base score from STAR analysis
        star_score = sum(star_scores.values()) / len(star_scores)
        
        # Communication quality factors
        communication_score = star_score * 3.0  # Scale STAR score to 0-3
        
        # Bonus for clear structure
        if re.search(r"first|second|finally|in conclusion", text):
            communication_score += 0.5
        
        # Bonus for specific examples
        if re.search(r"for example|specifically|in particular", text):
            communication_score += 0.5
        
        # Penalty for filler words
        filler_words = ["um", "uh", "like", "you know"]
        filler_count = sum(1 for filler in filler_words if filler in text)
        communication_score -= filler_count * 0.2
        
        return max(0.0, min(5.0, communication_score))
    
    def _calculate_ownership_score(self, text: str, star_scores: Dict[str, float]) -> float:
        """Calculate ownership score based on personal responsibility"""
        ownership_score = 0.0
        
        # Personal pronouns indicating ownership
        personal_pronouns = ["i", "my", "me", "myself"]
        for pronoun in personal_pronouns:
            if re.search(rf"\b{pronoun}\b", text):
                ownership_score += 0.5
        
        # Action verbs indicating personal responsibility
        action_verbs = ["i did", "i created", "i implemented", "i designed", "i led"]
        for verb in action_verbs:
            if verb in text:
                ownership_score += 0.3
        
        # STAR result component (shows outcome ownership)
        if star_scores.get("result", 0) > 0.5:
            ownership_score += 1.0
        
        return min(5.0, ownership_score)
    
    def _generate_rationale(self, star_scores: Dict[str, float], metrics_score: float,
                           tradeoff_score: float, structure_score: float, depth_score: float,
                           rubric_scores: RubricScore) -> str:
        """Generate evaluation rationale"""
        rationale_parts = []
        
        # STAR analysis
        star_avg = sum(star_scores.values()) / len(star_scores)
        if star_avg > 0.7:
            rationale_parts.append("Strong STAR structure with clear situation, task, action, and result components.")
        elif star_avg > 0.4:
            rationale_parts.append("Moderate STAR structure with some missing components.")
        else:
            rationale_parts.append("Weak STAR structure - missing key components of effective storytelling.")
        
        # Metrics usage
        if metrics_score > 0.7:
            rationale_parts.append("Good use of quantifiable metrics and specific data.")
        elif metrics_score > 0.3:
            rationale_parts.append("Some metrics used but could benefit from more specific data.")
        else:
            rationale_parts.append("Limited use of metrics - consider adding quantifiable results.")
        
        # Trade-off recognition
        if tradeoff_score > 0.7:
            rationale_parts.append("Demonstrates awareness of trade-offs and complexity.")
        elif tradeoff_score > 0.3:
            rationale_parts.append("Some recognition of trade-offs but could be more explicit.")
        else:
            rationale_parts.append("Limited discussion of trade-offs - consider addressing complexity.")
        
        # Overall assessment
        total_score = (rubric_scores.clarity + rubric_scores.structure + 
                      rubric_scores.depth_specificity + rubric_scores.role_fit + 
                      rubric_scores.technical + rubric_scores.communication + 
                      rubric_scores.ownership) / 7
        
        if total_score > 4.0:
            rationale_parts.append("Overall excellent response demonstrating strong competencies.")
        elif total_score > 3.0:
            rationale_parts.append("Good response with room for improvement in specific areas.")
        else:
            rationale_parts.append("Response needs improvement across multiple competency areas.")
        
        return " ".join(rationale_parts)
    
    def _generate_action_items(self, star_scores: Dict[str, float], metrics_score: float,
                              tradeoff_score: float, structure_score: float, 
                              depth_score: float) -> List[str]:
        """Generate actionable improvement items"""
        action_items = []
        
        # STAR improvements
        star_avg = sum(star_scores.values()) / len(star_scores)
        if star_avg < 0.7:
            action_items.append("Practice using the STAR method (Situation, Task, Action, Result) for behavioral questions.")
        
        if star_scores.get("result", 0) < 0.5:
            action_items.append("Always include specific outcomes and results when describing past experiences.")
        
        # Metrics improvements
        if metrics_score < 0.5:
            action_items.append("Include quantifiable metrics and specific data to strengthen your examples.")
        
        # Trade-off improvements
        if tradeoff_score < 0.5:
            action_items.append("Consider discussing trade-offs and complexity in your responses.")
        
        # Structure improvements
        if structure_score < 0.5:
            action_items.append("Use clear structure with transitions like 'First,' 'Second,' 'Finally' to organize your thoughts.")
        
        # Depth improvements
        if depth_score < 0.5:
            action_items.append("Provide more specific technical details and examples to demonstrate depth of knowledge.")
        
        return action_items
    
    def _find_exemplar_snippet(self, text: str, star_scores: Dict[str, float]) -> str:
        """Find the best exemplar snippet from the answer"""
        # Look for the strongest STAR component
        best_component = max(star_scores.items(), key=lambda x: x[1])
        
        if best_component[1] > 0.5:
            # Find text around the best component
            component_patterns = self.star_patterns[best_component[0]]
            for pattern in component_patterns:
                match = re.search(pattern, text)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 100)
                    return text[start:end].strip()
        
        # Fallback: return first 100 characters
        return text[:100] + "..." if len(text) > 100 else text


# Factory function
def get_rules_evaluator() -> RulesBasedEvaluator:
    """Get a rules-based evaluator instance"""
    return RulesBasedEvaluator()
