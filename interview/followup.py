from typing import List, Dict, Any, Optional
import random
from core.schemas import ScoreDetail


class FollowUpGenerator:
    """Generate follow-up questions based on answer evaluation"""
    
    def __init__(self):
        self.follow_up_templates = {
            "clarity": self._get_clarity_follow_ups(),
            "structure": self._get_structure_follow_ups(),
            "depth": self._get_depth_follow_ups(),
            "metrics": self._get_metrics_follow_ups(),
            "tradeoffs": self._get_tradeoffs_follow_ups(),
            "technical": self._get_technical_follow_ups(),
            "leadership": self._get_leadership_follow_ups()
        }
    
    async def generate_follow_ups(
        self, 
        answer_evaluation: ScoreDetail,
        question_meta: Dict[str, Any],
        max_follow_ups: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate follow-up questions based on answer evaluation"""
        follow_ups = []
        
        # Identify areas needing improvement
        improvement_areas = self._identify_improvement_areas(answer_evaluation)
        
        # Generate follow-ups for each improvement area
        for area in improvement_areas[:max_follow_ups]:
            follow_up = await self._generate_area_follow_up(area, answer_evaluation, question_meta)
            if follow_up:
                follow_ups.append(follow_up)
        
        # If no specific improvement areas, generate general follow-up
        if not follow_ups:
            follow_up = await self._generate_general_follow_up(answer_evaluation, question_meta)
            if follow_up:
                follow_ups.append(follow_up)
        
        return follow_ups
    
    def _identify_improvement_areas(self, evaluation: ScoreDetail) -> List[str]:
        """Identify areas that need improvement based on scores"""
        areas = []
        scores = evaluation.scores
        
        # Check each rubric dimension
        if scores.clarity < 3.5:
            areas.append("clarity")
        
        if scores.structure < 3.5:
            areas.append("structure")
        
        if scores.depth_specificity < 3.5:
            areas.append("depth")
        
        if scores.technical < 3.5:
            areas.append("technical")
        
        # Check for missing metrics
        if "metrics" not in areas and self._has_low_metrics_score(evaluation):
            areas.append("metrics")
        
        # Check for missing trade-offs
        if "tradeoffs" not in areas and self._has_low_tradeoffs_score(evaluation):
            areas.append("tradeoffs")
        
        # Check for leadership opportunities
        if scores.ownership < 3.5:
            areas.append("leadership")
        
        return areas
    
    def _has_low_metrics_score(self, evaluation: ScoreDetail) -> bool:
        """Check if answer lacks metrics"""
        # Look for metrics-related feedback in action items
        metrics_indicators = ["metrics", "quantifiable", "specific data", "numbers"]
        action_items_text = " ".join(evaluation.action_items).lower()
        
        return any(indicator in action_items_text for indicator in metrics_indicators)
    
    def _has_low_tradeoffs_score(self, evaluation: ScoreDetail) -> bool:
        """Check if answer lacks trade-off discussion"""
        # Look for trade-off related feedback
        tradeoff_indicators = ["trade-off", "complexity", "balance", "downside"]
        action_items_text = " ".join(evaluation.action_items).lower()
        
        return any(indicator in action_items_text for indicator in tradeoff_indicators)
    
    async def _generate_area_follow_up(
        self, 
        area: str, 
        evaluation: ScoreDetail, 
        question_meta: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a follow-up question for a specific improvement area"""
        if area not in self.follow_up_templates:
            return None
        
        templates = self.follow_up_templates[area]
        if not templates:
            return None
        
        # Select appropriate template
        template = random.choice(templates)
        
        # Customize template with context
        customized_question = self._customize_follow_up_template(
            template, evaluation, question_meta
        )
        
        return {
            "competency": question_meta.get("competency", "general"),
            "difficulty": "medium",  # Follow-ups are typically medium difficulty
            "text": customized_question["text"],
            "expected_signals": customized_question["expected_signals"],
            "pitfalls": customized_question["pitfalls"],
            "context_hints": customized_question["context_hints"],
            "is_follow_up": True,
            "improvement_area": area
        }
    
    async def _generate_general_follow_up(
        self, 
        evaluation: ScoreDetail, 
        question_meta: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a general follow-up question"""
        general_templates = [
            {
                "text": "Can you elaborate on one of the points you mentioned? I'd like to understand it better.",
                "expected_signals": ["Detailed explanation", "Specific examples", "Depth of knowledge"],
                "pitfalls": ["Vague elaboration", "No new information", "Repetition"],
                "context_hints": ["Choose a key point from your previous answer and expand on it"]
            },
            {
                "text": "What would you do differently if you faced a similar situation again?",
                "expected_signals": ["Learning reflection", "Continuous improvement", "Strategic thinking"],
                "pitfalls": ["No reflection", "Same approach", "No learning"],
                "context_hints": ["Consider what you learned and how you would apply it"]
            },
            {
                "text": "How does this experience relate to the role you're applying for?",
                "expected_signals": ["Role relevance", "Transferable skills", "Career alignment"],
                "pitfalls": ["No connection", "Generic response", "Role mismatch"],
                "context_hints": ["Connect your experience to the specific requirements of this role"]
            }
        ]
        
        template = random.choice(general_templates)
        
        return {
            "competency": question_meta.get("competency", "general"),
            "difficulty": "medium",
            "text": template["text"],
            "expected_signals": template["expected_signals"],
            "pitfalls": template["pitfalls"],
            "context_hints": template["context_hints"],
            "is_follow_up": True,
            "improvement_area": "general"
        }
    
    def _customize_follow_up_template(
        self, 
        template: Dict[str, Any], 
        evaluation: ScoreDetail, 
        question_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Customize a follow-up template with evaluation context"""
        text = template["text"]
        expected_signals = template["expected_signals"].copy()
        pitfalls = template["pitfalls"].copy()
        context_hints = template["context_hints"].copy()
        
        # Add context-specific hints based on improvement area
        if "metrics" in template.get("improvement_area", ""):
            context_hints.append("Include specific numbers, percentages, or quantifiable results")
        
        if "tradeoffs" in template.get("improvement_area", ""):
            context_hints.append("Consider discussing the pros and cons or challenges you faced")
        
        if "technical" in template.get("improvement_area", ""):
            context_hints.append("Provide technical details about the tools, technologies, or methods used")
        
        return {
            "text": text,
            "expected_signals": expected_signals,
            "pitfalls": pitfalls,
            "context_hints": context_hints
        }
    
    def _get_clarity_follow_ups(self) -> List[Dict[str, Any]]:
        """Get follow-up templates for clarity improvement"""
        return [
            {
                "text": "I want to make sure I understand correctly. Can you give me a specific example of what you mean?",
                "expected_signals": ["Concrete examples", "Clear explanation", "Specific details"],
                "pitfalls": ["Abstract response", "No examples", "Vague description"],
                "context_hints": ["Use a real, specific example from your experience"]
            },
            {
                "text": "Let me break this down. What was the first step you took, and why did you choose that approach?",
                "expected_signals": ["Step-by-step process", "Decision rationale", "Clear methodology"],
                "pitfalls": ["Jumping to solution", "No explanation", "Unclear process"],
                "context_hints": ["Walk through your thinking process step by step"]
            }
        ]
    
    def _get_structure_follow_ups(self) -> List[Dict[str, Any]]:
        """Get follow-up templates for structure improvement"""
        return [
            {
                "text": "Can you organize your thoughts into 2-3 key points? What would be the main takeaways?",
                "expected_signals": ["Organized thinking", "Key points", "Clear structure"],
                "pitfalls": ["Disorganized response", "No key points", "Rambling"],
                "context_hints": ["Think of 2-3 main points and organize your response around them"]
            },
            {
                "text": "Let's go through this chronologically. What happened first, then what, and what was the outcome?",
                "expected_signals": ["Chronological order", "Logical flow", "Clear timeline"],
                "pitfalls": ["Out of order", "Missing steps", "No timeline"],
                "context_hints": ["Present your experience in the order it happened"]
            }
        ]
    
    def _get_depth_follow_ups(self) -> List[Dict[str, Any]]:
        """Get follow-up templates for depth improvement"""
        return [
            {
                "text": "You mentioned the technology you used. Can you explain why you chose that specific approach?",
                "expected_signals": ["Technical reasoning", "Decision process", "Alternative consideration"],
                "pitfalls": ["No reasoning", "Generic choice", "No alternatives"],
                "context_hints": ["Explain your technical decision-making process"]
            },
            {
                "text": "What were the biggest challenges you faced, and how did you overcome them?",
                "expected_signals": ["Challenge identification", "Problem-solving", "Resilience"],
                "pitfalls": ["No challenges mentioned", "Easy success", "No problem-solving"],
                "context_hints": ["Be honest about challenges and show how you handled them"]
            }
        ]
    
    def _get_metrics_follow_ups(self) -> List[Dict[str, Any]]:
        """Get follow-up templates for metrics improvement"""
        return [
            {
                "text": "Can you quantify the impact? What were the numbers before and after?",
                "expected_signals": ["Quantifiable results", "Before/after data", "Impact measurement"],
                "pitfalls": ["No numbers", "Vague impact", "No measurement"],
                "context_hints": ["Include specific numbers, percentages, or metrics"]
            },
            {
                "text": "How did you measure success? What KPIs or metrics did you track?",
                "expected_signals": ["Success metrics", "KPI definition", "Measurement approach"],
                "pitfalls": ["No metrics", "Vague success", "No measurement"],
                "context_hints": ["Define how you measured and tracked success"]
            }
        ]
    
    def _get_tradeoffs_follow_ups(self) -> List[Dict[str, Any]]:
        """Get follow-up templates for trade-offs improvement"""
        return [
            {
                "text": "What were the trade-offs you considered? What were the pros and cons of your approach?",
                "expected_signals": ["Trade-off analysis", "Pros and cons", "Balanced thinking"],
                "pitfalls": ["No trade-offs", "One-sided view", "No analysis"],
                "context_hints": ["Consider both the benefits and drawbacks of your approach"]
            },
            {
                "text": "Were there alternative solutions you considered? Why did you choose this one over others?",
                "expected_signals": ["Alternative consideration", "Decision rationale", "Comparative analysis"],
                "pitfalls": ["No alternatives", "No comparison", "Single solution"],
                "context_hints": ["Think about other approaches you could have taken"]
            }
        ]
    
    def _get_technical_follow_ups(self) -> List[Dict[str, Any]]:
        """Get follow-up templates for technical improvement"""
        return [
            {
                "text": "Can you explain the technical architecture in more detail? What components were involved?",
                "expected_signals": ["Technical architecture", "System components", "Technical depth"],
                "pitfalls": ["No architecture", "Vague components", "Surface-level"],
                "context_hints": ["Describe the technical system design and components"]
            },
            {
                "text": "What technologies did you use, and how did you decide on the tech stack?",
                "expected_signals": ["Technology choices", "Stack selection", "Technical reasoning"],
                "pitfalls": ["No tech details", "Generic choices", "No reasoning"],
                "context_hints": ["Explain your technology selection process"]
            }
        ]
    
    def _get_leadership_follow_ups(self) -> List[Dict[str, Any]]:
        """Get follow-up templates for leadership improvement"""
        return [
            {
                "text": "How did you motivate your team during this project? What leadership approach did you take?",
                "expected_signals": ["Team motivation", "Leadership style", "People management"],
                "pitfalls": ["No leadership", "No team focus", "Individual only"],
                "context_hints": ["Focus on how you led and motivated your team"]
            },
            {
                "text": "What was your role in managing stakeholders? How did you handle different perspectives?",
                "expected_signals": ["Stakeholder management", "Perspective handling", "Communication"],
                "pitfalls": ["No stakeholders", "No management", "No communication"],
                "context_hints": ["Describe how you managed different stakeholder relationships"]
            }
        ]


# Factory function
def get_followup_generator() -> FollowUpGenerator:
    """Get a follow-up generator instance"""
    return FollowUpGenerator()
