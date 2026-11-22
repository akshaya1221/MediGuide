import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def uuid4_str() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    patient = "patient"
    clinician = "clinician"
    admin = "admin"


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    needs_review = "needs_review"
    failed = "failed"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    full_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.patient)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    documents: Mapped[list["MedicalDocument"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class MedicalDocument(Base):
    __tablename__ = "medical_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    doc_type: Mapped[str] = mapped_column(String(40), default="other")
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.uploaded)
    sha256: Mapped[str] = mapped_column(String(64))
    file_size: Mapped[int]
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extraction_confidence: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner: Mapped[User] = relationship(back_populates="documents")
    items: Mapped[list["ExtractedItem"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    explanation: Mapped["MedicalExplanation | None"] = relationship(back_populates="document", cascade="all, delete-orphan", uselist=False)
    followups: Mapped[list["FollowUp"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    medications: Mapped[list["Medication"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    questions: Mapped[list["ConsultationQuestion"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class ExtractedItem(Base):
    __tablename__ = "extracted_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("medical_documents.id", ondelete="CASCADE"), index=True)
    data_type: Mapped[str] = mapped_column(String(40))
    item_name: Mapped[str] = mapped_column(String(120))
    item_value: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_text: Mapped[str | None] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    document: Mapped[MedicalDocument] = relationship(back_populates="items")


class MedicalExplanation(Base):
    __tablename__ = "medical_explanations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("medical_documents.id", ondelete="CASCADE"), unique=True)
    simple_text: Mapped[str] = mapped_column(Text)
    important_points: Mapped[str] = mapped_column(Text, default="[]")
    cautions: Mapped[str] = mapped_column(Text, default="[]")
    citations: Mapped[str] = mapped_column(Text, default="[]")
    model_name: Mapped[str] = mapped_column(String(80))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    document: Mapped[MedicalDocument] = relationship(back_populates="explanation")


class FollowUp(Base):
    __tablename__ = "follow_ups"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("medical_documents.id", ondelete="CASCADE"), index=True)
    instruction: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reminder_set: Mapped[bool] = mapped_column(Boolean, default=False)
    source_text: Mapped[str | None] = mapped_column(Text)
    document: Mapped[MedicalDocument] = relationship(back_populates="followups")


class Medication(Base):
    __tablename__ = "medications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("medical_documents.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    dosage_text: Mapped[str | None] = mapped_column(String(120))
    timing_text: Mapped[str | None] = mapped_column(String(160))
    needs_confirmation: Mapped[bool] = mapped_column(Boolean, default=True)
    source_text: Mapped[str | None] = mapped_column(Text)
    document: Mapped[MedicalDocument] = relationship(back_populates="medications")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("medical_documents.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(40))
    event_date: Mapped[date | None] = mapped_column(Date)
    summary: Mapped[str] = mapped_column(Text)
    document: Mapped[MedicalDocument] = relationship(back_populates="timeline_events")


class ConsultationQuestion(Base):
    __tablename__ = "consultation_questions"
    __table_args__ = (UniqueConstraint("document_id", "question_text"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid4_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("medical_documents.id", ondelete="CASCADE"), index=True)
    question_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="saved")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    document: Mapped[MedicalDocument | None] = relationship(back_populates="questions")
