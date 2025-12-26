"""
Advanced Interview System using LangGraph
Generates contextual questions based on CV and JD analysis
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import re
from datetime import datetime

@dataclass
class InterviewState:
    user_id: str
    session_id: str
    role_title: str
    company_name: str
    industry: str
    cv_content: str
    jd_content: str
    round_type: str
    current_stage: str = "intro"
    question_count: int = 0
    max_questions: int = 8
    history: List[Dict] = None
    cv_analysis: Dict = None
    jd_analysis: Dict = None
    completed: bool = False
    asked_questions: List[str] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.cv_analysis is None:
            self.cv_analysis = {}
        if self.jd_analysis is None:
            self.jd_analysis = {}
        if self.asked_questions is None:
            self.asked_questions = []

class AdvancedInterviewManager:
    def __init__(self):
        self.sessions: Dict[str, InterviewState] = {}
        self.question_stages = [
            "intro",
            "technical_background", 
            "experience_deep_dive",
            "role_alignment",
            "behavioral",
            "problem_solving",
            "company_culture",
            "closing"
        ]
    
    def create_session(self, user_id: str, session_id: str, role_title: str,
                      company_name: str, industry: str, jd: str = "",
                      cv: str = "", round_type: str = "full") -> Dict:
        """Create new interview session with CV/JD analysis"""
        
        state = InterviewState(
            user_id=user_id,
            session_id=session_id,
            role_title=role_title,
            company_name=company_name,
            industry=industry,
            cv_content=cv,
            jd_content=jd,
            round_type=round_type
        )
        
        # Analyze CV and JD content
        state.cv_analysis = self._analyze_cv(cv)
        state.jd_analysis = self._analyze_jd(jd)
        
        key = f"{user_id}_{session_id}"
        self.sessions[key] = state
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "role_title": role_title,
            "company_name": company_name,
            "industry": industry,
            "jd": jd,
            "cv": cv,
            "round_type": round_type,
            "status": "active",
            "history": [],
            "completed": False
        }
    
    async def step(self, user_id: str, session_id: str, user_answer: str = None, 
                  audio_data: bytes = None, audio_url: str = None) -> Dict:
        """Process interview step with intelligent question generation and voice analysis"""
        key = f"{user_id}_{session_id}"
        state = self.sessions.get(key)
        
        if not state:
            raise ValueError("Session not found")
        
        # Process previous answer if provided
        if user_answer and state.history:
            last_question = state.history[-1]
            if last_question.get("answer") is None:
                # Evaluate the answer (text + voice)
                evaluation = self._evaluate_answer(
                    last_question["question"], 
                    user_answer, 
                    state.cv_analysis, 
                    state.jd_analysis,
                    state.role_title,
                    audio_data=audio_data,
                    audio_url=audio_url
                )
                
                # Update the last question with answer and evaluation
                last_question["answer"] = user_answer
                last_question["evaluation"] = evaluation
                last_question["transcribed_text"] = user_answer  # Store the transcribed text
                if audio_data:
                    last_question["has_audio"] = True
        
        # Generate next question if not completed
        if not state.completed and state.question_count < state.max_questions:
            next_question = self._generate_next_question(state)
            if next_question:
                state.history.append({
                    "question": next_question,
                    "answer": None,
                    "evaluation": None,
                    "stage": state.current_stage,
                    "timestamp": datetime.utcnow().isoformat()
                })
                state.question_count += 1
            else:
                state.completed = True
        else:
            state.completed = True
        
        return {
            "user_id": state.user_id,
            "session_id": state.session_id,
            "role_title": state.role_title,
            "company_name": state.company_name,
            "industry": state.industry,
            "jd": state.jd_content,
            "cv": state.cv_content,
            "round_type": state.round_type,
            "status": "active" if not state.completed else "completed",
            "history": state.history,
            "completed": state.completed
        }
    
    def _analyze_cv(self, cv_content: str) -> Dict:
        """Analyze CV content to extract key information"""
        analysis = {
            "technologies": [],
            "experience_years": 0,
            "projects": [],
            "leadership": False,
            "education": "",
            "strengths": [],
            "gaps": []
        }
        
        if not cv_content:
            return analysis
        
        cv_lower = cv_content.lower()
        
        # Extract technologies
        tech_keywords = [
            "python", "javascript", "java", "react", "node", "express", "fastapi",
            "mongodb", "postgresql", "mysql", "redis", "docker", "kubernetes",
            "aws", "azure", "gcp", "microservices", "api", "rest", "graphql"
        ]
        
        for tech in tech_keywords:
            if tech in cv_lower:
                analysis["technologies"].append(tech.title())
        
        # Extract experience years
        year_matches = re.findall(r'(\d+)\+?\s*years?', cv_lower)
        if year_matches:
            analysis["experience_years"] = max([int(y) for y in year_matches])
        
        # Check for leadership indicators
        leadership_keywords = ["lead", "manage", "mentor", "team", "project ownership"]
        analysis["leadership"] = any(keyword in cv_lower for keyword in leadership_keywords)
        
        # Extract strengths from evidence
        if "downloads" in cv_lower:
            analysis["strengths"].append("Product impact with measurable downloads")
        if "projects" in cv_lower:
            analysis["strengths"].append("Multiple project experience")
        if "portfolio" in cv_lower:
            analysis["strengths"].append("Strong portfolio presence")
        
        # Identify gaps
        if not analysis["leadership"]:
            analysis["gaps"].append("Limited leadership experience mentioned")
        
        return analysis
    
    def _analyze_jd(self, jd_content: str) -> Dict:
        """Analyze JD content to extract requirements"""
        analysis = {
            "required_skills": [],
            "experience_level": "",
            "responsibilities": [],
            "company_focus": ""
        }
        
        if not jd_content:
            return analysis
        
        jd_lower = jd_content.lower()
        
        # Extract required skills
        skill_keywords = [
            "python", "javascript", "backend", "frontend", "fullstack",
            "microservices", "api", "database", "cloud", "devops"
        ]
        
        for skill in skill_keywords:
            if skill in jd_lower:
                analysis["required_skills"].append(skill.title())
        
        # Determine experience level
        if "senior" in jd_lower:
            analysis["experience_level"] = "Senior"
        elif "junior" in jd_lower:
            analysis["experience_level"] = "Junior"
        else:
            analysis["experience_level"] = "Mid-level"
        
        return analysis
    
    def _generate_next_question(self, state: InterviewState) -> Optional[str]:
        """Generate contextually relevant next question with variety tracking"""
        
        # Determine current stage based on question count
        stage_index = min(state.question_count, len(self.question_stages) - 1)
        state.current_stage = self.question_stages[stage_index]
        
        # Get possible questions for current stage
        possible_questions = self._get_stage_questions(state)
        
        # Filter out already asked questions
        available_questions = [q for q in possible_questions if q not in state.asked_questions]
        
        if not available_questions:
            # If all questions for this stage are used, move to next stage
            if stage_index < len(self.question_stages) - 1:
                state.current_stage = self.question_stages[stage_index + 1]
                possible_questions = self._get_stage_questions(state)
                available_questions = [q for q in possible_questions if q not in state.asked_questions]
            
            if not available_questions:
                return None  # No more unique questions available
        
        # Select the first available question (they're already contextually ordered)
        selected_question = available_questions[0]
        state.asked_questions.append(selected_question)
        
        return selected_question
    
    def _get_stage_questions(self, state: InterviewState) -> List[str]:
        """Get all possible questions for current stage"""
        questions = []
        
        if state.current_stage == "intro":
            questions = [
                "Tell me about yourself and what draws you to this role.",
                f"What interests you most about the {state.role_title} position?",
                "Walk me through your background and how it led you here."
            ]
        
        elif state.current_stage == "technical_background":
            techs = state.cv_analysis.get("technologies", [])
            if techs:
                primary_tech = techs[0]
                questions = [
                    f"I see you have experience with {primary_tech}. Can you walk me through a challenging project where you used {primary_tech} and the technical decisions you made?",
                    f"What's been your most complex {primary_tech} implementation?",
                    f"How do you stay current with {primary_tech} best practices?"
                ]
            else:
                questions = [
                    "What's the most complex technical challenge you've solved recently?",
                    "Describe your approach to learning new technologies.",
                    "Tell me about a technical decision you made that you're particularly proud of."
                ]
        
        elif state.current_stage == "experience_deep_dive":
            years = state.cv_analysis.get("experience_years", 0)
            if years > 3:
                questions = [
                    f"With {years} years of experience, what would you say has been your most significant professional growth moment?",
                    "What's the most impactful project you've worked on?",
                    "Describe a time when you had to make a critical technical decision under pressure."
                ]
            else:
                questions = [
                    "Describe a project where you had to learn something completely new. How did you approach it?",
                    "Tell me about a time when you exceeded expectations on a project.",
                    "What's been your biggest learning experience in your career so far?"
                ]
        
        elif state.current_stage == "role_alignment":
            required_skills = state.jd_analysis.get("required_skills", [])
            if required_skills:
                skill = required_skills[0]
                questions = [
                    f"This role requires strong {skill} skills. How does your background prepare you for these responsibilities?",
                    "How do you see your experience aligning with what we're looking for in this position?",
                    f"What excites you most about working with {skill} in this role?"
                ]
            else:
                questions = [
                    "How do you see your experience aligning with what we're looking for in this position?",
                    "What aspects of this role do you think you'd excel at?",
                    "Where do you see the biggest opportunities for growth in this position?"
                ]
        
        elif state.current_stage == "behavioral":
            if state.cv_analysis.get("leadership"):
                questions = [
                    "Tell me about a time when you had to lead a team through a difficult technical decision.",
                    "Describe a situation where you had to mentor or guide a junior developer.",
                    "How do you handle disagreements within your team?"
                ]
            else:
                questions = [
                    "Describe a situation where you had to collaborate with team members who had different technical opinions.",
                    "Tell me about a time when you had to work with a difficult stakeholder.",
                    "How do you handle feedback and criticism?"
                ]
        
        elif state.current_stage == "problem_solving":
            questions = [
                "Walk me through your approach when you encounter a problem you've never solved before.",
                "Describe a time when you had to debug a particularly challenging issue.",
                "How do you prioritize tasks when everything seems urgent?"
            ]
        
        elif state.current_stage == "company_culture":
            questions = [
                f"What interests you most about working at {state.company_name}, and how do you see yourself contributing to our team?",
                f"What do you know about {state.company_name}'s mission and values?",
                "How do you prefer to work within a team environment?"
            ]
        
        elif state.current_stage == "closing":
            questions = [
                "What questions do you have for me about the role, team, or company?",
                "Is there anything else you'd like me to know about your background?",
                "What are your expectations for the next steps in this process?"
            ]
        
        return questions
    
    def _evaluate_answer(self, question: str, answer: str, cv_analysis: Dict, 
                        jd_analysis: Dict, role_title: str, audio_data: bytes = None, 
                        audio_url: str = None) -> Dict:
        """Advanced answer evaluation with context-aware scoring and voice analysis"""
        
        # Text-based evaluation
        text_evaluation = self._evaluate_text_answer(question, answer, cv_analysis, jd_analysis, role_title)
        
        # Voice-based evaluation
        voice_evaluation = self._evaluate_voice_answer(audio_data, audio_url)
        
        # Combine evaluations
        combined_score = self._combine_text_voice_scores(text_evaluation, voice_evaluation)
        
        return {
            "score": combined_score["total_score"],
            "feedback": combined_score["feedback"],
            "suggestions": combined_score["suggestions"],
            "breakdown": {
                **text_evaluation["breakdown"],
                **voice_evaluation["voice_scores"]
            },
            "voice_metrics": voice_evaluation["voice_metrics"],
            "total_possible": 11.0  # 5 for text + 6 for voice
        }
    
    def _evaluate_text_answer(self, question: str, answer: str, cv_analysis: Dict, 
                             jd_analysis: Dict, role_title: str) -> Dict:
        """Evaluate text-based aspects of the answer"""
        
        # Initialize scoring components
        scores = {
            "relevance": 0,      # How well answer addresses the question
            "depth": 0,          # Level of detail and insight
            "structure": 0,      # Organization and clarity
            "examples": 0,       # Concrete examples and evidence
            "technical": 0,      # Technical accuracy and knowledge
            "alignment": 0       # Alignment with role/company
        }
        
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        # 1. RELEVANCE SCORING (0-2 points)
        relevance_score = self._score_relevance(question_lower, answer_lower, cv_analysis)
        scores["relevance"] = relevance_score
        
        # 2. DEPTH & DETAIL SCORING (0-1.5 points)
        depth_score = self._score_depth(answer, answer_lower)
        scores["depth"] = depth_score
        
        # 3. STRUCTURE SCORING (0-1 point)
        structure_score = self._score_structure(answer, answer_lower)
        scores["structure"] = structure_score
        
        # 4. EXAMPLES & EVIDENCE (0-1 point)
        examples_score = self._score_examples(answer_lower, cv_analysis)
        scores["examples"] = examples_score
        
        # 5. TECHNICAL KNOWLEDGE (0-1 point)
        technical_score = self._score_technical(answer_lower, cv_analysis, jd_analysis)
        scores["technical"] = technical_score
        
        # 6. ROLE ALIGNMENT (0-0.5 points)
        alignment_score = self._score_alignment(answer_lower, role_title, jd_analysis)
        scores["alignment"] = alignment_score
        
        # Calculate final score (out of 7, then scale to 5)
        total_score = sum(scores.values())
        final_score = min(5.0, (total_score / 7.0) * 5.0)
        
        # Generate detailed feedback
        feedback = self._generate_detailed_feedback(scores, answer_lower, question_lower)
        suggestions = self._generate_smart_suggestions(scores, answer_lower, question_lower)
        
        return {
            "score": round(final_score, 1),
            "feedback": feedback,
            "suggestions": suggestions,
            "breakdown": {k: round(v, 1) for k, v in scores.items()},
            "total_possible": 5.0
        }
    
    def _evaluate_voice_answer(self, audio_data: bytes = None, audio_url: str = None) -> Dict:
        """Evaluate voice-based aspects of the answer"""
        try:
            from interview.voice_analyzer import voice_analyzer
            return voice_analyzer.analyze_voice(audio_data=audio_data, audio_url=audio_url)
        except ImportError:
            # Fallback if voice analyzer not available
            return {
                "voice_scores": {
                    "fluency": 1.0,
                    "clarity": 0.8,
                    "confidence": 0.8,
                    "pace": 0.6,
                    "total": 3.2
                },
                "voice_metrics": {
                    "duration": 0,
                    "speech_rate": 0,
                    "avg_pitch": 0,
                    "pitch_variation": 0,
                    "avg_energy": 0,
                    "pause_ratio": 0,
                    "speech_segments": 0
                }
            }
    
    def _combine_text_voice_scores(self, text_eval: Dict, voice_eval: Dict) -> Dict:
        """Combine text and voice evaluations into final score"""
        
        text_score = text_eval["score"]  # Out of 5
        voice_score = voice_eval["voice_scores"]["total"]  # Out of 6
        
        # Combined score out of 11, scaled to 10
        total_score = min(10.0, ((text_score + voice_score) / 11.0) * 10.0)
        
        # Enhanced feedback
        feedback_parts = [text_eval["feedback"]]
        
        # Add voice feedback
        voice_scores = voice_eval["voice_scores"]
        if voice_scores["fluency"] >= 1.5:
            feedback_parts.append("Good speech fluency")
        elif voice_scores["fluency"] < 1.0:
            feedback_parts.append("Could improve speech fluency")
        
        if voice_scores["confidence"] >= 1.0:
            feedback_parts.append("Confident delivery")
        elif voice_scores["confidence"] < 0.8:
            feedback_parts.append("Could sound more confident")
        
        # Enhanced suggestions
        suggestions = text_eval["suggestions"].copy()
        
        # Add voice suggestions
        if voice_scores["pace"] < 0.6:
            suggestions.append("Adjust speaking pace - aim for 140-170 words per minute")
        if voice_scores["clarity"] < 1.0:
            suggestions.append("Speak more clearly and maintain consistent volume")
        if voice_scores["fluency"] < 1.2:
            suggestions.append("Reduce pauses and filler words for better fluency")
        
        return {
            "total_score": round(total_score, 1),
            "feedback": " | ".join(feedback_parts),
            "suggestions": suggestions[:4]  # Limit to top 4
        }
    
    def _score_relevance(self, question_lower: str, answer_lower: str, cv_analysis: Dict) -> float:
        """Score how well the answer addresses the question (0-2 points)"""
        score = 0.5  # Base score for attempting to answer
        
        # Check for direct question addressing
        if "tell me about yourself" in question_lower:
            if any(word in answer_lower for word in ["experience", "background", "engineer", "developer"]):
                score += 0.5
            if any(word in answer_lower for word in ["passionate", "specialize", "focus"]):
                score += 0.3
        
        elif "challenging project" in question_lower or "technical decision" in question_lower:
            if any(word in answer_lower for word in ["project", "built", "developed", "implemented"]):
                score += 0.7
            if any(word in answer_lower for word in ["challenge", "problem", "solution", "decision"]):
                score += 0.5
            else:
                score -= 0.3  # Penalty for not addressing the challenge aspect
        
        elif "learn something new" in question_lower:
            if any(word in answer_lower for word in ["learn", "new", "approach", "research"]):
                score += 0.8
            else:
                score -= 0.4  # Big penalty for not addressing learning
        
        elif "align" in question_lower or "background" in question_lower:
            if any(word in answer_lower for word in ["experience", "background", "skills", "match"]):
                score += 0.6
        
        elif "team" in question_lower or "lead" in question_lower:
            if any(word in answer_lower for word in ["team", "lead", "collaborate", "manage"]):
                score += 0.8
            else:
                score -= 0.5  # Penalty for not addressing team aspect
        
        elif "problem" in question_lower and "never solved" in question_lower:
            if any(word in answer_lower for word in ["approach", "research", "break down", "analyze"]):
                score += 0.7
        
        elif "company" in question_lower or "working at" in question_lower:
            if any(word in answer_lower for word in ["company", "team", "contribute", "mission"]):
                score += 0.6
        
        elif "questions" in question_lower and "for me" in question_lower:
            if "?" in answer_lower or any(word in answer_lower for word in ["what", "how", "when", "why"]):
                score += 0.8
            else:
                score -= 0.3  # Should ask questions
        
        return min(2.0, score)
    
    def _score_depth(self, answer: str, answer_lower: str) -> float:
        """Score the depth and detail of the answer (0-1.5 points)"""
        score = 0
        
        # Length-based scoring
        if len(answer) < 50:
            score = 0.1  # Too short
        elif len(answer) < 100:
            score = 0.4
        elif len(answer) < 200:
            score = 0.8
        elif len(answer) < 400:
            score = 1.2
        else:
            score = 1.5  # Comprehensive answer
        
        # Bonus for specific details
        if any(char.isdigit() for char in answer):
            score += 0.2  # Numbers/metrics
        
        # Penalty for generic responses
        generic_phrases = ["passionate software engineer", "5+ years of experience", "scalable applications"]
        if any(phrase in answer_lower for phrase in generic_phrases):
            score -= 0.3
        
        return min(1.5, max(0, score))
    
    def _score_structure(self, answer: str, answer_lower: str) -> float:
        """Score the structure and clarity (0-1 point)"""
        score = 0.3  # Base score
        
        # STAR method indicators
        star_words = ["situation", "task", "action", "result", "when", "then", "so", "because"]
        star_count = sum(1 for word in star_words if word in answer_lower)
        if star_count >= 3:
            score += 0.5
        elif star_count >= 2:
            score += 0.3
        
        # Logical flow indicators
        flow_words = ["first", "then", "next", "finally", "as a result", "therefore"]
        if any(word in answer_lower for word in flow_words):
            score += 0.2
        
        return min(1.0, score)
    
    def _score_examples(self, answer_lower: str, cv_analysis: Dict) -> float:
        """Score concrete examples and evidence (0-1 point)"""
        score = 0
        
        # Concrete action words
        action_words = ["built", "developed", "implemented", "designed", "created", "led", "managed"]
        action_count = sum(1 for word in action_words if word in answer_lower)
        score += min(0.4, action_count * 0.1)
        
        # Specific technologies mentioned
        cv_techs = [tech.lower() for tech in cv_analysis.get("technologies", [])]
        tech_mentions = sum(1 for tech in cv_techs if tech in answer_lower)
        score += min(0.3, tech_mentions * 0.1)
        
        # Quantifiable results
        if any(word in answer_lower for word in ["increased", "reduced", "improved", "achieved"]):
            score += 0.2
        
        # Specific project/company names
        if any(word in answer_lower for word in ["project", "application", "system", "platform"]):
            score += 0.1
        
        return min(1.0, score)
    
    def _score_technical(self, answer_lower: str, cv_analysis: Dict, jd_analysis: Dict) -> float:
        """Score technical knowledge and accuracy (0-1 point)"""
        score = 0
        
        # Technical terms from CV
        cv_techs = [tech.lower() for tech in cv_analysis.get("technologies", [])]
        cv_tech_mentions = sum(1 for tech in cv_techs if tech in answer_lower)
        score += min(0.4, cv_tech_mentions * 0.1)
        
        # Technical terms from JD
        jd_skills = [skill.lower() for skill in jd_analysis.get("required_skills", [])]
        jd_skill_mentions = sum(1 for skill in jd_skills if skill in answer_lower)
        score += min(0.3, jd_skill_mentions * 0.1)
        
        # Advanced technical concepts
        advanced_terms = ["architecture", "scalability", "performance", "optimization", "design patterns"]
        if any(term in answer_lower for term in advanced_terms):
            score += 0.3
        
        return min(1.0, score)
    
    def _score_alignment(self, answer_lower: str, role_title: str, jd_analysis: Dict) -> float:
        """Score alignment with role and company (0-0.5 points)"""
        score = 0
        
        # Role-specific terms
        role_lower = role_title.lower()
        if "senior" in role_lower and any(word in answer_lower for word in ["lead", "mentor", "senior"]):
            score += 0.2
        
        if "backend" in role_lower and any(word in answer_lower for word in ["backend", "server", "api"]):
            score += 0.2
        
        # Company interest indicators
        if any(word in answer_lower for word in ["excited", "interested", "passionate", "opportunity"]):
            score += 0.1
        
        return min(0.5, score)
    
    def _generate_detailed_feedback(self, scores: Dict, answer_lower: str, question_lower: str) -> str:
        """Generate specific, actionable feedback"""
        feedback_parts = []
        
        if scores["relevance"] >= 1.5:
            feedback_parts.append("Excellent question addressing")
        elif scores["relevance"] >= 1.0:
            feedback_parts.append("Good relevance to the question")
        elif scores["relevance"] < 0.8:
            feedback_parts.append("Answer could be more directly relevant to the question")
        
        if scores["depth"] >= 1.0:
            feedback_parts.append("Good level of detail provided")
        elif scores["depth"] < 0.5:
            feedback_parts.append("Could benefit from more specific details")
        
        if scores["examples"] >= 0.6:
            feedback_parts.append("Strong use of concrete examples")
        elif scores["examples"] < 0.3:
            feedback_parts.append("Would benefit from specific examples")
        
        if scores["technical"] >= 0.6:
            feedback_parts.append("Good technical knowledge demonstrated")
        
        if scores["structure"] >= 0.7:
            feedback_parts.append("Well-structured response")
        
        return " | ".join(feedback_parts) if feedback_parts else "Consider providing more specific details"
    
    def _generate_smart_suggestions(self, scores: Dict, answer_lower: str, question_lower: str) -> List[str]:
        """Generate intelligent, context-aware suggestions"""
        suggestions = []
        
        if scores["relevance"] < 1.0:
            if "challenging project" in question_lower:
                suggestions.append("Focus more on the specific challenge and how you overcame it")
            elif "learn something new" in question_lower:
                suggestions.append("Describe your learning process and what resources you used")
            elif "team" in question_lower:
                suggestions.append("Provide specific examples of team collaboration or leadership")
        
        if scores["depth"] < 0.8:
            suggestions.append("Add more specific details about your experience and outcomes")
        
        if scores["examples"] < 0.4:
            suggestions.append("Include concrete examples with measurable results")
        
        if scores["structure"] < 0.6:
            suggestions.append("Try using the STAR method: Situation, Task, Action, Result")
        
        if scores["technical"] < 0.5 and any(word in question_lower for word in ["technical", "project", "system"]):
            suggestions.append("Mention specific technologies and technical decisions you made")
        
        # Generic answer detection
        if "passionate software engineer" in answer_lower:
            suggestions.append("Avoid generic phrases - be more specific about your unique experience")
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def get_state(self, user_id: str, session_id: str) -> Optional[Dict]:
        """Get current session state"""
        key = f"{user_id}_{session_id}"
        state = self.sessions.get(key)
        
        if not state:
            return None
        
        return {
            "user_id": state.user_id,
            "session_id": state.session_id,
            "role_title": state.role_title,
            "company_name": state.company_name,
            "industry": state.industry,
            "jd": state.jd_content,
            "cv": state.cv_content,
            "round_type": state.round_type,
            "status": "active" if not state.completed else "completed",
            "history": state.history,
            "completed": state.completed,
            "current_stage": state.current_stage,
            "question_count": state.question_count,
            "asked_questions": state.asked_questions
        }
    
    def get_user_sessions(self, user_id: str) -> List[Dict]:
        """Get all sessions for a user"""
        user_sessions = []
        for key, state in self.sessions.items():
            if state.user_id == user_id:
                user_sessions.append({
                    "session_id": state.session_id,
                    "role_title": state.role_title,
                    "company_name": state.company_name,
                    "status": "completed" if state.completed else "active",
                    "question_count": state.question_count
                })
        return user_sessions
    
    def generate_report(self, user_id: str, session_id: str) -> Dict:
        """Generate comprehensive interview report"""
        state = self.get_state(user_id, session_id)
        
        if not state:
            return {"error": "Session not found"}
        
        # Calculate average scores
        scores = []
        answered_questions = [q for q in state["history"] if q.get("evaluation")]
        
        for question in answered_questions:
            eval_data = question.get("evaluation", {})
            if "score" in eval_data:
                scores.append(eval_data["score"])
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Generate competency breakdown
        competency_scores = {
            "technical": sum(s for s in scores[:3]) / min(3, len(scores)) if scores else 0,
            "communication": sum(s for s in scores[1:4]) / min(3, len(scores[1:4])) if len(scores) > 1 else 0,
            "problem_solving": sum(s for s in scores[2:5]) / min(3, len(scores[2:5])) if len(scores) > 2 else 0,
            "cultural_fit": sum(s for s in scores[-2:]) / min(2, len(scores[-2:])) if len(scores) > 1 else 0
        }
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "role": state["role_title"],
            "company": state["company_name"],
            "industry": state["industry"],
            "avg_scores": {
                "overall": round(avg_score, 1),
                **{k: round(v, 1) for k, v in competency_scores.items()}
            },
            "history": state["history"],
            "total_questions": len(state["history"]),
            "completed": state["completed"]
        }

# Global instance
interview_manager = AdvancedInterviewManager()