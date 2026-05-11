from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from typing import List, Optional
from app.database import get_db
from app.models import (
    User, Internship, Company, Proposal, Agreement,
    Logbook, Evaluation, EvaluationRule, Competency, CompetencyProfile, Feedback
)
from app.schemas import (
    InternshipCreate, InternshipResponse, InternshipUpdate,
    InternshipListResponse, ProposalResponse, AgreementResponse,
    LogbookCreate, LogbookResponse, LogbookUpdate, LogbookWeekStatus,
    EvaluationCreate, EvaluationResponse, EvaluationUpdate,
    EvaluationWithScoreResponse, EvaluationRuleResponse, EvaluationRuleUpdate,
    FeedbackCreate, FeedbackResponse,
    DashboardStats, AgreementStatusItem, FinalReportItem,
    ProposalUpdate, AgreementUpdate
)
from app.auth import (
    get_current_active_user,
    require_student, require_committee, require_committee_or_admin,
    require_teacher, require_mentor, require_any_staff
)
import os
import shutil
from datetime import datetime, UTC

router = APIRouter(prefix="/internships", tags=["internships"])

UPLOAD_DIR = "uploads"
AGREEMENTS_DIR = os.path.join(UPLOAD_DIR, "agreements")

os.makedirs(AGREEMENTS_DIR, exist_ok=True)


def get_active_competency_profile(db: Session) -> Optional[CompetencyProfile]:
    """Get the currently active competency profile"""
    return db.query(CompetencyProfile).filter(CompetencyProfile.active == True).first()


def calculate_evaluation_score(db: Session, evaluation: Evaluation) -> dict:
    """Calculate weighted score for an evaluation"""
    rules = db.query(EvaluationRule).options(
        joinedload(EvaluationRule.competency)
    ).filter(EvaluationRule.evaluation_id == evaluation.id).all()

    if not rules:
        return {
            "total_weight": 0,
            "achieved_weight": 0,
            "weighted_score": None
        }

    total_weight = 0
    achieved_weight = 0
    all_scored = True

    for rule in rules:
        competency = rule.competency
        if competency:
            weight = competency.weight
            total_weight += weight
            if rule.score is not None:
                # Score is 1-5, normalize to 0-1 then multiply by weight
                achieved_weight += (rule.score / 5.0) * weight
            else:
                all_scored = False

    weighted_score = (achieved_weight / total_weight * 100) if total_weight > 0 and all_scored else None

    return {
        "total_weight": total_weight,
        "achieved_weight": achieved_weight,
        "weighted_score": weighted_score
    }


# ============================================================================
# Internship CRUD
# ============================================================================

