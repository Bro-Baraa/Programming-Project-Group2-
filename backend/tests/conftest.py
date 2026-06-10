import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app, _rate_limit
from app.auth import get_password_hash
from app.models import User, Competency

# Create test database in memory
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with fresh database."""
    _rate_limit.clear()
    yield TestClient(app)


def _create_test_user(db, email, password, first_name, role):
    """Helper to create a test user with standard boilerplate."""
    user = User(
        email=email,
        password_hash=get_password_hash(password),
        first_name=first_name,
        last_name="User",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db):
    return _create_test_user(db, "admin@test.com", "admin123", "Admin", "admin")


@pytest.fixture
def test_student(db):
    return _create_test_user(db, "student@test.com", "student123", "Student", "student")


@pytest.fixture
def test_teacher(db):
    return _create_test_user(db, "teacher@test.com", "teacher123", "Teacher", "teacher")


@pytest.fixture
def test_committee(db):
    return _create_test_user(
        db, "committee@test.com", "committee123", "Committee", "committee"
    )


@pytest.fixture
def test_mentor(db):
    return _create_test_user(db, "mentor@test.com", "mentor123", "Mentor", "mentor")


@pytest.fixture
def admin_token(client, test_admin):
    """Get admin access token."""
    response = client.post(
        "/api/auth/login", data={"username": "admin@test.com", "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def student_token(client, test_student):
    """Get student access token."""
    response = client.post(
        "/api/auth/login",
        data={"username": "student@test.com", "password": "student123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def teacher_token(client, test_teacher):
    """Get teacher access token."""
    response = client.post(
        "/api/auth/login",
        data={"username": "teacher@test.com", "password": "teacher123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def committee_token(client, test_committee):
    """Get committee access token."""
    response = client.post(
        "/api/auth/login",
        data={"username": "committee@test.com", "password": "committee123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def mentor_token(client, test_mentor):
    """Get mentor access token."""
    response = client.post(
        "/api/auth/login", data={"username": "mentor@test.com", "password": "mentor123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def sample_competencies(db):
    """Create sample competencies that sum to 100% under a profile."""
    from app.models import CompetencyProfile

    # Create a competency profile first
    profile = CompetencyProfile(
        name="Test Profile", version="1.0", academic_year="2024-2025", active=True
    )
    db.add(profile)
    db.flush()

    competencies = [
        Competency(
            name="Technical Skills", weight=25.0, active=True, profile_id=profile.id
        ),
        Competency(
            name="Communication", weight=25.0, active=True, profile_id=profile.id
        ),
        Competency(name="Teamwork", weight=25.0, active=True, profile_id=profile.id),
        Competency(
            name="Problem Solving", weight=25.0, active=True, profile_id=profile.id
        ),
    ]
    for comp in competencies:
        db.add(comp)
    db.commit()
    return competencies


@pytest.fixture
def auth_headers_admin(admin_token):
    """Authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_student(student_token):
    """Authorization headers for student."""
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture
def auth_headers_teacher(teacher_token):
    """Authorization headers for teacher."""
    return {"Authorization": f"Bearer {teacher_token}"}


@pytest.fixture
def auth_headers_committee(committee_token):
    """Authorization headers for committee."""
    return {"Authorization": f"Bearer {committee_token}"}


@pytest.fixture
def auth_headers_mentor(mentor_token):
    """Authorization headers for mentor."""
    return {"Authorization": f"Bearer {mentor_token}"}


@pytest.fixture
def sample_internship(db, test_student, test_teacher):
    """Create a sample internship for testing with proper company and proposal."""
    from datetime import date, timedelta
    from app.models import Internship, Company, Proposal

    # Create company first
    company = Company(
        name="Test Company",
        address="123 Test Street",
        sector="IT",
        contact_person="John Contact",
        contact_email="john@test.com",
    )
    db.add(company)
    db.flush()

    # Create internship with teacher assigned
    internship = Internship(
        student_id=test_student.id,
        teacher_id=test_teacher.id,
        company_id=company.id,
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=120),
        status="Lopend",
    )
    db.add(internship)
    db.flush()

    # Create proposal
    proposal = Proposal(
        internship_id=internship.id,
        description="Test internship description",
        status="Goedgekeurd",
    )
    db.add(proposal)
    db.commit()
    db.refresh(internship)
    return internship


@pytest.fixture
def internship_with_logbook(db, test_student, test_mentor):
    """Create internship with Lopend status for logbook testing."""
    from datetime import date, timedelta
    from app.models import Internship, Company, Proposal

    # Create company
    company = Company(
        name="Test Company", contact_person="John", contact_email="john@test.com"
    )
    db.add(company)
    db.flush()

    # Create internship with mentor assigned
    internship = Internship(
        student_id=test_student.id,
        mentor_id=test_mentor.id,
        company_id=company.id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        status="Lopend",
    )
    db.add(internship)
    db.flush()

    # Create proposal
    proposal = Proposal(
        internship_id=internship.id, description="Test", status="Goedgekeurd"
    )
    db.add(proposal)
    db.commit()
    db.refresh(internship)

    return internship
