from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User, Internship, Logbook, Evaluation, Feedback
from app.schemas import (
    InternshipCreate, InternshipResponse, InternshipUpdateStatus,
    LogbookCreate, LogbookResponse, LogbookUpdate,
    EvaluationCreate, EvaluationResponse, EvaluationUpdate, EvaluationFinalize,
    FeedbackCreate, FeedbackResponse,
    DashboardStats
)
from app.auth import (
    get_current_active_user,
    require_student, require_committee,
    require_teacher, require_any_staff
)
import os
import shutil
import json
from datetime import datetime, UTC

router = APIRouter(prefix="/internships", tags=["internships"])

UPLOAD_DIR = "uploads/agreements"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Valid status transitions
STATUS_FLOW = {
    "Ingediend": ["In Beoordeling"],
    "In Beoordeling": ["Goedgekeurd", "Afgekeurd", "Aanpassingen Vereist"],
    "Aanpassingen Vereist": ["Ingediend"],
    "Goedgekeurd": ["Overeenkomst Ingediend"],
    "Overeenkomst Ingediend": ["Lopend"],
    "Lopend": ["Afgerond"],
    "Afgekeurd": [],
    "Afgerond": []
}


@router.get("", response_model=List[InternshipResponse])
def list_internships(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Internship)
    
    # Filter based on role
    if current_user.role == "student":
        query = query.filter(Internship.student_id == current_user.id)
    elif current_user.role == "mentor":
        # Mentors see internships where they are assigned (simplified)
        query = query.filter(Internship.status.in_(["Lopend", "Afgerond"]))
    # Committee, teacher, admin see all
    
    if status:
        query = query.filter(Internship.status == status)
    
    internships = query.order_by(Internship.created_at.desc()).all()
    return internships


@router.post("", response_model=InternshipResponse)
def create_internship(
    data: InternshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    internship = Internship(
        student_id=current_user.id,
        company_name=data.company_name,
        contact_person=data.contact_person,
        contact_email=data.contact_email,
        start_date=data.start_date,
        end_date=data.end_date,
        description=data.description,
        status="Ingediend"
    )
    
    db.add(internship)
    db.commit()
    db.refresh(internship)
    
    return internship


@router.get("/{internship_id}", response_model=InternshipResponse)
def get_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check permissions
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this internship")
    
    return internship


@router.patch("/{internship_id}/status", response_model=InternshipResponse)
def update_status(
    internship_id: int,
    update: InternshipUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_committee)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Validate new status is a known status
    new_status = update.status
    valid_statuses = set(STATUS_FLOW.keys()) | {s for targets in STATUS_FLOW.values() for s in targets}
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: '{new_status}'")
    
    # Validate status transition
    current_status = internship.status
    if new_status not in STATUS_FLOW.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from '{current_status}' to '{new_status}'"
        )
    
    # Special rule: to "Lopend" requires agreement
    if new_status == "Lopend" and not internship.agreement_uploaded:
        raise HTTPException(
            status_code=400,
            detail="Cannot transition to 'Lopend' without signed agreement"
        )
    
    internship.status = new_status
    if update.feedback:
        internship.committee_feedback = update.feedback
    
    db.commit()
    db.refresh(internship)
    
    return internship