@router.get("", response_model=List[InternshipListResponse])
def list_internships(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List internships - filtered by role"""
    query = db.query(Internship)
    
    # Filter based on role
    if current_user.role == "student":
        query = query.filter(Internship.student_id == current_user.id)
    elif current_user.role == "mentor":
        query = query.filter(Internship.mentor_id == current_user.id)
    elif current_user.role == "teacher":
        query = query.filter(Internship.teacher_id == current_user.id)
    # Committee and admin see all
    
    if status:
        query = query.filter(Internship.status == status)
    
    internships = query.order_by(Internship.created_at.desc()).all()
    return internships


@router.post("", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
def create_internship(
    data: InternshipCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """US-01: Student submits a new internship proposal
    
    Creates:
    1. A Company (if it doesn't exist, or we could link to existing)
    2. An Internship record
    3. A Proposal record with the description
    """
    # Create or find company
    company = Company(
        name=data.company_name,
        address=data.company_address,
        sector=data.company_sector,
        contact_person=data.contact_person,
        contact_email=data.contact_email
    )
    db.add(company)
    db.flush()  # Get company ID
    
    # Create internship
    internship = Internship(
        student_id=current_user.id,
        company_id=company.id,
        start_date=data.start_date,
        end_date=data.end_date,
        status="Ingediend"
    )
    db.add(internship)
    db.flush()  # Get internship ID
    
    # Create proposal
    proposal = Proposal(
        internship_id=internship.id,
        description=data.description,
        status="Ingediend"
    )
    db.add(proposal)
    
    db.commit()
    db.refresh(internship)
    
    return internship


@router.get("/{internship_id}", response_model=InternshipResponse)
def get_internship(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed internship information"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check permissions
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this internship")
    if current_user.role == "mentor" and internship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this internship")
    if current_user.role == "teacher" and internship.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this internship")
    
    return internship


@router.patch("/{internship_id}", response_model=InternshipResponse)
def update_internship(
    internship_id: int,
    update: InternshipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    """Update internship details - staff only (teacher, committee, admin)"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if update.teacher_id is not None:
        internship.teacher_id = update.teacher_id
    if update.mentor_id is not None:
        internship.mentor_id = update.mentor_id
    if update.company_id is not None:
        internship.company_id = update.company_id
    if update.start_date is not None:
        internship.start_date = update.start_date
    if update.end_date is not None:
        internship.end_date = update.end_date
    if update.status is not None:
        internship.status = update.status
    
    db.commit()
    db.refresh(internship)
    
    return internship


# ============================================================================
# Proposal (Stagevoorstel) Endpoints
# ============================================================================

@router.get("/{internship_id}/proposal", response_model=ProposalResponse)
def get_proposal(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """US-02: Get proposal status"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if not internship.proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Check permissions - committee and admin can view all proposals
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "mentor" and internship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher" and internship.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Committee and admin have implicit access
    
    return internship.proposal


@router.patch("/{internship_id}/proposal", response_model=ProposalResponse)
def update_proposal(
    internship_id: int,
    update_data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_committee)
):
    """US-11, US-12: Committee evaluates proposal
    
    Status transitions:
    - Goedgekeurd: Proposal approved, student can upload agreement
    - Afgekeurd: Proposal rejected
    - Aanpassingen Vereist: Feedback required, student must revise
    """
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if not internship.proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    proposal = internship.proposal
    new_status = update_data.status
    
    # Validate status
    valid_statuses = ["Goedgekeurd", "Afgekeurd", "Aanpassingen Vereist"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    
    # Aanpassingen Vereist requires feedback
    if new_status == "Aanpassingen Vereist" and not update_data.feedback:
        raise HTTPException(status_code=400, detail="Feedback is required when requesting changes")
    
    # Update proposal
    proposal.status = new_status
    if update_data.feedback:
        proposal.feedback = update_data.feedback
    
    # Update internship status to match
    internship.status = new_status
    
    db.commit()
    db.refresh(proposal)
    
    return proposal


@router.post("/{internship_id}/resubmit", response_model=ProposalResponse)
def resubmit_proposal(
    internship_id: int,
    new_description: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """Student resubmits proposal after changes requested"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not internship.proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    if internship.proposal.status != "Aanpassingen Vereist":
        raise HTTPException(status_code=400, detail="Can only resubmit when changes are requested")
    
    proposal = internship.proposal
    proposal.description = new_description
    proposal.status = "Ingediend"
    proposal.submitted_at = datetime.now(UTC)
    
    internship.status = "Ingediend"
    
    db.commit()
    db.refresh(proposal)
    
    return proposal


# ============================================================================
# Agreement (Overeenkomst) Endpoints
# ============================================================================

@router.post("/{internship_id}/agreement", response_model=AgreementResponse)
def upload_agreement(
    internship_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """US-04: Student uploads internship agreement (PDF only)
    
    Only allowed when proposal is approved (Goedgekeurd)
    """
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
    filepath = os.path.join(AGREEMENTS_DIR, filename)
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    
    # Create or update agreement record
    if internship.agreement:
        agreement = internship.agreement
        agreement.file_path = filepath
        agreement.status = "Ingediend"
        agreement.uploaded_at = datetime.now(UTC)
    else:
        agreement = Agreement(
            internship_id=internship_id,
            file_path=filepath,
            status="Ingediend",
            uploaded_at=datetime.now(UTC)
        )
        db.add(agreement)
    
    # Update internship status
    internship.status = "Overeenkomst Ingediend"
    
    db.commit()
    db.refresh(agreement)
    
    return agreement


@router.get("/{internship_id}/agreement", response_model=AgreementResponse)
def get_agreement(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get agreement details"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check permissions - committee and admin can view all agreements
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "mentor" and internship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher" and internship.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Committee and admin have implicit access
    
    if not internship.agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    return internship.agreement


@router.patch("/{internship_id}/agreement", response_model=AgreementResponse)
def validate_agreement(
    internship_id: int,
    update: AgreementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_committee_or_admin)
):
    """US-13, US-26: Committee/admin validates agreement
    
    Status: Gevalideerd or Onvolledig
    """
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if not internship.agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    
    if update.status not in ["Gevalideerd", "Onvolledig"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    agreement = internship.agreement
    if update.insurance_verified is not None:
        agreement.insurance_verified = update.insurance_verified
    if update.status is not None:
        agreement.status = update.status
    
    if agreement.status == "Gevalideerd":
        agreement.validated_at = datetime.now(UTC)
        internship.status = "Lopend"
    
    db.commit()
    db.refresh(agreement)
    
    return agreement


# ============================================================================
# Logbook Endpoints
# ============================================================================

@router.get("/{internship_id}/logbooks", response_model=List[LogbookResponse])
def list_logbooks(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """US-05, US-08, US-14, US-15, US-21: List logbooks for an internship"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check permissions - committee and admin can view all logbooks
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "mentor" and internship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher" and internship.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Committee and admin have implicit access
    
    logbooks = db.query(Logbook).filter(Logbook.internship_id == internship_id).all()
    return logbooks


@router.get("/{internship_id}/logbooks/weeks", response_model=List[LogbookWeekStatus])
def get_week_overview(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """US-05, US-08: Get status of all weeks for the internship period"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check permissions - committee and admin can view all week overviews
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "mentor" and internship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher" and internship.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Committee and admin have implicit access
    
    if not internship.start_date or not internship.end_date:
        raise HTTPException(status_code=400, detail="Internship dates not set")
    
    # Calculate total weeks (handles year boundaries correctly)
    total_days = (internship.end_date - internship.start_date).days
    total_weeks = (total_days // 7) + 1
    
    # Get existing logbooks
    logbooks = db.query(Logbook).filter(Logbook.internship_id == internship_id).all()
    logbook_map = {lb.week_number: lb for lb in logbooks}
    
    result = []
    for week in range(1, total_weeks + 1):
        if week in logbook_map:
            lb = logbook_map[week]
            result.append(LogbookWeekStatus(
                week_number=week,
                logbook_id=lb.id,
                status=lb.status,
                mentor_validated=lb.mentor_validated
            ))
        else:
            result.append(LogbookWeekStatus(
                week_number=week,
                logbook_id=None,
                status="missing",
                mentor_validated=False
            ))
    
    return result


@router.post("/{internship_id}/logbooks", response_model=LogbookResponse)
def create_logbook(
    internship_id: int,
    data: LogbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student)
):
    """US-05: Create a new logbook entry for a week"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    if internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate week_number (must be positive, no upper limit to support long internships)
    if data.week_number < 1:
        raise HTTPException(status_code=400, detail="Week number must be at least 1")
    
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
    """US-05: Update logbook - students edit, mentors validate"""
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
        if internship.mentor_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if any([update.tasks, update.reflection, update.issues, update.status]):
            raise HTTPException(status_code=403, detail="Mentors can only validate logbooks")
        if update.mentor_validated is not None:
            logbook.mentor_validated = update.mentor_validated
    
    # Teachers can edit and validate logbooks for their assigned internships
    if current_user.role == "teacher":
        if internship.teacher_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields (students and teachers)
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


# ============================================================================
# Evaluation Endpoints
# ============================================================================

@router.get("/{internship_id}/evaluations", response_model=List[EvaluationResponse])
def list_evaluations(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """US-09, US-18: List evaluations for an internship"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check permissions
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "mentor" and internship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher" and internship.teacher_id != current_user.id:
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
    """US-17, US-18: Teacher creates an evaluation (tussentijds or final)"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Only allow evaluations for ongoing or completed internships
    if internship.status not in ["Lopend", "Afgerond", "Overeenkomst Ingediend"]:
        raise HTTPException(status_code=400, detail="Can only evaluate ongoing or completed internships")
    
    # Check if final evaluation already exists
    if data.eval_type == "final":
        existing_final = db.query(Evaluation).filter(
            Evaluation.internship_id == internship_id,
            Evaluation.eval_type == "final"
        ).first()
        if existing_final:
            raise HTTPException(status_code=400, detail="Final evaluation already exists")
    
    evaluation = Evaluation(
        internship_id=internship_id,
        evaluator_id=current_user.id,
        eval_type=data.eval_type,
        status="concept",
        comments=data.comments,
        finalized=False
    )
    
    db.add(evaluation)
    db.flush()  # Get evaluation ID
    
    # Create empty evaluation rules for all active competencies
    profile = get_active_competency_profile(db)
    if not profile:
        raise HTTPException(status_code=400, detail="No active competency profile found")
    
    competencies = db.query(Competency).filter(
        Competency.profile_id == profile.id,
        Competency.active == True
    ).all()
    
    for comp in competencies:
        rule = EvaluationRule(
            evaluation_id=evaluation.id,
            competency_id=comp.id,
            score=None,
            student_description=None,
            evaluator_feedback=None
        )
        db.add(rule)
    
    db.commit()
    db.refresh(evaluation)
    
    return evaluation


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationWithScoreResponse)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get evaluation with calculated score"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    internship = evaluation.internship
    
    # Check permissions
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "mentor" and internship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher" and internship.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Calculate score
    score_data = calculate_evaluation_score(db, evaluation)
    
    return EvaluationWithScoreResponse(
        **EvaluationResponse.model_validate(evaluation).model_dump(),
        **score_data
    )


@router.patch("/evaluations/{evaluation_id}/rules/{rule_id}", response_model=EvaluationRuleResponse)
def update_evaluation_rule(
    evaluation_id: int,
    rule_id: int,
    update: EvaluationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    """US-06, US-16, US-18, US-23: Update an evaluation rule
    
    Student adds description of what they learned
    Teacher/mentor adds score and feedback
    """
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    if evaluation.finalized:
        raise HTTPException(status_code=400, detail="Cannot update finalized evaluation")
    
    rule = db.query(EvaluationRule).filter(
        EvaluationRule.id == rule_id,
        EvaluationRule.evaluation_id == evaluation_id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Evaluation rule not found")
    
    internship = evaluation.internship
    
    # Students can only update their own description
    if current_user.role == "student":
        if internship.student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if update.student_description is not None:
            rule.student_description = update.student_description
    
    # Teachers and mentors can update scores and feedback
    if current_user.role in ["teacher", "mentor", "committee", "admin"]:
        if current_user.role in ["teacher", "mentor"]:
            if internship.teacher_id != current_user.id and internship.mentor_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized for this internship")
        
        if update.score is not None:
            if update.score < 1 or update.score > 5:
                raise HTTPException(status_code=400, detail="Score must be between 1 and 5")
            rule.score = update.score
        if update.evaluator_feedback is not None:
            rule.evaluator_feedback = update.evaluator_feedback
        if update.student_description is not None:
            rule.student_description = update.student_description
    
    db.commit()
    db.refresh(rule)
    
    return rule


@router.post("/evaluations/{evaluation_id}/finalize", response_model=EvaluationWithScoreResponse)
def finalize_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """US-18: Finalize an evaluation - cannot be modified after"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    if evaluation.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the evaluator can finalize")
    
    if evaluation.finalized:
        raise HTTPException(status_code=400, detail="Evaluation already finalized")
    
    # Check all rules have scores
    rules = db.query(EvaluationRule).filter(EvaluationRule.evaluation_id == evaluation_id).all()
    missing_scores = [r.id for r in rules if r.score is None]
    
    if missing_scores:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot finalize: missing scores for competencies: {missing_scores}"
        )
    
    evaluation.finalized = True
    evaluation.status = "afgerond"
    evaluation.finalized_at = datetime.now(UTC)
    
    db.commit()
    db.refresh(evaluation)
    
    # Calculate final score
    score_data = calculate_evaluation_score(db, evaluation)
    
    return EvaluationWithScoreResponse(
        **EvaluationResponse.model_validate(evaluation).model_dump(),
        **score_data
    )


# ============================================================================
# Feedback Endpoints
# ============================================================================

@router.get("/{internship_id}/feedback", response_model=List[FeedbackResponse])
def list_feedback(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """US-03, US-07: List feedback for an internship"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Check permissions - committee and admin can view all feedback
    if current_user.role == "student" and internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "mentor" and internship.mentor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.role == "teacher" and internship.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Committee and admin have implicit access
    
    feedbacks = db.query(Feedback).filter(Feedback.internship_id == internship_id).all()
    return feedbacks


@router.post("/{internship_id}/feedback", response_model=FeedbackResponse)
def create_feedback(
    internship_id: int,
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    """US-03, US-07, US-12, US-16, US-20: Create feedback"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Validate that to_user_id is a participant in this internship
    valid_recipients = [internship.student_id, internship.teacher_id, internship.mentor_id]
    if data.to_user_id not in valid_recipients:
        raise HTTPException(
            status_code=400,
            detail="Recipient must be a participant in this internship (student, teacher, or mentor)"
        )
    
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


# ============================================================================
# Dashboard and Reporting
# ============================================================================

@router.get("/stats/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get dashboard statistics - filtered by role"""
    # Build base query based on role
    base_query = db.query(Internship)
    
    if current_user.role == "student":
        base_query = base_query.filter(Internship.student_id == current_user.id)
    elif current_user.role == "mentor":
        base_query = base_query.filter(Internship.mentor_id == current_user.id)
    elif current_user.role == "teacher":
        base_query = base_query.filter(Internship.teacher_id == current_user.id)
    # Committee and admin see all
    
    total = base_query.count()
    pending = base_query.filter(Internship.status.in_(["Ingediend", "In Beoordeling"])).count()
    approved = base_query.filter(Internship.status == "Goedgekeurd").count()
    rejected = base_query.filter(Internship.status == "Afgekeurd").count()
    ongoing = base_query.filter(Internship.status.in_(["Lopend", "Overeenkomst Ingediend"])).count()
    
    # Agreement counts for filtered internships
    internship_ids = [i.id for i in base_query.all()]
    if internship_ids:
        agreements_received = db.query(Agreement).filter(Agreement.internship_id.in_(internship_ids)).count()
        agreements_validated = db.query(Agreement).filter(
            Agreement.internship_id.in_(internship_ids),
            Agreement.status == "Gevalideerd"
        ).count()
    else:
        agreements_received = 0
        agreements_validated = 0
    
    return DashboardStats(
        total_internships=total,
        pending_approval=pending,
        approved=approved,
        rejected=rejected,
        ongoing=ongoing,
        agreements_received=agreements_received,
        agreements_pending=agreements_received - agreements_validated
    )


@router.get("/reports/agreements", response_model=List[AgreementStatusItem])
def get_agreement_status_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    """US-26: Admin view of agreement status for all students"""
    # Build query with role-based filtering
    query = db.query(Internship).filter(
        Internship.status.in_(["Goedgekeurd", "Overeenkomst Ingediend", "Lopend", "Afgerond"])
    )
    
    # Apply role-based filtering
    if current_user.role == "mentor":
        query = query.filter(Internship.mentor_id == current_user.id)
    elif current_user.role == "teacher":
        query = query.filter(Internship.teacher_id == current_user.id)
    # Committee and admin see all
    
    internships = query.all()
    
    result = []
    for internship in internships:
        agreement_status = "Niet Ingediend"
        uploaded_at = None
        
        if internship.agreement:
            agreement_status = internship.agreement.status
            uploaded_at = internship.agreement.uploaded_at
        
        result.append(AgreementStatusItem(
            internship_id=internship.id,
            student=UserResponse.model_validate(internship.student),
            status=internship.status,
            agreement_status=agreement_status,
            uploaded_at=uploaded_at
        ))
    
    return result


@router.get("/{internship_id}/final-report", response_model=FinalReportItem)
def get_final_report(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    """US-19: Generate final report for a student"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    # Calculate logbook stats (handles year boundaries correctly)
    total_weeks = 0
    if internship.start_date and internship.end_date:
        total_days = (internship.end_date - internship.start_date).days
        total_weeks = (total_days // 7) + 1
    
    submitted_logbooks = db.query(Logbook).filter(
        Logbook.internship_id == internship_id,
        Logbook.status == "submitted"
    ).count()
    
    # Get final evaluation
    final_eval = db.query(Evaluation).filter(
        Evaluation.internship_id == internship_id,
        Evaluation.eval_type == "final",
        Evaluation.finalized == True
    ).first()
    
    final_eval_response = None
    weighted_score = None
    
    if final_eval:
        score_data = calculate_evaluation_score(db, final_eval)
        final_eval_response = EvaluationWithScoreResponse(
            **EvaluationResponse.model_validate(final_eval).model_dump(),
            **score_data
        )
        weighted_score = score_data["weighted_score"]
    
    return FinalReportItem(
        internship_id=internship.id,
        student=UserResponse.model_validate(internship.student),
        company_name=internship.company.name if internship.company else None,
        start_date=internship.start_date,
        end_date=internship.end_date,
        proposal_status=internship.proposal.status if internship.proposal else "Onbekend",
        proposal_submitted_at=internship.proposal.submitted_at if internship.proposal else None,
        agreement_status=internship.agreement.status if internship.agreement else "Niet Ingediend",
        agreement_uploaded_at=internship.agreement.uploaded_at if internship.agreement else None,
        total_weeks=total_weeks,
        submitted_logbooks=submitted_logbooks,
        missing_logbooks=max(0, total_weeks - submitted_logbooks),
        final_evaluation=final_eval_response,
        weighted_final_score=weighted_score
    )
