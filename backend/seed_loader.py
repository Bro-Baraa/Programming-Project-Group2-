#!/usr/bin/env python3
"""
YAML-backed database seeding loader.

Reads seed_data.yaml and populates the database with all test data.

Usage:
    python seed_loader.py              # uses seed_data.yaml
    python seed_loader.py mydata.yaml # uses custom yaml file

To edit the data, just open seed_data.yaml and change values.
No Python code needed!
"""

import sys
from datetime import date, timedelta, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import (
    Base, User, Company, Internship, Proposal, Agreement,
    Logbook, Evaluation, EvaluationRule, Feedback,
    CompetencyProfile, Competency, Document
)
import bcrypt

# ---------------------------------------------------------------------------
# Safe YAML import
# ---------------------------------------------------------------------------
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is not installed.")
    print("       Run: pip install pyyaml")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _resolve_user_id(user_lookup: dict, email: str | None) -> int | None:
    return user_lookup[email].id if email else None


def _get_or_create(db, model, filters, defaults):
    existing = db.query(model).filter_by(**filters).first()
    if existing:
        return existing
    obj = model(**defaults)
    db.add(obj)
    db.flush()
    return obj


def parse_date(value):
    """
    Parse a date value from YAML.
    - Integer: relative days from today (+30 = over 30 dagen, -30 = 30 dagen geleden)
    - String: absolute ISO date ("2024-09-01")
    - None: null
    """
    if value is None:
        return None
    if isinstance(value, int):
        return date.today() + timedelta(days=value)
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {value!r}. Use integer or YYYY-MM-DD.")
    raise ValueError(f"Cannot parse date value: {value!r}")


def parse_datetime(value):
    """
    Parse a datetime value from YAML.
    - Integer: relative days from today (at midnight)
    - String: absolute ISO datetime ("2024-09-01T10:00:00")
    - None: null
    """
    if value is None:
        return None
    if isinstance(value, int):
        return datetime.now() + timedelta(days=value)
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise ValueError(f"Invalid datetime format: {value!r}")
    raise ValueError(f"Cannot parse datetime value: {value!r}")

# ---------------------------------------------------------------------------
# Entity creators
# ---------------------------------------------------------------------------

def create_user(db: Session, data: dict) -> User:
    return _get_or_create(db, User,
        filters={"email": data["email"]},
        defaults={
            "email": data["email"],
            "password_hash": get_password_hash(data["password"]),
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "role": data["role"],
            "is_active": data.get("is_active", True)
        })


def create_company(db: Session, data: dict, user_lookup: dict) -> Company:
    mentor_id = _resolve_user_id(user_lookup, data.get("mentor"))
    return _get_or_create(db, Company,
        filters={"name": data["name"]},
        defaults={
            "name": data["name"],
            "address": data.get("address"),
            "sector": data.get("sector"),
            "contact_person": data.get("contact_person"),
            "contact_email": data.get("contact_email"),
            "mentor_id": mentor_id
        })


def create_competency_profile(db: Session, data: dict) -> CompetencyProfile:
    existing = db.query(CompetencyProfile).filter(
        CompetencyProfile.name == data["name"],
        CompetencyProfile.academic_year == data["academic_year"]
    ).first()
    if existing:
        return existing
    profile = CompetencyProfile(
        name=data["name"],
        version=data.get("version", "1.0"),
        academic_year=data["academic_year"],
        active=data.get("active", True)
    )
    db.add(profile)
    db.flush()
    for comp_data in data.get("competencies", []):
        comp = Competency(
            profile_id=profile.id,
            name=comp_data["name"],
            description=comp_data.get("description"),
            weight=float(comp_data["weight"]),
            active=True
        )
        db.add(comp)
    db.flush()
    return profile


def create_internship(db: Session, data: dict, user_lookup: dict, company_lookup: dict) -> Internship:
    student = user_lookup[data["student"]]
    company = company_lookup[data["company"]]
    teacher_id = _resolve_user_id(user_lookup, data.get("teacher"))
    mentor_id = _resolve_user_id(user_lookup, data.get("mentor"))

    return _get_or_create(db, Internship,
        filters={"student_id": student.id, "company_id": company.id},
        defaults={
            "student_id": student.id,
            "teacher_id": teacher_id,
            "mentor_id": mentor_id,
            "company_id": company.id,
            "start_date": parse_date(data.get("start_date")),
            "end_date": parse_date(data.get("end_date")),
            "status": data["status"]
        })


def create_proposal(db: Session, internship_id: int, data: dict) -> Proposal:
    return _get_or_create(db, Proposal,
        filters={"internship_id": internship_id},
        defaults={
            "internship_id": internship_id,
            "description": data.get("description", ""),
            "status": data["status"],
            "feedback": data.get("feedback"),
            "revision_count": data.get("revision_count", 0),
            "resubmitted_at": parse_datetime(data.get("resubmitted_at"))
        })


