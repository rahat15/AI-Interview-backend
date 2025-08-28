from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import uuid

from core.db import get_db
from core.models import User, Session as SessionModel, Question, Answer, Report
from core.schemas import (
    SessionCreate, 
    Session as SessionSchema, 
    NextQuestionResponse,
    AnswerCreate,
    Report as ReportSchema
)
from apps.api.deps.auth import get_current_active_user
from interview.graph import InterviewGraph
from apps.worker.jobs import enqueue_scoring_job

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionSchema)
async def create_session(
    session_in: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new interview session"""
    # Create session
    db_session = SessionModel(
        user_id=current_user.id,
        role=session_in.role,
        industry=session_in.industry,
        company=session_in.company,
        cv_file_id=session_in.cv_file_id,
        jd_file_id=session_in.jd_file_id,
        status="planning"
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Initialize interview plan using LangGraph
    try:
        interview_graph = InterviewGraph()
        plan = await interview_graph.create_plan(db_session)
        
        # Update session with plan
        db_session.plan_json = plan
        db_session.status = "active"
        db.commit()
        db.refresh(db_session)
        
    except Exception as e:
        # If planning fails, mark session as failed
        db_session.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create interview plan: {str(e)}"
        )
    
    return db_session


@router.get("/{session_id}", response_model=SessionSchema)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get session details"""
    db_session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return db_session


@router.get("/", response_model=List[SessionSchema])
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's sessions"""
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).order_by(SessionModel.created_at.desc()).all()
    
    return sessions


@router.get("/{session_id}/next-question", response_model=NextQuestionResponse)
async def get_next_question(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the next question for a session"""
    # Verify session ownership
    db_session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if db_session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active"
        )
    
    # Get next question
    next_question = db.query(Question).filter(
        Question.session_id == session_id,
        Question.order_index == db_session.current_question_index
    ).first()
    
    if not next_question:
        # Session completed
        db_session.status = "completed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No more questions - session completed"
        )
    
    return NextQuestionResponse(
        question_id=next_question.id,
        text=next_question.text,
        competency=next_question.competency,
        difficulty=next_question.difficulty,
        meta=next_question.meta
    )


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: uuid.UUID,
    answer_in: AnswerCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit an answer to a question"""
    # Verify session ownership
    db_session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if db_session.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active"
        )
    
    # Verify question belongs to session
    question = db.query(Question).filter(
        Question.id == answer_in.question_id,
        Question.session_id == session_id
    ).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in session"
        )
    
    # Create answer
    db_answer = Answer(
        session_id=session_id,
        question_id=answer_in.question_id,
        text=answer_in.text,
        audio_url=answer_in.audio_url
    )
    
    db.add(db_answer)
    db.commit()
    db.refresh(db_answer)
    
    # Enqueue scoring job
    background_tasks.add_task(
        enqueue_scoring_job,
        answer_id=str(db_answer.id)
    )
    
    # Move to next question
    db_session.current_question_index += 1
    db.commit()
    
    return {
        "message": "Answer submitted successfully",
        "answer_id": db_answer.id,
        "next_question_index": db_session.current_question_index
    }


@router.get("/{session_id}/report", response_model=ReportSchema)
async def get_session_report(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the session report"""
    # Verify session ownership
    db_session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get or generate report
    report = db.query(Report).filter(Report.session_id == session_id).first()
    
    if not report:
        # Generate report if it doesn't exist
        try:
            interview_graph = InterviewGraph()
            report_data = await interview_graph.generate_report(db_session)
            
            report = Report(
                session_id=session_id,
                json=report_data,
                summary=report_data.get("summary", ""),
                overall_score=report_data.get("overall_score", 0.0),
                strengths=report_data.get("strengths", []),
                areas_for_improvement=report_data.get("areas_for_improvement", []),
                recommendations=report_data.get("recommendations", [])
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate report: {str(e)}"
            )
    
    return report


@router.delete("/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a session"""
    db_session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    db.delete(db_session)
    db.commit()
    
    return {"message": "Session deleted successfully"}
