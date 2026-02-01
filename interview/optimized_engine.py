"""
Optimized Interview Engine using LangGraph with best practices
- Streaming responses for faster perceived performance
- Async/concurrent operations
- MongoDB caching for reduced API calls
- Efficient state management
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict
import google.generativeai as genai

from core.config import settings
from core.db import get_database
from interview.performance import monitor, track_llm_call, RequestTimer

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


# ============================================================================
# State Definitions
# ============================================================================

class InterviewMessage(TypedDict):
    role: str  # 'interviewer' or 'candidate'
    content: str
    timestamp: float
    metadata: Optional[Dict[str, Any]]


class OptimizedInterviewState(TypedDict):
    session_id: str
    user_id: str
    role: str
    company: str
    cv_text: str
    jd_text: str
    
    # Context cache (computed once, reused)
    cv_summary: Optional[str]
    jd_requirements: Optional[List[str]]
    candidate_skills: Optional[List[str]]
    
    # Conversation state
    messages: List[InterviewMessage]
    question_count: int
    stage: str  # intro, technical, behavioral, closing
    
    # Metadata
    created_at: float
    last_updated: float
    completed: bool
    
    # Performance tracking
    response_times: List[float]


# ============================================================================
# Caching Layer
# ============================================================================

class MongoCache:
    """MongoDB-based caching for interview sessions and context"""
    
    def __init__(self):
        self.db = None
        self.cache_ttl = timedelta(hours=24)
    
    async def _get_db(self):
        """Lazy database connection"""
        if self.db is None:
            self.db = await get_database()
        return self.db
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached session state"""
        try:
            db = await self._get_db()
            session = await db.interview_sessions.find_one({"session_id": session_id})
            
            if session and session.get("expires_at", 0) > time.time():
                logger.info(f"Cache HIT: session {session_id}")
                monitor.record_cache_hit(f"session_{session_id}")
                return session.get("state")
            
            logger.info(f"Cache MISS: session {session_id}")
            monitor.record_cache_miss(f"session_{session_id}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def save_session(self, session_id: str, state: Dict[str, Any]):
        """Cache session state in MongoDB"""
        try:
            db = await self._get_db()
            await db.interview_sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "session_id": session_id,
                        "state": state,
                        "updated_at": time.time(),
                        "expires_at": time.time() + self.cache_ttl.total_seconds()
                    }
                },
                upsert=True
            )
            logger.info(f"Cached session: {session_id}")
        except Exception as e:
            logger.error(f"Cache save error: {e}")
    
    async def get_cv_analysis(self, cv_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached CV analysis to avoid reprocessing"""
        try:
            db = await self._get_db()
            result = await db.cv_analysis_cache.find_one({"cv_hash": cv_hash})
            if result and result.get("expires_at", 0) > time.time():
                monitor.record_cache_hit(f"cv_{cv_hash[:8]}")
                return result.get("analysis")
            monitor.record_cache_miss(f"cv_{cv_hash[:8]}")
            return None
        except Exception as e:
            logger.error(f"CV cache error: {e}")
            return None
    
    async def save_cv_analysis(self, cv_hash: str, analysis: Dict[str, Any]):
        """Cache CV analysis"""
        try:
            db = await self._get_db()
            await db.cv_analysis_cache.update_one(
                {"cv_hash": cv_hash},
                {
                    "$set": {
                        "cv_hash": cv_hash,
                        "analysis": analysis,
                        "created_at": time.time(),
                        "expires_at": time.time() + timedelta(days=7).total_seconds()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"CV cache save error: {e}")


# Global cache instance
cache = MongoCache()


# ============================================================================
# Context Analyzer (with caching)
# ============================================================================

class ContextAnalyzer:
    """Analyze CV/JD once and cache results"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # Best stable model - fast with 1M token support
    
    async def analyze_cv(self, cv_text: str) -> Dict[str, Any]:
        """Extract key information from CV (cached)"""
        import hashlib
        cv_hash = hashlib.md5(cv_text.encode()).hexdigest()
        
        # Check cache first
        cached = await cache.get_cv_analysis(cv_hash)
        if cached:
            logger.info(f"✅ Using cached CV analysis (hash: {cv_hash[:8]}...)")
            return cached
        
        # Analyze with Gemini
        prompt = f"""Analyze this resume/CV carefully and extract ALL key information in JSON format.

RESUME/CV:
{cv_text}

Extract the following details. BE THOROUGH and accurate:

Return ONLY a valid JSON object with these exact fields:
{{
    "candidate_name": "Full name of the candidate (IMPORTANT: extract from CV)",
    "email": "Email address if present, else null",
    "phone": "Phone number if present, else null",
    "location": "City/Country if mentioned, else null",
    "summary": "2-3 sentence professional summary highlighting key experience and expertise",
    "current_role": "Current or most recent job title",
    "current_company": "Current or most recent company name",
    "total_experience_years": <number of years of total experience>,
    "skills": ["skill1", "skill2", "skill3", ...],
    "technical_skills": ["programming languages", "frameworks", "tools", ...],
    "key_projects": ["Brief description of notable project 1", "project 2", ...],
    "education": ["Degree, University, Year", ...],
    "certifications": ["cert1", "cert2", ...],
    "strengths": ["strength1", "strength2", "strength3"],
    "achievements": ["achievement1", "achievement2", ...]
}}

IMPORTANT: Extract the candidate's NAME from the CV. It's usually at the top."""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            result_text = response.text.strip()
            
            # Log raw Gemini response for CV analysis
            logger.info("=" * 80)
            logger.info("🤖 GEMINI CV ANALYSIS RESPONSE:")
            logger.info(result_text)
            logger.info("=" * 80)
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(result_text)
            
            # Log extracted info for debugging
            logger.info(f"📋 Extracted candidate: {analysis.get('candidate_name', 'Unknown')}")
            logger.info(f"📋 Email: {analysis.get('email', 'N/A')}")
            logger.info(f"📋 Role: {analysis.get('current_role', 'N/A')} at {analysis.get('current_company', 'N/A')}")
            logger.info(f"📋 Experience: {analysis.get('total_experience_years', 0)} years")
            logger.info(f"📋 Technical Skills: {', '.join(analysis.get('technical_skills', [])[:5])}")
            logger.info(f"📋 Total Skills: {len(analysis.get('skills', []))} extracted")
            
            # Cache the result
            await cache.save_cv_analysis(cv_hash, analysis)
            
            return analysis
        except Exception as e:
            logger.error(f"CV analysis error: {e}")
            # Return minimal fallback
            return {
                "candidate_name": "Candidate",
                "email": None,
                "phone": None,
                "location": None,
                "summary": "Experienced professional",
                "current_role": "Professional",
                "current_company": None,
                "total_experience_years": 0,
                "skills": [],
                "technical_skills": [],
                "key_projects": [],
                "education": [],
                "certifications": [],
                "strengths": [],
                "achievements": []
            }
    
    async def analyze_jd(self, jd_text: str) -> Dict[str, Any]:
        """Extract requirements from JD (lightweight, no caching needed)"""
        prompt = f"""Extract key requirements from this job description in JSON:

{jd_text}

Return ONLY:
{{
    "must_have_skills": ["skill1", "skill2", ...],
    "nice_to_have": ["skill1", "skill2", ...],
    "responsibilities": ["resp1", "resp2", ...]
}}"""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            result_text = response.text.strip()
            
            # Log JD analysis response
            logger.info("=" * 80)
            logger.info("🤖 GEMINI JD ANALYSIS RESPONSE:")
            logger.info(result_text)
            logger.info("=" * 80)
            
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            
            jd_analysis = json.loads(result_text)
            logger.info(f"📋 Must-have skills: {', '.join(jd_analysis.get('must_have_skills', [])[:5])}")
            logger.info(f"📋 Nice-to-have: {', '.join(jd_analysis.get('nice_to_have', [])[:3])}")
            
            return jd_analysis
        except Exception as e:
            logger.error(f"JD analysis error: {e}")
            return {
                "must_have_skills": [],
                "nice_to_have": [],
                "responsibilities": []
            }


# ============================================================================
# Question Generator (Streaming)
# ============================================================================

class StreamingQuestionGenerator:
    """Generate interview questions with streaming support"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # Best stable model - fast with 1M token support
    
    def build_context_prompt(self, state: OptimizedInterviewState) -> str:
        """Build efficient context prompt using CV analysis"""
        stage = state.get("stage", "intro")
        question_count = state.get("question_count", 0)
        
        # Get detailed CV analysis
        cv_analysis = state.get("cv_analysis", {})
        candidate_name = cv_analysis.get("candidate_name", "")
        
        # Handle missing or placeholder names from old cache
        if not candidate_name or candidate_name in ["Candidate", "the candidate", "[Candidate Name]", "Unknown"]:
            candidate_name = ""  # Don't use placeholder
        
        current_role = cv_analysis.get("current_role", "professional")
        current_company = cv_analysis.get("current_company", "")
        experience_years = cv_analysis.get("total_experience_years", 0)
        technical_skills = cv_analysis.get("technical_skills", [])
        key_projects = cv_analysis.get("key_projects", [])
        
        # Get JD requirements
        jd_requirements = state.get("jd_requirements", [])
        
        # Build candidate context
        if candidate_name:
            candidate_context = f"{candidate_name}"
        else:
            candidate_context = "The candidate"
            
        if current_role:
            candidate_context += f", currently working as {current_role}" if candidate_name else f" is currently working as {current_role}"
        if current_company:
            candidate_context += f" at {current_company}"
        if experience_years > 0:
            candidate_context += f" with {experience_years} years of experience"
        
        # Build skills context
        skills_context = ""
        if technical_skills:
            skills_context = f"\nCandidate's Technical Skills: {', '.join(technical_skills[:8])}"
        
        # Build projects context
        projects_context = ""
        if key_projects:
            projects_context = f"\nNotable Projects: {'; '.join(key_projects[:3])}"
        
        # Personalized greeting instruction
        greeting_instruction = f"use their name ({candidate_name})" if candidate_name else "greet them warmly"
        closing_name = candidate_name if candidate_name else "them"
        
        stage_instructions = {
            "intro": f"Start with a warm, personalized greeting ({greeting_instruction}). Ask an opening question about their background or current role{' at ' + current_company if current_company else ''}.",
            "technical": f"Ask a technical question based on their experience with {', '.join(technical_skills[:3]) if technical_skills else 'the technologies'} OR the job requirements: {', '.join(jd_requirements[:3]) if jd_requirements else 'relevant technologies'}. Reference their specific experience.",
            "behavioral": f"Ask a behavioral question using the STAR method. Consider their {experience_years} years of experience and role as {current_role}.",
            "closing": f"Wrap up professionally, thank {closing_name}, and ask if they have any questions about the {state.get('role', 'role')} position."
        }
        
        return f"""You are conducting a professional interview for the {state.get('role', 'position')} role at {state.get('company', 'the company')}.

CANDIDATE PROFILE:
{candidate_context}{skills_context}{projects_context}

JOB REQUIREMENTS: {', '.join(jd_requirements[:5]) if jd_requirements else 'See job description'}

INTERVIEW STAGE: {stage}
QUESTION NUMBER: {question_count + 1}

INSTRUCTIONS: {stage_instructions.get(stage, 'Ask a relevant interview question')}

IMPORTANT:
{"- Use the candidate's NAME (" + candidate_name + ") when appropriate" if candidate_name else "- Greet the candidate warmly (name not available)"}
- Reference their SPECIFIC experience and skills
- Keep the tone conversational, warm, and professional
- Ask ONE clear, focused question
- Make it feel personalized, not generic

Generate the next interview question:"""
    
    async def generate_question(self, state: OptimizedInterviewState) -> str:
        """Generate next interview question (non-streaming for now)"""
        start_time = time.time()
        
        prompt = self.build_context_prompt(state)
        
        try:
            # Run in thread pool to avoid blocking
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            question = response.text.strip()
            
            # Log generated question
            logger.info("=" * 80)
            logger.info("🤖 GEMINI GENERATED QUESTION:")
            logger.info(question)
            logger.info("=" * 80)
            
            # Track performance
            elapsed = time.time() - start_time
            state.setdefault("response_times", []).append(elapsed)
            monitor.record_llm_call(elapsed, "gemini-2.5-flash", "generate_question")
            logger.info(f"Question generated in {elapsed:.2f}s")
            
            return question
        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return "Tell me about your experience with the technologies mentioned in the job description."
    
    async def generate_streaming(self, state: OptimizedInterviewState) -> AsyncIterator[str]:
        """Generate question with streaming (for SSE endpoints)"""
        prompt = self.build_context_prompt(state)
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield "Tell me about your experience."


# ============================================================================
# Answer Evaluator (Async)
# ============================================================================

class AsyncAnswerEvaluator:
    """Evaluate answers asynchronously"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')  # Best stable model - fast with 1M token support
    
    async def evaluate(
        self, 
        question: str, 
        answer: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate candidate's answer"""
        start_time = time.time()
        
        prompt = f"""Evaluate this interview answer:

Question: {question}
Answer: {answer}

Rate (1-10) and provide brief feedback in JSON:
{{
    "clarity": <1-10>,
    "relevance": <1-10>,
    "depth": <1-10>,
    "feedback": "One sentence feedback"
}}"""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            result_text = response.text.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            
            evaluation = json.loads(result_text)
            
            # Log evaluation response
            logger.info("=" * 80)
            logger.info("🤖 GEMINI EVALUATION RESULT:")
            logger.info(f"Clarity: {evaluation.get('clarity', 'N/A')}/10")
            logger.info(f"Relevance: {evaluation.get('relevance', 'N/A')}/10")
            logger.info(f"Depth: {evaluation.get('depth', 'N/A')}/10")
            logger.info(f"Feedback: {evaluation.get('feedback', 'N/A')}")
            logger.info("=" * 80)
            
            elapsed = time.time() - start_time
            monitor.record_llm_call(elapsed, "gemini-2.5-flash", "evaluate_answer")
            logger.info(f"Evaluation completed in {elapsed:.2f}s")
            return evaluation
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {
                "clarity": 7,
                "relevance": 7,
                "depth": 7,
                "feedback": "Reasonable answer"
            }


# ============================================================================
# LangGraph Workflow
# ============================================================================

class OptimizedInterviewGraph:
    """Optimized LangGraph-based interview workflow"""
    
    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        self.question_generator = StreamingQuestionGenerator()
        self.answer_evaluator = AsyncAnswerEvaluator()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        workflow = StateGraph(OptimizedInterviewState)
        
        # Add nodes
        workflow.add_node("analyze_context", self._analyze_context_node)
        workflow.add_node("generate_question", self._generate_question_node)
        workflow.add_node("evaluate_answer", self._evaluate_answer_node)
        workflow.add_node("transition_stage", self._transition_stage_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_context")
        
        # Add edges
        workflow.add_edge("analyze_context", "generate_question")
        workflow.add_edge("generate_question", END)
        workflow.add_edge("evaluate_answer", "transition_stage")
        
        # Conditional edge for stage transition
        workflow.add_conditional_edges(
            "transition_stage",
            self._should_continue,
            {
                "continue": "generate_question",
                "end": END
            }
        )
        
        # Add memory checkpoint
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def _analyze_context_node(self, state: OptimizedInterviewState) -> OptimizedInterviewState:
        """Analyze CV/JD context (runs once per session)"""
        # Skip if already analyzed
        if state.get("cv_analysis"):
            return state
        
        # Analyze in parallel
        cv_task = self.context_analyzer.analyze_cv(state["cv_text"])
        jd_task = self.context_analyzer.analyze_jd(state["jd_text"])
        
        cv_analysis, jd_analysis = await asyncio.gather(cv_task, jd_task)
        
        # Update state with full analysis
        state["cv_analysis"] = cv_analysis  # Store complete analysis
        state["cv_summary"] = cv_analysis.get("summary", "")
        state["candidate_skills"] = cv_analysis.get("skills", [])
        state["jd_requirements"] = jd_analysis.get("must_have_skills", [])
        
        return state
    
    async def _generate_question_node(self, state: OptimizedInterviewState) -> OptimizedInterviewState:
        """Generate next interview question"""
        question = await self.question_generator.generate_question(state)
        
        # Add to messages
        message: InterviewMessage = {
            "role": "interviewer",
            "content": question,
            "timestamp": time.time(),
            "metadata": {"stage": state.get("stage", "intro")}
        }
        
        state.setdefault("messages", []).append(message)
        state["question_count"] = state.get("question_count", 0) + 1
        state["last_updated"] = time.time()
        
        # Cache state
        await cache.save_session(state["session_id"], state)
        
        return state
    
    async def _evaluate_answer_node(self, state: OptimizedInterviewState) -> OptimizedInterviewState:
        """Evaluate candidate's answer"""
        messages = state.get("messages", [])
        if len(messages) < 2:
            return state
        
        last_question = messages[-2]["content"]
        last_answer = messages[-1]["content"]
        
        evaluation = await self.answer_evaluator.evaluate(last_question, last_answer)
        
        # Add evaluation to last message metadata
        if messages:
            messages[-1]["metadata"] = messages[-1].get("metadata", {})
            messages[-1]["metadata"]["evaluation"] = evaluation
        
        return state
    
    async def _transition_stage_node(self, state: OptimizedInterviewState) -> OptimizedInterviewState:
        """Transition between interview stages"""
        question_count = state.get("question_count", 0)
        current_stage = state.get("stage", "intro")
        
        # Stage progression logic
        stages = ["intro", "technical", "behavioral", "closing"]
        stage_limits = {"intro": 1, "technical": 3, "behavioral": 2, "closing": 1}
        
        # Count questions in current stage
        messages = state.get("messages", [])
        stage_questions = sum(
            1 for m in messages 
            if m.get("role") == "interviewer" and m.get("metadata", {}).get("stage") == current_stage
        )
        
        if stage_questions >= stage_limits.get(current_stage, 2):
            try:
                current_idx = stages.index(current_stage)
                if current_idx + 1 < len(stages):
                    state["stage"] = stages[current_idx + 1]
                else:
                    state["completed"] = True
            except ValueError:
                state["completed"] = True
        
        return state
    
    def _should_continue(self, state: OptimizedInterviewState) -> str:
        """Determine if interview should continue"""
        if state.get("completed") or state.get("question_count", 0) >= 8:
            return "end"
        return "continue"


# ============================================================================
# Main Interview Engine
# ============================================================================

class OptimizedInterviewEngine:
    """Main optimized interview engine"""
    
    def __init__(self):
        self.graph_engine = OptimizedInterviewGraph()
        self.question_generator = StreamingQuestionGenerator()  # Add for streaming support
        self.sessions: Dict[str, OptimizedInterviewState] = {}
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        role: str,
        company: str,
        cv_text: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """Create new interview session"""
        # Check cache first
        cached_state = await cache.get_session(session_id)
        if cached_state:
            self.sessions[session_id] = cached_state
            return {
                "session_id": session_id,
                "status": "restored",
                "question": cached_state.get("messages", [])[-1].get("content") if cached_state.get("messages") else None
            }
        
        # Create new state
        state: OptimizedInterviewState = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "company": company,
            "cv_text": cv_text,
            "jd_text": jd_text,
            "cv_summary": None,
            "jd_requirements": None,
            "candidate_skills": None,
            "messages": [],
            "question_count": 0,
            "stage": "intro",
            "created_at": time.time(),
            "last_updated": time.time(),
            "completed": False,
            "response_times": []
        }
        
        # Run graph to get first question
        config = {"configurable": {"thread_id": session_id}}
        result = await self.graph_engine.graph.ainvoke(state, config)
        
        self.sessions[session_id] = result
        
        # Get first question
        first_question = result.get("messages", [])[-1].get("content") if result.get("messages") else "Tell me about yourself."
        
        return {
            "session_id": session_id,
            "status": "active",
            "question": first_question,
            "question_number": result.get("question_count", 1)
        }
    
    async def submit_answer(
        self,
        session_id: str,
        answer: str,
        voice_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit answer and get next question"""
        # Get or load session
        state = self.sessions.get(session_id)
        if not state:
            state = await cache.get_session(session_id)
            if state:
                self.sessions[session_id] = state
            else:
                raise ValueError(f"Session {session_id} not found")
        
        # Add candidate answer
        message: InterviewMessage = {
            "role": "candidate",
            "content": answer,
            "timestamp": time.time(),
            "metadata": {"voice_metrics": voice_metrics} if voice_metrics else {}
        }
        state.setdefault("messages", []).append(message)
        
        # Run evaluation and next question in parallel
        eval_task = self.graph_engine._evaluate_answer_node(state)
        transition_task = self.graph_engine._transition_stage_node(state)
        
        state = await eval_task
        state = await transition_task
        
        # Check if interview should continue
        should_continue = self.graph_engine._should_continue(state)
        
        if should_continue == "continue":
            # Generate next question
            state = await self.graph_engine._generate_question_node(state)
            
            next_question = state.get("messages", [])[-1].get("content")
            
            return {
                "session_id": session_id,
                "status": "active",
                "question": next_question,
                "question_number": state.get("question_count", 0),
                "evaluation": state.get("messages", [])[-2].get("metadata", {}).get("evaluation") if len(state.get("messages", [])) >= 2 else None
            }
        else:
            state["completed"] = True
            await cache.save_session(session_id, state)
            
            return {
                "session_id": session_id,
                "status": "completed",
                "message": "Interview completed",
                "total_questions": state.get("question_count", 0)
            }
    
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session state"""
        state = self.sessions.get(session_id)
        if not state:
            state = await cache.get_session(session_id)
        
        return state
    
    async def stream_question(self, session_id: str) -> AsyncIterator[str]:
        """Stream question generation (for SSE endpoints)"""
        state = self.sessions.get(session_id)
        if not state:
            yield "Error: Session not found"
            return
        
        async for chunk in self.question_generator.generate_streaming(state):
            yield chunk


# Global engine instance
optimized_engine = OptimizedInterviewEngine()