def _ensure_fake_file(path: str | None) -> None:
    """Create a minimal fake PDF on disk if the path is set but the file doesn't exist."""
    if not path:
        return
    p = Path(path)
    if p.exists():
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"%PDF-1.4 fake pdf content\n%%EOF\n")


def create_agreement(db: Session, internship_id: int, data: dict) -> Agreement:
    file_path = data.get("file_path")
    _ensure_fake_file(file_path)
    return _get_or_create(db, Agreement,
        filters={"internship_id": internship_id},
        defaults={
            "internship_id": internship_id,
            "file_path": file_path,
            "insurance_verified": data.get("insurance", False),
            "status": data["status"],
            "uploaded_at": parse_datetime(data.get("uploaded_at")),
            "validated_at": parse_datetime(data.get("validated_at"))
        })


def create_logbook(db: Session, internship_id: int, week: int, data: dict) -> Logbook:
    logbook = Logbook(
        internship_id=internship_id,
        week_number=week,
        tasks=data.get("tasks"),
        reflection=data.get("reflection"),
        issues=data.get("issues"),
        status=data.get("status"),
        mentor_validated=data.get("mentor_validated", False),
        mentor_feedback=data.get("mentor_feedback"),
        submitted_at=parse_datetime(data.get("submitted_at"))
    )
    db.add(logbook)
    db.flush()
    return logbook


