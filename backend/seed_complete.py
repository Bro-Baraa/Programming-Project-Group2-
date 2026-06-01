#!/usr/bin/env python3
"""
Comprehensive database seeding for the Stage Monitoring Tool.
Creates realistic test data for all models: users, companies, internships,
proposals, agreements, logbooks, evaluations, and feedback.

Usage:
    python seed_complete.py

The script is idempotent - safe to run multiple times.
"""

import sys
import os
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Base, User, Company, Internship, Proposal, Agreement, Logbook, Evaluation, EvaluationRule, Feedback, CompetencyProfile, Competency
import bcrypt

# Password hashing (compatible with app.auth's get_password_hash)
def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Create tables if they don't exist
print("[INIT] Dropping and recreating database tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("[OK] Tables ready!")

# Initialize database session
db = SessionLocal()

def get_or_create_user(db: Session, email: str, defaults: dict) -> User:
    """Get existing user or create a new one."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    
    user = User(
        email=email,
        password_hash=get_password_hash(defaults["password"]),
        first_name=defaults["first_name"],
        last_name=defaults["last_name"],
        role=defaults["role"],
        is_active=True
    )
    db.add(user)
    db.flush()
    return user

def get_or_create_company(db: Session, name: str, defaults: dict) -> Company:
    """Get existing company or create a new one."""
    company = db.query(Company).filter(Company.name == name).first()
    if company:
        return company
    
    company = Company(
        name=name,
        address=defaults.get("address"),
        sector=defaults.get("sector"),
        contact_person=defaults.get("contact_person"),
        contact_email=defaults.get("contact_email"),
        mentor_id=defaults.get("mentor_id")
    )
    db.add(company)
    db.flush()
    return company

def get_or_create_internship(db: Session, student_id: int, company_id: int, defaults: dict) -> Internship:
    """Get existing internship or create a new one."""
    internship = db.query(Internship).filter(
        Internship.student_id == student_id,
        Internship.company_id == company_id
    ).first()
    if internship:
        return internship
    
    internship = Internship(
        student_id=student_id,
        teacher_id=defaults.get("teacher_id"),
        mentor_id=defaults.get("mentor_id"),
        company_id=company_id,
        start_date=defaults.get("start_date"),
        end_date=defaults.get("end_date"),
        status=defaults.get("status", "Ingediend")
    )
    db.add(internship)
    db.flush()
    return internship

def get_or_create_proposal(db: Session, internship_id: int, defaults: dict) -> Proposal:
    """Get existing proposal or create a new one."""
    proposal = db.query(Proposal).filter(Proposal.internship_id == internship_id).first()
    if proposal:
        return proposal
    
    proposal = Proposal(
        internship_id=internship_id,
        description=defaults.get("description", ""),
        status=defaults.get("status", "Ingediend"),
        feedback=defaults.get("feedback")
    )
    db.add(proposal)
    db.flush()
    return proposal

def get_or_create_agreement(db: Session, internship_id: int, defaults: dict) -> Agreement:
    """Get existing agreement or create a new one."""
    agreement = db.query(Agreement).filter(Agreement.internship_id == internship_id).first()
    if agreement:
        return agreement
    
    agreement = Agreement(
        internship_id=internship_id,
        file_path=defaults.get("file_path"),
        insurance_verified=defaults.get("insurance_verified", False),
        status=defaults.get("status", "Niet Ingediend"),
        uploaded_at=defaults.get("uploaded_at"),
        validated_at=defaults.get("validated_at")
    )
    db.add(agreement)
    db.flush()
    return agreement

def create_logbook(db: Session, internship_id: int, week_number: int, defaults: dict) -> Logbook:
    """Create a logbook entry for a specific week."""
    logbook = Logbook(
        internship_id=internship_id,
        week_number=week_number,
        tasks=defaults.get("tasks"),
        reflection=defaults.get("reflection"),
        issues=defaults.get("issues"),
        status=defaults.get("status", "draft"),
        mentor_validated=defaults.get("mentor_validated", False),
        submitted_at=defaults.get("submitted_at")
    )
    db.add(logbook)
    db.flush()
    return logbook

def create_evaluation_with_rules(db: Session, internship_id: int, evaluator_id: int, eval_type: str, defaults: dict) -> Evaluation:
    """Create an evaluation with rules for all active competencies."""
    evaluation = Evaluation(
        internship_id=internship_id,
        evaluator_id=evaluator_id,
        eval_type=eval_type,
        status=defaults.get("status", "concept"),
        comments=defaults.get("comments"),
        finalized=defaults.get("finalized", False),
        finalized_at=defaults.get("finalized_at")
    )
    db.add(evaluation)
    db.flush()
    
    # Get active competencies
    competencies = db.query(Competency).filter(Competency.active == True).all()
    for comp in competencies:
        rule = EvaluationRule(
            evaluation_id=evaluation.id,
            competency_id=comp.id,
            score=defaults.get("score"),
            student_description=defaults.get("student_description"),
            evaluator_feedback=defaults.get("evaluator_feedback")
        )
        db.add(rule)
    
    return evaluation

def create_feedback(db: Session, internship_id: int, from_user_id: int, to_user_id: int, message: str) -> Feedback:
    """Create a feedback message."""
    feedback = Feedback(
        internship_id=internship_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        message=message
    )
    db.add(feedback)
    db.flush()
    return feedback


# ============================================================
# SEED DATA DEFINITIONS
# ============================================================

print("\n[SEED] Starting comprehensive database seeding...\n")

# Step 1: Ensure users exist
print("1. Creating users...")

# Get existing users or create new ones
users = {}
user_defs = {
    "admin@school.be": {
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin"
    },
    "student1@school.be": {
        "password": "student123",
        "first_name": "Jan",
        "last_name": "Peeters",
        "role": "student"
    },
    "student2@school.be": {
        "password": "student123",
        "first_name": "Marie",
        "last_name": "Verhoeven",
        "role": "student"
    },
    "commissie1@school.be": {
        "password": "commissie123",
        "first_name": "Peter",
        "last_name": "Smit",
        "role": "committee"
    },
    "docent1@school.be": {
        "password": "docent123",
        "first_name": "Ann",
        "last_name": "Claessens",
        "role": "teacher"
    },
    "mentor1@school.be": {
        "password": "mentor123",
        "first_name": "Bram",
        "last_name": "Janssens",
        "role": "mentor"
    },
}

for email, defaults in user_defs.items():
    user = get_or_create_user(db, email, defaults)
    users[email] = user
    role_display = defaults["role"].ljust(12)
    print(f"   {'[OK]' if email not in [u.email for u in db.query(User).all()] else '[INFO]'} {role_display} | {email}")

# Get user IDs for relationships
admin_id = users["admin@school.be"].id
student1_id = users["student1@school.be"].id
student2_id = users["student2@school.be"].id
committee1_id = users["commissie1@school.be"].id
teacher1_id = users["docent1@school.be"].id
mentor1_id = users["mentor1@school.be"].id

# Step 2: Create competency profile if it doesn't exist
print("\n2. Creating competency profile...")

profile = db.query(CompetencyProfile).filter(
    CompetencyProfile.active == True
).first()

if not profile:
    profile = CompetencyProfile(
        name="Toegepaste Informatica 2024-2025",
        version="1.0",
        academic_year="2024-2025",
        active=True
    )
    db.add(profile)
    db.flush()
    print(f"   [OK] Created profile: {profile.name}")
else:
    print(f"   [INFO] Using existing profile: {profile.name}")

# Create competencies if they don't exist
competencies = db.query(Competency).filter(Competency.profile_id == profile.id).all()
if not competencies:
    comp_defs = [
        {"name": "Analyseren", "description": "Probleemanalyse en requirements bepalen", "weight": 30.0},
        {"name": "Ontwerpen", "description": "Technisch ontwerp en architectuur", "weight": 25.0},
        {"name": "Realiseren", "description": "Implementatie en coding", "weight": 25.0},
        {"name": "Testen", "description": "Kwaliteitsborging en testing", "weight": 20.0},
    ]
    for comp_def in comp_defs:
        comp = Competency(
            profile_id=profile.id,
            name=comp_def["name"],
            description=comp_def["description"],
            weight=comp_def["weight"],
            active=True
        )
        db.add(comp)
    db.flush()
    competencies = db.query(Competency).filter(Competency.profile_id == profile.id).all()
    print(f"   [OK] Created {len(competencies)} competencies")
else:
    print(f"   [INFO] Competencies already exist ({len(competencies)} competencies)")

# Step 3: Create companies
print("\n3. Creating companies...")

company_defs = [
    {
        "name": "TechCorp BV",
        "address": "Technologielaan 1, 1000 Brussel",
        "sector": "IT",
        "contact_person": "Jan De Smet",
        "contact_email": "j.desmet@techcorp.be",
        "mentor_id": mentor1_id
    },
    {
        "name": "DataFlow Solutions",
        "address": "Daalmeersekade 123, 2000 Antwerpen",
        "sector": "Data & Analytics",
        "contact_person": "Sophie Willems",
        "contact_email": "s.willems@dataflow.be",
        "mentor_id": None
    },
    {
        "name": "WebWise Agency",
        "address": "Koninginnastraat 45, 3000 Leuven",
        "sector": "Web Development",
        "contact_person": "Tom Van den Berg",
        "contact_email": "t.vandenberg@webwise.be",
        "mentor_id": None
    },
    {
        "name": "SecureNet",
        "address": "Wisselstraat 67, 9000 Gent",
        "sector": "Cybersecurity",
        "contact_person": "Laura Peeters",
        "contact_email": "l.peeters@securenet.be",
        "mentor_id": mentor1_id
    },
    {
        "name": "CloudScale NV",
        "address": "Avenue de la Renaissance 1, 1050 Brussel",
        "sector": "Cloud Services",
        "contact_person": "Mohammed El Amrani",
        "contact_email": "m.amrani@cloudscale.be",
        "mentor_id": None
    },
]

companies = {}
for cdef in company_defs:
    company = get_or_create_company(db, cdef["name"], cdef)
    companies[cdef["name"]] = company
    print(f"   {'[OK]' if cdef['name'] not in [c.name for c in db.query(Company).all()] else '[INFO]'} {company.name} ({company.sector})")

# Step 4: Create internships, proposals, agreements, logbooks, evaluations, feedback
print("\n4. Creating internships and related data...")

# Helper to get dates
def date_offset(days):
    return date.today() + timedelta(days=days)

# Internship scenarios for Jan Peeters (student1)
jan_internships = [
    {
        "company": "TechCorp BV",
        "teacher_id": teacher1_id,
        "mentor_id": mentor1_id,
        "start_date": date_offset(-60),
        "end_date": date_offset(30),
        "status": "Lopend",
        "proposal_status": "Goedgekeurd",
        "agreement_status": "Gevalideerd",
        "agreement_insurance": True,
        "logbooks": True,  # Create logbooks
        "evaluation_tussentijds": True,
        "evaluation_tussentijds_finalized": True,
        "evaluation_final": False,
        "feedback_count": 3
    },
    {
        "company": "DataFlow Solutions",
        "teacher_id": teacher1_id,
        "mentor_id": None,
        "start_date": date_offset(30),
        "end_date": date_offset(120),
        "status": "Goedgekeurd",
        "proposal_status": "Goedgekeurd",
        "agreement_status": "Overeenkomst Ingediend",
        "agreement_insurance": False,
        "logbooks": False,
        "evaluation_tussentijds": False,
        "evaluation_final": False,
        "feedback_count": 1
    },
    {
        "company": "WebWise Agency",
        "teacher_id": None,
        "mentor_id": None,
        "start_date": date_offset(10),
        "end_date": date_offset(100),
        "status": "Ingediend",
        "proposal_status": "Ingediend",
        "agreement_status": "Niet Ingediend",
        "agreement_insurance": False,
        "logbooks": False,
        "evaluation_tussentijds": False,
        "evaluation_final": False,
        "feedback_count": 0
    },
]

# Internship scenarios for Marie Verhoeven (student2)
marie_internships = [
    {
        "company": "SecureNet",
        "teacher_id": teacher1_id,
        "mentor_id": mentor1_id,
        "start_date": date_offset(-90),
        "end_date": date_offset(0),  # Today is end date
        "status": "Afgerond",
        "proposal_status": "Goedgekeurd",
        "agreement_status": "Gevalideerd",
        "agreement_insurance": True,
        "logbooks": False,
        "evaluation_tussentijds": True,
        "evaluation_tussentijds_finalized": True,
        "evaluation_final": True,
        "feedback_count": 5
    },
    {
        "company": "CloudScale NV",
        "teacher_id": teacher1_id,
        "mentor_id": None,
        "start_date": date_offset(15),
        "end_date": date_offset(105),
        "status": "In Beoordeling",
        "proposal_status": "In Beoordeling",
        "agreement_status": "Niet Ingediend",
        "agreement_insurance": False,
        "logbooks": False,
        "evaluation_tussentijds": False,
        "evaluation_final": False,
        "feedback_count": 0
    },
]

all_internship_configs = [
    (users["student1@school.be"].id, jan_internships),
    (users["student2@school.be"].id, marie_internships),
]

total_internships = 0
total_proposals = 0
total_agreements = 0
total_logbooks = 0
total_evaluations = 0
total_feedback = 0

for student_id, configs in all_internship_configs:
    student = db.query(User).filter(User.id == student_id).first()
    for i, config in enumerate(configs):
        company = companies[config["company"]]
        
        # Create internship
        internship = get_or_create_internship(db, student_id, company.id, {
            "teacher_id": config.get("teacher_id"),
            "mentor_id": config.get("mentor_id"),
            "start_date": config["start_date"],
            "end_date": config["end_date"],
            "status": config["status"]
        })
        total_internships += 1
        internship_num = i + 1
        print(f"   [OK] Internship #{internship_num}: {student.first_name} @ {company.name} [{config['status']}]")
        
        # Create or update proposal
        proposal = get_or_create_proposal(db, internship.id, {
            "description": f"Stage bij {company.name} als {student.role}. Project gericht op {company.sector.lower()} oplossingen.",
            "status": config["proposal_status"],
            "feedback": "Goed voorstel, voldoet aan alle criteria." if config["proposal_status"] in ["Goedgekeurd", "In Beoordeling"] else None
        })
        total_proposals += 1
        print(f"      [OK] Proposal: {proposal.status}")
        
        # Create or update agreement
        agreement = get_or_create_agreement(db, internship.id, {
            "file_path": f"/uploads/agreements/{student.email.split('@')[0]}_{company.name.replace(' ', '_')}.pdf",
            "insurance_verified": config["agreement_insurance"],
            "status": config["agreement_status"],
            "uploaded_at": datetime.now() - timedelta(days=5) if config["agreement_status"] != "Niet Ingediend" else None,
            "validated_at": datetime.now() - timedelta(days=2) if config["agreement_status"] == "Gevalideerd" else None
        })
        total_agreements += 1
        print(f"      [OK] Agreement: {agreement.status} (insurance: {agreement.insurance_verified})")
        
        # Create logbooks if needed
        if config["logbooks"] and internship.start_date and internship.end_date:
            total_days = (internship.end_date - internship.start_date).days
            num_weeks = min(10, (total_days // 7) + 1)  # Max 10 weeks for demo
            for week in range(1, num_weeks + 1):
                logbook = create_logbook(db, internship.id, week, {
                    "tasks": f"Week {week}: Opstart fase, kennis maken met codebase en eerste kleine taken uitgevoerd. Werken met {company.sector} tools.",
                    "reflection": f"Goede eerste week. Veel geleerd over de werkomgeving en team dynamiek.",
                    "issues": "Geen grote problemen deze week.",
                    "status": "submitted" if week <= 5 else "draft",
                    "mentor_validated": week <= 3,
                    "submitted_at": datetime.now() - timedelta(days=num_weeks - week) if week <= 5 else None
                })
                total_logbooks += 1
            print(f"      [OK] Logbooks: {num_weeks} weeks created")
        
        # Create intermediate evaluation if needed
        if config.get("evaluation_tussentijds"):
            eval_type = "tussentijds"
            existing_eval = db.query(Evaluation).filter(
                Evaluation.internship_id == internship.id,
                Evaluation.eval_type == eval_type
            ).first()
            
            if not existing_eval:
                evaluation = create_evaluation_with_rules(db, internship.id, teacher1_id, eval_type, {
                    "status": "afgerond",
                    "comments": "Goede vooruitgang. Student toont sterke analysemvaardigheden.",
                    "finalized": config["evaluation_tussentijds_finalized"],
                    "finalized_at": datetime.now() - timedelta(days=15) if config["evaluation_tussentijds_finalized"] else None,
                    "score": 4,
                    "evaluator_feedback": "Sterke prestaties. Blijf verder doen."
                })
                total_evaluations += 1
                print(f"      [OK] Evaluation: {eval_type} (finalized: {evaluation.finalized})")
        
        # Create final evaluation if needed
        if config.get("evaluation_final"):
            eval_type = "final"
            existing_eval = db.query(Evaluation).filter(
                Evaluation.internship_id == internship.id,
                Evaluation.eval_type == eval_type
            ).first()
            
            if not existing_eval:
                evaluation = create_evaluation_with_rules(db, internship.id, teacher1_id, eval_type, {
                    "status": "afgerond",
                    "comments": "Uitstekende stage. Student heeft alle doelen bereikt.",
                    "finalized": True,
                    "finalized_at": datetime.now() - timedelta(days=1),
                    "score": 5,
                    "evaluator_feedback": "Zeer goede prestaties. Aanbevolen voor toekomstige projecten."
                })
                total_evaluations += 1
                print(f"      [OK] Evaluation: {eval_type} (finalized: {evaluation.finalized})")
        
        # Create feedback messages if needed
        if config.get("feedback_count", 0) > 0:
            feedback_messages = [
                ("Goede start van de stage!", "teacher to student"),
                ("Bedankt voor de snelle feedback", "student to teacher"),
                ("Heeft u nog vragen over het project?", "mentor to student"),
            ]
            for i in range(min(config["feedback_count"], len(feedback_messages))):
                msg, direction = feedback_messages[i]
                if direction == "teacher to student":
                    from_id, to_id = teacher1_id, student_id
                elif direction == "student to teacher":
                    from_id, to_id = student_id, teacher1_id
                else:  # mentor to student
                    from_id, to_id = mentor1_id, student_id
                
                feedback = create_feedback(db, internship.id, from_id, to_id, msg)
                total_feedback += 1
        
        if config.get("feedback_count", 0) > 0:
            print(f"      [OK] Feedback: {config['feedback_count']} messages created")

db.commit()

# Step 5: Summary
print("\n" + "="*60)
print("[DONE] Seeding complete!")
print("="*60)
print(f"\nData created:")
print(f"  Users:                {db.query(User).count()}")
print(f"  Companies:            {db.query(Company).count()}")
print(f"  Internships:          {db.query(Internship).count()}")
print(f"  Proposals:            {db.query(Proposal).count()}")
print(f"  Agreements:           {db.query(Agreement).count()}")
print(f"  Logbook entries:      {db.query(Logbook).count()}")
print(f"  Evaluations:          {db.query(Evaluation).count()}")
print(f"  Evaluation rules:     {db.query(EvaluationRule).count()}")
print(f"  Feedback messages:    {db.query(Feedback).count()}")
print(f"  Competency profiles:  {db.query(CompetencyProfile).count()}")
print(f"  Competencies:         {db.query(Competency).count()}")

db.close()

print("\n[INFO] Test credentials:")
print("  " + "-"*56)
print(f"  {'Role':<12} | {'Email':<28} | {'Password'}")
print("  " + "-"*56)
for email, u in user_defs.items():
    print(f"  {u['role']:<12} | {email:<28} | {u['password']}")
print("  " + "-"*56)

print("\n[START] Next steps:")
print("  1. Start backend: uvicorn app.main:app --reload")
print("  2. Open frontend: http://localhost:8080/index.html")
print("  3. Login with any account above\n")
