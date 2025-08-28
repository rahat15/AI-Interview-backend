from typing import List, Dict, Any, Optional
import json
import random
from core.config import settings
from rag.store_pgvector import get_vector_store


class QuestionGenerator:
    """Generate interview questions based on CV/JD and context"""
    
    def __init__(self):
        self.competency_questions = {
            "technical": self._get_technical_questions(),
            "behavioral": self._get_behavioral_questions(),
            "leadership": self._get_leadership_questions(),
            "problem_solving": self._get_problem_solving_questions(),
            "communication": self._get_communication_questions()
        }
    
    async def generate_questions(
        self, 
        session_context: Dict[str, Any],
        num_questions: int = 10,
        db_session=None
    ) -> List[Dict[str, Any]]:
        """Generate questions for an interview session"""
        questions = []
        
        # Get relevant context from CV/JD
        context_snippets = await self._get_context_snippets(session_context, db_session)
        
        # Generate questions for each competency
        competencies = list(self.competency_questions.keys())
        questions_per_competency = max(1, num_questions // len(competencies))
        
        for competency in competencies:
            competency_questions = await self._generate_competency_questions(
                competency, 
                session_context, 
                context_snippets, 
                questions_per_competency
            )
            questions.extend(competency_questions)
        
        # Shuffle and limit to requested number
        random.shuffle(questions)
        return questions[:num_questions]
    
    async def _get_context_snippets(
        self, 
        session_context: Dict[str, Any], 
        db_session
    ) -> Dict[str, List[str]]:
        """Get relevant context snippets from CV/JD"""
        if not db_session:
            return {}
        
        try:
            vector_store = get_vector_store(db_session)
            
            # Search for relevant CV/JD content
            cv_snippets = []
            jd_snippets = []
            
            if session_context.get("cv_file_id"):
                cv_results = await vector_store.similarity_search(
                    f"role: {session_context['role']} industry: {session_context['industry']}",
                    k=5,
                    artifact_types=["cv"]
                )
                cv_snippets = [result["content"] for result in cv_results]
            
            if session_context.get("jd_file_id"):
                jd_results = await vector_store.similarity_search(
                    f"requirements responsibilities {session_context['role']}",
                    k=5,
                    artifact_types=["jd"]
                )
                jd_snippets = [result["content"] for result in jd_results]
            
            return {
                "cv": cv_snippets,
                "jd": jd_snippets
            }
        
        except Exception as e:
            print(f"Failed to get context snippets: {e}")
            return {}
    
    async def _generate_competency_questions(
        self,
        competency: str,
        session_context: Dict[str, Any],
        context_snippets: Dict[str, List[str]],
        num_questions: int
    ) -> List[Dict[str, Any]]:
        """Generate questions for a specific competency"""
        questions = []
        base_questions = self.competency_questions[competency]
        
        for i in range(num_questions):
            if i < len(base_questions):
                # Use existing template
                question_template = base_questions[i]
            else:
                # Generate new question from template
                question_template = random.choice(base_questions)
            
            # Customize question with context
            customized_question = self._customize_question(
                question_template, 
                session_context, 
                context_snippets
            )
            
            questions.append({
                "competency": competency,
                "difficulty": question_template["difficulty"],
                "text": customized_question["text"],
                "expected_signals": customized_question["expected_signals"],
                "pitfalls": customized_question["pitfalls"],
                "context_hints": customized_question["context_hints"]
            })
        
        return questions
    
    def _customize_question(
        self,
        template: Dict[str, Any],
        session_context: Dict[str, Any],
        context_snippets: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Customize a question template with session context"""
        text = template["text"]
        expected_signals = template["expected_signals"].copy()
        pitfalls = template["pitfalls"].copy()
        context_hints = []
        
        # Replace placeholders with actual context
        if "{role}" in text:
            text = text.replace("{role}", session_context["role"])
        
        if "{industry}" in text:
            text = text.replace("{industry}", session_context["industry"])
        
        if "{company}" in text:
            text = text.replace("{company}", session_context["company"])
        
        # Add context-specific signals and pitfalls
        if context_snippets.get("cv"):
            # Add CV-specific expectations
            cv_text = " ".join(context_snippets["cv"][:2])  # Use first 2 snippets
            if "python" in cv_text.lower():
                expected_signals.append("Python programming experience")
            if "aws" in cv_text.lower():
                expected_signals.append("Cloud infrastructure knowledge")
            if "lead" in cv_text.lower():
                expected_signals.append("Leadership experience")
        
        if context_snippets.get("jd"):
            # Add JD-specific expectations
            jd_text = " ".join(context_snippets["jd"][:2])
            if "agile" in jd_text.lower():
                expected_signals.append("Agile methodology experience")
            if "microservices" in jd_text.lower():
                expected_signals.append("Microservices architecture knowledge")
        
        # Add context hints
        if session_context.get("role"):
            context_hints.append(f"Focus on {session_context['role']} responsibilities")
        if session_context.get("industry"):
            context_hints.append(f"Consider {session_context['industry']} industry context")
        
        return {
            "text": text,
            "expected_signals": expected_signals,
            "pitfalls": pitfalls,
            "context_hints": context_hints
        }
    
    def _get_technical_questions(self) -> List[Dict[str, Any]]:
        """Get technical question templates"""
        return [
            {
                "text": "Can you walk me through a technical challenge you faced in your previous role as a {role}? What was the problem, how did you approach it, and what was the outcome?",
                "difficulty": "medium",
                "expected_signals": [
                    "Problem identification and analysis",
                    "Technical solution design",
                    "Implementation approach",
                    "Results and impact measurement"
                ],
                "pitfalls": [
                    "Vague problem description",
                    "No technical details",
                    "Missing outcome/results",
                    "No learning reflection"
                ]
            },
            {
                "text": "How would you design a scalable system to handle {industry} data processing? Walk me through your architecture decisions.",
                "difficulty": "hard",
                "expected_signals": [
                    "System design principles",
                    "Scalability considerations",
                    "Technology choices",
                    "Trade-off analysis"
                ],
                "pitfalls": [
                    "Over-engineering",
                    "No scalability discussion",
                    "Missing trade-offs",
                    "No technology justification"
                ]
            },
            {
                "text": "Describe a time when you had to learn a new technology quickly. How did you approach the learning process?",
                "difficulty": "easy",
                "expected_signals": [
                    "Learning methodology",
                    "Resource identification",
                    "Time management",
                    "Application of learning"
                ],
                "pitfalls": [
                    "No structured approach",
                    "No practical application",
                    "No time constraints mentioned"
                ]
            }
        ]
    
    def _get_behavioral_questions(self) -> List[Dict[str, Any]]:
        """Get behavioral question templates"""
        return [
            {
                "text": "Tell me about a time when you had to work with a difficult team member. How did you handle the situation?",
                "difficulty": "medium",
                "expected_signals": [
                    "Conflict resolution approach",
                    "Communication skills",
                    "Team collaboration",
                    "Positive outcome focus"
                ],
                "pitfalls": [
                    "Blaming others",
                    "No resolution mentioned",
                    "Negative attitude",
                    "No learning reflection"
                ]
            },
            {
                "text": "Describe a situation where you had to meet a tight deadline. How did you prioritize and manage your work?",
                "difficulty": "easy",
                "expected_signals": [
                    "Time management",
                    "Prioritization skills",
                    "Communication with stakeholders",
                    "Quality maintenance"
                ],
                "pitfalls": [
                    "No prioritization strategy",
                    "Quality compromise",
                    "No stakeholder communication",
                    "No deadline management"
                ]
            }
        ]
    
    def _get_leadership_questions(self) -> List[Dict[str, Any]]:
        """Get leadership question templates"""
        return [
            {
                "text": "Tell me about a time when you had to lead a team through a major change or transition. How did you approach it?",
                "difficulty": "hard",
                "expected_signals": [
                    "Change management approach",
                    "Team communication",
                    "Stakeholder management",
                    "Results and impact"
                ],
                "pitfalls": [
                    "No change management strategy",
                    "Poor communication",
                    "No stakeholder involvement",
                    "No measurable results"
                ]
            },
            {
                "text": "How do you motivate team members who are struggling or underperforming?",
                "difficulty": "medium",
                "expected_signals": [
                    "Performance management",
                    "Coaching approach",
                    "Individual development",
                    "Team support"
                ],
                "pitfalls": [
                    "Punitive approach",
                    "No individual consideration",
                    "No development focus",
                    "No support mechanisms"
                ]
            }
        ]
    
    def _get_problem_solving_questions(self) -> List[Dict[str, Any]]:
        """Get problem-solving question templates"""
        return [
            {
                "text": "Walk me through your problem-solving process. How do you typically approach complex problems?",
                "difficulty": "medium",
                "expected_signals": [
                    "Structured approach",
                    "Analysis methodology",
                    "Solution evaluation",
                    "Iterative improvement"
                ],
                "pitfalls": [
                    "No structured approach",
                    "Jumping to solutions",
                    "No evaluation criteria",
                    "No iteration process"
                ]
            },
            {
                "text": "Describe a time when you had to make a decision with incomplete information. How did you proceed?",
                "difficulty": "hard",
                "expected_signals": [
                    "Risk assessment",
                    "Information gathering",
                    "Decision framework",
                    "Outcome evaluation"
                ],
                "pitfalls": [
                    "Rash decisions",
                    "No risk consideration",
                    "No information seeking",
                    "No outcome review"
                ]
            }
        ]
    
    def _get_communication_questions(self) -> List[Dict[str, Any]]:
        """Get communication question templates"""
        return [
            {
                "text": "How do you explain complex technical concepts to non-technical stakeholders?",
                "difficulty": "medium",
                "expected_signals": [
                    "Audience adaptation",
                    "Simplification skills",
                    "Visual aids usage",
                    "Feedback incorporation"
                ],
                "pitfalls": [
                    "Technical jargon",
                    "No audience consideration",
                    "No examples",
                    "No feedback loop"
                ]
            },
            {
                "text": "Tell me about a time when you had to present to senior leadership. How did you prepare and what was the outcome?",
                "difficulty": "hard",
                "expected_signals": [
                    "Preparation strategy",
                    "Audience analysis",
                    "Clear messaging",
                    "Outcome and feedback"
                ],
                "pitfalls": [
                    "Poor preparation",
                    "No audience understanding",
                    "Unclear message",
                    "No outcome mentioned"
                ]
            }
        ]


# Factory function
def get_question_generator() -> QuestionGenerator:
    """Get a question generator instance"""
    return QuestionGenerator()
