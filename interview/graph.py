from typing import Dict, List, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from core.models import Session as SessionModel
from interview.question import get_question_generator
from interview.followup import get_followup_generator
from interview.evaluate.judge import get_llm_judge_evaluator


class InterviewGraph:
    """LangGraph state machine for interview orchestration"""
    
    def __init__(self):
        self.question_generator = get_question_generator()
        self.followup_generator = get_followup_generator()
        self.evaluator = get_llm_judge_evaluator()
        
        # Define state structure
        self.state_schema = {
            "session_id": str,
            "current_question_index": int,
            "questions": List[Dict[str, Any]],
            "answers": List[Dict[str, Any]],
            "evaluations": List[Dict[str, Any]],
            "follow_ups": List[Dict[str, Any]],
            "status": str,
            "plan": Dict[str, Any],
            "context": Dict[str, Any]
        }
        
        # Initialize the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        # Create the graph
        workflow = StateGraph(self.state_schema)
        
        # Add nodes
        workflow.add_node("plan", self._plan_interview)
        workflow.add_node("ask", self._ask_question)
        workflow.add_node("evaluate", self._evaluate_answer)
        workflow.add_node("follow_up", self._generate_follow_up)
        workflow.add_node("next", self._determine_next)
        
        # Add edges
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "ask")
        workflow.add_edge("ask", "evaluate")
        workflow.add_edge("evaluate", "follow_up")
        workflow.add_edge("follow_up", "next")
        workflow.add_edge("next", "ask")
        workflow.add_edge("next", END)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "next",
            self._should_continue,
            {
                "continue": "ask",
                "complete": END
            }
        )
        
        return workflow.compile()
    
    async def create_plan(self, session: SessionModel) -> Dict[str, Any]:
        """Create an interview plan for a session"""
        # Initialize state
        initial_state = {
            "session_id": str(session.id),
            "current_question_index": 0,
            "questions": [],
            "answers": [],
            "evaluations": [],
            "follow_ups": [],
            "status": "planning",
            "plan": {},
            "context": {
                "role": session.role,
                "industry": session.industry,
                "company": session.company,
                "cv_file_id": str(session.cv_file_id) if session.cv_file_id else None,
                "jd_file_id": str(session.jd_file_id) if session.jd_file_id else None
            }
        }
        
        # Run the planning phase
        result = await self.graph.ainvoke(initial_state)
        
        return result["plan"]
    
    async def _plan_interview(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Plan the interview structure and generate questions"""
        context = state["context"]
        
        # Generate questions based on session context
        questions = await self.question_generator.generate_questions(
            session_context=context,
            num_questions=10
        )
        
        # Create interview plan
        plan = {
            "total_questions": len(questions),
            "competency_breakdown": self._analyze_competencies(questions),
            "estimated_duration": len(questions) * 5,  # 5 minutes per question
            "focus_areas": self._identify_focus_areas(context),
            "question_sequence": questions
        }
        
        # Update state
        state["questions"] = questions
        state["plan"] = plan
        state["status"] = "active"
        
        return state
    
    async def _ask_question(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current question to ask"""
        current_index = state["current_question_index"]
        questions = state["questions"]
        
        if current_index < len(questions):
            current_question = questions[current_index]
            # The question is already available in state
            return state
        else:
            # No more questions
            state["status"] = "completed"
            return state
    
    async def _evaluate_answer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the current answer"""
        current_index = state["current_question_index"]
        questions = state["questions"]
        answers = state["answers"]
        
        if current_index < len(questions) and current_index < len(answers):
            current_question = questions[current_index]
            current_answer = answers[current_index]
            
            # Evaluate the answer
            evaluation = await self.evaluator.evaluate_answer(
                answer_text=current_answer["text"],
                question_meta=current_question,
                question_text=current_question["text"]
            )
            
            # Add evaluation to state
            state["evaluations"].append({
                "question_index": current_index,
                "question_id": current_question.get("id"),
                "answer_id": current_answer.get("id"),
                "evaluation": evaluation
            })
        
        return state
    
    async def _generate_follow_up(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate follow-up questions based on evaluation"""
        current_index = state["current_question_index"]
        evaluations = state["evaluations"]
        
        if current_index < len(evaluations):
            current_evaluation = evaluations[current_index]
            question_meta = state["questions"][current_index]
            
            # Generate follow-ups
            follow_ups = await self.followup_generator.generate_follow_ups(
                answer_evaluation=current_evaluation["evaluation"],
                question_meta=question_meta,
                max_follow_ups=2
            )
            
            # Add follow-ups to state
            state["follow_ups"].append({
                "question_index": current_index,
                "follow_ups": follow_ups
            })
        
        return state
    
    async def _determine_next(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the next step in the interview"""
        current_index = state["current_question_index"]
        questions = state["questions"]
        follow_ups = state["follow_ups"]
        
        # Check if we should ask follow-ups
        if (current_index < len(follow_ups) and 
            follow_ups[current_index]["follow_ups"] and
            state.get("should_follow_up", False)):
            
            # Ask follow-up question
            state["current_follow_up_index"] = state.get("current_follow_up_index", 0)
            return state
        
        # Move to next main question
        state["current_question_index"] += 1
        state["current_follow_up_index"] = 0  # Reset follow-up index
        
        return state
    
    def _should_continue(self, state: Dict[str, Any]) -> str:
        """Determine if the interview should continue"""
        current_index = state["current_question_index"]
        questions = state["questions"]
        
        if current_index >= len(questions):
            return "complete"
        else:
            return "continue"
    
    def _analyze_competencies(self, questions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze the competency breakdown of questions"""
        competency_counts = {}
        for question in questions:
            competency = question.get("competency", "general")
            competency_counts[competency] = competency_counts.get(competency, 0) + 1
        
        return competency_counts
    
    def _identify_focus_areas(self, context: Dict[str, Any]) -> List[str]:
        """Identify focus areas based on session context"""
        focus_areas = []
        
        if context.get("role"):
            if "senior" in context["role"].lower() or "lead" in context["role"].lower():
                focus_areas.append("leadership")
                focus_areas.append("strategic thinking")
            
            if "engineer" in context["role"].lower() or "developer" in context["role"].lower():
                focus_areas.append("technical depth")
                focus_areas.append("system design")
        
        if context.get("industry"):
            if context["industry"].lower() in ["technology", "software", "fintech"]:
                focus_areas.append("innovation")
                focus_areas.append("scalability")
        
        return focus_areas
    
    async def generate_report(self, session: SessionModel) -> Dict[str, Any]:
        """Generate a comprehensive interview report"""
        # This would typically be called after the interview is complete
        # For now, return a template report structure
        
        report = {
            "session_id": str(session.id),
            "overall_score": 0.0,
            "competency_breakdown": {},
            "strengths": [],
            "areas_for_improvement": [],
            "recommendations": [],
            "summary": f"Interview completed for {session.role} position at {session.company}",
            "total_questions": 0,
            "completion_date": session.created_at.isoformat() if session.created_at else None
        }
        
        return report
    
    async def run_interview_step(self, state: Dict[str, Any], step: str) -> Dict[str, Any]:
        """Run a specific step of the interview"""
        if step == "plan":
            return await self._plan_interview(state)
        elif step == "ask":
            return await self._ask_question(state)
        elif step == "evaluate":
            return await self._evaluate_answer(state)
        elif step == "follow_up":
            return await self._generate_follow_up(state)
        elif step == "next":
            return await self._determine_next(state)
        else:
            raise ValueError(f"Unknown step: {step}")
    
    def get_current_question(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the current question from the state"""
        current_index = state["current_question_index"]
        questions = state["questions"]
        
        if current_index < len(questions):
            return questions[current_index]
        return None
    
    def get_follow_ups(self, state: Dict[str, Any], question_index: int) -> List[Dict[str, Any]]:
        """Get follow-up questions for a specific question"""
        for follow_up_group in state["follow_ups"]:
            if follow_up_group["question_index"] == question_index:
                return follow_up_group["follow_ups"]
        return []
    
    def is_interview_complete(self, state: Dict[str, Any]) -> bool:
        """Check if the interview is complete"""
        return state["status"] == "completed" or state["current_question_index"] >= len(state["questions"])


# Factory function
def get_interview_graph() -> InterviewGraph:
    """Get an interview graph instance"""
    return InterviewGraph()