@router.post("/{internship_id}/agreement")
def upload_agreement(
    internship_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if internship.status != "Goedgekeurd":
        raise HTTPException(
            status_code=400,
            detail="Can only upload agreement after proposal is approved"
        )
    
    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save file
    filename = f"agreement_{internship_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    
    internship.agreement_uploaded = True
    internship.agreement_filename = filename
    internship.status = "Overeenkomst Ingediend"
    
    db.commit()
    db.refresh(internship)
    
    return {"message": "Agreement uploaded successfully", "filename": filename}


@router.get("/{internship_id}/logbooks", response_model=List[LogbookResponse])
def list_logbooks(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check permissions
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    logbooks = db.query(Logbook).filter(Logbook.internship_id == internship_id).all()
    return logbooks


@router.post("/{internship_id}/logbooks", response_model=LogbookResponse)
def create_logbook(
    internship_id: int,
    data: LogbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate week_number first (before DB query)
    if data.week_number < 1 or data.week_number > 52:
        raise HTTPException(status_code=400, detail="Week number must be between 1 and 52")
    
    # Check for existing logbook for this week
    existing = db.query(Logbook).filter(
        Logbook.internship_id == internship_id,
        Logbook.week_number == data.week_number
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Logbook for week {data.week_number} already exists")
    
    logbook = Logbook(
        internship_id=internship_id,
        week_number=data.week_number,
        tasks=data.tasks,
        reflection=data.reflection,
        issues=data.issues,
        status="draft"
    )
    
    db.add(logbook)
    db.commit()
    db.refresh(logbook)
    
    return logbook


@router.patch("/logbooks/{logbook_id}", response_model=LogbookResponse)
def update_logbook(
    logbook_id: int,
    update: LogbookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    logbook = db.query(Logbook).filter(Logbook.id == logbook_id).first()
    if not logbook:
        raise HTTPException(status_code=404, detail="Logbook not found")
    
    internship = logbook.internship
    
    # Students can only update their own logbooks
    if current_user.role == "student":
        if internship.student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Students can't change validation status
        if update.mentor_validated is not None:
            raise HTTPException(status_code=403, detail="Cannot change mentor validation")
    
    # Mentors can only validate - check first before any changes
    if current_user.role == "mentor":
        if any([update.tasks, update.reflection, update.issues, update.status]):
            raise HTTPException(status_code=403, detail="Mentors can only validate logbooks")
        if update.mentor_validated is not None:
            logbook.mentor_validated = update.mentor_validated
    
    # Update fields
    if update.tasks is not None:
        logbook.tasks = update.tasks
    if update.reflection is not None:
        logbook.reflection = update.reflection
    if update.issues is not None:
        logbook.issues = update.issues
    if update.status is not None and current_user.role != "mentor":
        logbook.status = update.status
        if update.status == "submitted":
            logbook.submitted_at = datetime.now(UTC)
    
    db.commit()
    db.refresh(logbook)
    
    return logbook


@router.get("/{internship_id}/evaluations", response_model=List[EvaluationResponse])
def list_evaluations(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    evaluations = db.query(Evaluation).filter(Evaluation.internship_id == internship_id).all()
    return evaluations


@router.post("/{internship_id}/evaluations", response_model=EvaluationResponse)
def create_evaluation(
    internship_id: int,
    data: EvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    evaluation = Evaluation(
        internship_id=internship_id,
        evaluator_id=current_user.id,
        type=data.type,
        scores="{}",
        comments=data.comments,
        finalized=False
    )
    
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    return evaluation


@router.patch("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def update_evaluation(
    evaluation_id: int,
    update: EvaluationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Update evaluation scores and comments (only if not finalized)."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Only the evaluator who created it can update
    if evaluation.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this evaluation")
    
    # Can't update if already finalized
    if evaluation.finalized:
        raise HTTPException(status_code=400, detail="Cannot update finalized evaluation")
    
    if update.scores is not None:
        evaluation.scores = json.dumps(update.scores)
    if update.comments is not None:
        evaluation.comments = update.comments
    
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.post("/evaluations/{evaluation_id}/finalize", response_model=EvaluationResponse)
def finalize_evaluation(
    evaluation_id: int,
    data: EvaluationFinalize,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Finalize an evaluation with scores."""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    # Only the evaluator who created it can finalize
    if evaluation.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to finalize this evaluation")
    
    # Can't finalize if already finalized
    if evaluation.finalized:
        raise HTTPException(status_code=400, detail="Evaluation already finalized")
    
    evaluation.scores = json.dumps(data.scores)
    evaluation.finalized = True
    evaluation.finalized_at = datetime.now(UTC)
    
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.get("/{internship_id}/feedback", response_model=List[FeedbackResponse])
def list_feedback(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    feedbacks = db.query(Feedback).filter(Feedback.internship_id == internship_id).all()
    return feedbacks


@router.post("/{internship_id}/feedback", response_model=FeedbackResponse)
def create_feedback(
    internship_id: int,
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    feedback = Feedback(
        internship_id=internship_id,
        from_user_id=current_user.id,
        to_user_id=data.to_user_id,
        message=data.message
    )
    
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return feedback


@router.get("/stats/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    total = db.query(Internship).count()
    pending = db.query(Internship).filter(Internship.status.in_(["Ingediend", "In Beoordeling"])).count()
    approved = db.query(Internship).filter(Internship.status == "Goedgekeurd").count()
    rejected = db.query(Internship).filter(Internship.status == "Afgekeurd").count()
    ongoing = db.query(Internship).filter(Internship.status.in_(["Lopend", "Overeenkomst Ingediend"])).count()
    agreements_received = db.query(Internship).filter(Internship.agreement_uploaded == True).count()
    
    return DashboardStats(
        total_internships=total,
        pending_approval=pending,
        approved=approved,
        rejected=rejected,
        ongoing=ongoing,
        agreements_received=agreements_received,
        agreements_pending=max(0, approved - agreements_received)
    )