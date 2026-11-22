from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .models import DocumentStatus, Role


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    email: EmailStr
    role: Role
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ExtractedItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    data_type: str
    item_name: str
    item_value: str
    unit: str | None
    confidence: float
    source_text: str | None
    verified: bool


class ExplanationRead(BaseModel):
    id: str
    simple_text: str
    important_points: list[str]
    cautions: list[str]
    citations: list[dict[str, str | int]]
    model_name: str
    generated_at: datetime


class FollowUpRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str
    instruction: str
    due_date: date | None
    status: str
    reminder_set: bool
    source_text: str | None


class FollowUpUpdate(BaseModel):
    status: Literal["pending", "completed", "dismissed"] | None = None
    reminder_set: bool | None = None
    due_date: date | None = None


class MedicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str
    name: str
    dosage_text: str | None
    timing_text: str | None
    needs_confirmation: bool
    source_text: str | None


class TimelineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str
    event_type: str
    event_date: date | None
    summary: str


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str | None
    question_text: str
    status: str
    created_at: datetime


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    original_name: str
    doc_type: str
    content_type: str
    file_size: int
    status: DocumentStatus
    extraction_confidence: float | None
    uploaded_at: datetime
    processed_at: datetime | None
    error_message: str | None


class DocumentDetail(DocumentSummary):
    extracted_text: str | None
    items: list[ExtractedItemRead]
    explanation: ExplanationRead | None
    followups: list[FollowUpRead]
    medications: list[MedicationRead]
    timeline_events: list[TimelineRead]
    questions: list[QuestionRead]


class DashboardStats(BaseModel):
    document_count: int
    ready_count: int
    pending_followups: int
    medication_count: int
    needs_review_count: int
    recent_documents: list[DocumentSummary]
    upcoming_followups: list[FollowUpRead]


class AgentCitation(BaseModel):
    chunk: int = Field(ge=1)
    quote: str = Field(max_length=240)


class AgentMedication(BaseModel):
    name: str
    dosage_text: str | None = None
    timing_text: str | None = None
    source_text: str
    needs_confirmation: bool = True


class AgentFollowUp(BaseModel):
    instruction: str
    due_date: date | None = None
    source_text: str


class AgentAnalysis(BaseModel):
    simple_summary: str
    important_points: list[str] = Field(max_length=10)
    cautions: list[str] = Field(max_length=8)
    medications: list[AgentMedication] = Field(max_length=20)
    followups: list[AgentFollowUp] = Field(max_length=20)
    consultation_questions: list[str] = Field(max_length=10)
    citations: list[AgentCitation] = Field(max_length=12)