def create_logbooks_for_internship(db: Session, internship: Internship, logbook_config: dict, company: Company) -> int:
    total_days = (internship.end_date - internship.start_date).days
    count = min(logbook_config["count"], max(1, (total_days // 7) + 1))
    all_sub = logbook_config.get("all_submitted", False)
    all_val = logbook_config.get("all_validated", False)
    for week in range(1, count + 1):
        is_sub = all_sub or week <= count // 2
        is_val = is_sub and (all_val or week <= count // 3)
        lb_data = {
            "tasks": f"Week {week}: Werk aan {company.sector} project.",
            "reflection": f"Week {week}: {'Sterke' if week % 2 == 0 else 'Stabiele'} prestaties.",
            "issues": "Geen problemen" if week % 3 != 0 else "Technische uitdaging, opgelost.",
            "status": "submitted" if is_sub else "draft",
            "mentor_validated": is_val,
            "mentor_feedback": "Goed werk" if is_val else None,
            "submitted_at": -count + week if is_sub else None
        }
        create_logbook(db, internship.id, week, lb_data)
    return count


def create_evaluation(db: Session, internship_id: int, evaluator_id: int, data: dict, competencies: list) -> Evaluation:
    evaluation = Evaluation(
        internship_id=internship_id,
        evaluator_id=evaluator_id,
        eval_type=data["type"],
        status=data.get("status", "concept"),
        comments=data.get("comments"),
        finalized=data.get("finalized", False),
        finalized_at=parse_datetime(data.get("finalized_at"))
    )
    db.add(evaluation)
    db.flush()

    for comp in competencies:
        rule = EvaluationRule(
            evaluation_id=evaluation.id,
            competency_id=comp.id,
            score=data.get("score"),
            student_description=data.get("student_description"),
            evaluator_feedback=data.get("evaluator_feedback")
        )
        db.add(rule)
    db.flush()
    return evaluation


def create_feedback(db: Session, internship_id: int, from_user_id: int, to_user_id: int, message: str) -> Feedback:
    feedback = Feedback(
        internship_id=internship_id,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        message=message
    )
    db.add(feedback)
    db.flush()
    return feedback


def create_document(db: Session, internship_id: int, data: dict) -> Document:
    file_path = data.get("file_path")
    _ensure_fake_file(file_path)
    doc = Document(
        internship_id=internship_id,
        doc_type=data.get("doc_type", "other"),
        file_path=file_path
    )
    db.add(doc)
    db.flush()
    return doc

# ---------------------------------------------------------------------------
# Main seeding
# ---------------------------------------------------------------------------

def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def seed_from_yaml(path: str = "seed_data.yaml"):
    print("=" * 70)
    print("YAML-backed database seeding")
    print("=" * 70)
    print(f"\nLoading: {path}\n")

    data = load_yaml(path)
    db = SessionLocal()

    # Reset database
    print("[INIT] Dropping and recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[OK] Tables ready!\n")

    # --- Users ---
    print("1. Creating users...")
    user_lookup = {}
    for user_data in data.get("users", []):
        user = create_user(db, user_data)
        user_lookup[user_data["email"]] = user
        status = "✓" if user_data.get("is_active", True) else "✗ INACTIVE"
        print(f"   {user.role:<12} | {user.email:<30} | {status}")
    print()

    # --- Companies ---
    print("2. Creating companies...")
    company_lookup = {}
    for company_data in data.get("companies", []):
        company = create_company(db, company_data, user_lookup)
        company_lookup[company_data["name"]] = company
        print(f"   {company.name:<25} | {company.sector}")
    print()

    # --- Competency profiles ---
    print("3. Creating competency profiles...")
    for profile_data in data.get("competency_profiles", []):
        profile = create_competency_profile(db, profile_data)
        active = "✓ active" if profile.active else "✗ inactive"
        print(f"   {profile.name:<35} | {active}")
    print()

    # Get active competencies for evaluations
    active_competencies = db.query(Competency).join(CompetencyProfile).filter(
        CompetencyProfile.active
    ).all()

    # --- Internships ---
    print("4. Creating internships...")
    scenarios = data.get("internships", [])
    print(f"   {len(scenarios)} scenario(s) found\n")

    for idx, scenario in enumerate(scenarios, 1):
        student = user_lookup[scenario["student"]]
        company = company_lookup[scenario["company"]]
        internship = create_internship(db, scenario, user_lookup, company_lookup)

        print(f"   [{idx:02d}] {student.first_name:<12} @ {company.name:<20} | {scenario['status']}")

        # Proposal
        if "proposal" in scenario:
            create_proposal(db, internship.id, scenario["proposal"])
            print(f"        Proposal: {scenario['proposal']['status']}")

        # Agreement
        if "agreement" in scenario:
            create_agreement(db, internship.id, scenario["agreement"])
            print(f"        Agreement: {scenario['agreement']['status']}")

        # Documents
        documents = scenario.get("documents", [])
        for doc_data in documents:
            create_document(db, internship.id, doc_data)
        if documents:
            print(f"        Documents: {len(documents)}")

        # Logbooks
        logbook_config = scenario.get("logbooks")
        if logbook_config and internship.start_date and internship.end_date:
            weeks = create_logbooks_for_internship(db, internship, logbook_config, company)
            print(f"        Logbooks: {weeks} weeks")

        # Evaluations
        for eval_data in scenario.get("evaluations", []):
            evaluator = user_lookup[eval_data["evaluator"]]
            create_evaluation(db, internship.id, evaluator.id, eval_data, active_competencies)
            print(f"        Evaluation: {eval_data['type']} ({eval_data['status']}) score={eval_data.get('score')}")

        # Feedback
        feedback_items = scenario.get("feedback", [])
        for fb_data in feedback_items:
            from_user = user_lookup[fb_data["from"]]
            to_user = user_lookup[fb_data["to"]]
            create_feedback(db, internship.id, from_user.id, to_user.id, fb_data["message"])
        if feedback_items:
            print(f"        Feedback: {len(feedback_items)} berichten")

        print()

    db.commit()

    # Summary
    print("=" * 70)
    print("[DONE] Seeding complete!")
    print("=" * 70)
    entities = [
        ("Users", User),
        ("Companies", Company),
        ("Competency profiles", CompetencyProfile),
        ("Competencies", Competency),
        ("Internships", Internship),
        ("Proposals", Proposal),
        ("Agreements", Agreement),
        ("Logbooks", Logbook),
        ("Evaluations", Evaluation),
        ("Feedback", Feedback),
        ("Documents", Document),
    ]
    print(f"\n{'Entity':<25} {'Count':>10}")
    print("-" * 36)
    for label, model in entities:
        print(f"{label:<25} {db.query(model).count():>10}")

    print("\n" + "=" * 70)
    print("Test credentials:")
    print("=" * 70)
    print(f"  {'Role':<12} | {'Email':<30} | {'Password'}")
    print("  " + "-" * 60)
    for user_data in data.get("users", []):
        print(f"  {user_data['role']:<12} | {user_data['email']:<30} | {user_data['password']}")
    print("  " + "-" * 60)

    print("\n" + "=" * 70)
    print("Scenarios covered:")
    print("=" * 70)
    covered = [
        "All internship statuses",
        "All proposal statuses",
        "All agreement statuses",
        "Logbook variations",
        "Evaluations: concept & afgerond",
        "Score range: 1-5",
        "Active & inactive profiles",
        "Inactive users",
        "Edge cases: no teacher, no mentor",
        "Committee involvement",
        "Documents model",
    ]
    for s in covered:
        print(f"  ✓ {s}")
    print("=" * 70)
    print("\n[START] Next steps:")
    print("  1. Start backend:  uvicorn app.main:app --reload")
    print("  2. Open frontend:  http://localhost:8080/index.html")
    print("\n")
    db.close()


if __name__ == "__main__":
    yaml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("seed_data.yaml")
    if not yaml_path.is_absolute():
        yaml_path = Path(__file__).parent / yaml_path
    if not yaml_path.exists():
        print(f"ERROR: File not found: {yaml_path}")
        sys.exit(1)
    seed_from_yaml(str(yaml_path))
