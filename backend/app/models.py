from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # student, teacher, committee, mentor, admin
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    internships_as_student = relationship("Internship", foreign_keys="Internship.student_id", back_populates="student")
    internships_as_teacher = relationship("Internship", foreign_keys="Internship.teacher_id", back_populates="teacher")
    internships_as_mentor = relationship("Internship", foreign_keys="Internship.mentor_id", back_populates="mentor")
    evaluations = relationship("Evaluation", back_populates="evaluator")
    feedback_sent = relationship("Feedback", foreign_keys="Feedback.from_user_id", back_populates="from_user")
    feedback_received = relationship("Feedback", foreign_keys="Feedback.to_user_id", back_populates="to_user")
    companies_as_mentor = relationship("Company", foreign_keys="Company.mentor_id", back_populates="mentor")


class Company(Base):
    """Bedrijven table - stores company information"""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    contact_person = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="companies_as_mentor")
    internships = relationship("Internship", back_populates="company")


class Internship(Base):
    """Stages table - the main internship record"""
    __tablename__ = "internships"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String, default="Ingediend")  # Ingediend, In Beoordeling, Goedgekeurd, Afgekeurd, Aanpassingen Vereist, Overeenkomst Ingediend, Lopend, Afgerond
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id], back_populates="internships_as_student")
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="internships_as_teacher")
    mentor = relationship("User", foreign_keys=[mentor_id], back_populates="internships_as_mentor")
    company = relationship("Company", back_populates="internships")
    proposal = relationship("Proposal", back_populates="internship", uselist=False)
    agreement = relationship("Agreement", back_populates="internship", uselist=False)
    documents = relationship("Document", back_populates="internship", cascade="all, delete-orphan")
    logbooks = relationship("Logbook", back_populates="internship", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="internship", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="internship", cascade="all, delete-orphan")


class Proposal(Base):
    """Stagevoorstellen table - internship proposals"""
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    status = Column(String, default="Ingediend")  # Ingediend, In Beoordeling, Goedgekeurd, Afgekeurd, Aanpassingen Vereist
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    internship = relationship("Internship", back_populates="proposal")


class Agreement(Base):
    """Overeenkomst table - internship agreements"""
    __tablename__ = "agreements"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False, unique=True)
    file_path = Column(String, nullable=True)
    insurance_verified = Column(Boolean, default=False)
    status = Column(String, default="Niet Ingediend")  # Niet Ingediend, Ingediend, Gevalideerd, Onvolledig
    uploaded_at = Column(DateTime(timezone=True), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)

    internship = relationship("Internship", back_populates="agreement")


class Document(Base):
    """Documenten table - additional documents"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    doc_type = Column(String, nullable=False)  # agreement, evaluation, other
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    internship = relationship("Internship", back_populates="documents")


class Logbook(Base):
    """Logboeken table - weekly logbooks"""
    __tablename__ = "logbooks"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    tasks = Column(Text, nullable=True)
    reflection = Column(Text, nullable=True)
    issues = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft, submitted
    mentor_validated = Column(Boolean, default=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    internship = relationship("Internship", back_populates="logbooks")


class CompetencyProfile(Base):
    """CompetentieProfielen table - competency profiles"""
    __tablename__ = "competency_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    academic_year = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    competencies = relationship("Competency", back_populates="profile")


class Competency(Base):
    """Competenties table - individual competencies"""
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("competency_profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("CompetencyProfile", back_populates="competencies")
    evaluation_rules = relationship("EvaluationRule", back_populates="competency")


class Evaluation(Base):
    """Evaluaties table - evaluations"""
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    eval_type = Column(String, nullable=False)  # tussentijds, final
    status = Column(String, default="concept")  # concept, afgerond
    comments = Column(Text, nullable=True)
    finalized = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    internship = relationship("Internship", back_populates="evaluations")
    evaluator = relationship("User", back_populates="evaluations")
    rules = relationship("EvaluationRule", back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationRule(Base):
    """Evaluatie_Regels table - per-competency evaluation scores"""
    __tablename__ = "evaluation_rules"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id"), nullable=False)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False)
    score = Column(Integer, nullable=True)  # 1-5
    student_description = Column(Text, nullable=True)
    evaluator_feedback = Column(Text, nullable=True)

    evaluation = relationship("Evaluation", back_populates="rules")
    competency = relationship("Competency", back_populates="evaluation_rules")


class Feedback(Base):
    """Feedback table - general feedback messages"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    internship = relationship("Internship", back_populates="feedbacks")
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="feedback_sent")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="feedback_received")
