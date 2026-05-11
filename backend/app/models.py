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

    internships_as_student = relationship("Internship", foreign_keys="Internship.student_id", back_populates="student")
    evaluations = relationship("Evaluation", back_populates="evaluator")
    feedback_sent = relationship("Feedback", foreign_keys="Feedback.from_user_id", back_populates="from_user")
    feedback_received = relationship("Feedback", foreign_keys="Feedback.to_user_id", back_populates="to_user")


class Internship(Base):
    __tablename__ = "internships"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    contact_person = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="Ingediend")  # Ingediend, In Beoordeling, Goedgekeurd, etc.
    agreement_uploaded = Column(Boolean, default=False)
    agreement_filename = Column(String, nullable=True)
    committee_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("User", foreign_keys=[student_id], back_populates="internships_as_student")
    logbooks = relationship("Logbook", back_populates="internship", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="internship", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="internship", cascade="all, delete-orphan")


class Logbook(Base):
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


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    weight = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    internship_id = Column(Integer, ForeignKey("internships.id"), nullable=False)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # tussentijds, final
    scores = Column(String)  # JSON string: {"competency_id": score}
    comments = Column(Text, nullable=True)
    finalized = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    internship = relationship("Internship", back_populates="evaluations")
    evaluator = relationship("User", back_populates="evaluations")


class Feedback(Base):
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