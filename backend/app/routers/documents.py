import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..agent_service import analyze_record, encode_json
from ..database import get_db
from ..deps import get_current_user
from ..document_processing import extract_structured_items, extract_text, normalize_text, parse_date
from ..models import (
    ConsultationQuestion,
    DocumentStatus,
    ExtractedItem,
    FollowUp,
    MedicalDocument,
    MedicalExplanation,
    Medication,
    TimelineEvent,
    User,
)
from ..schemas import DocumentDetail, DocumentSummary, ExplanationRead
from ..storage import document_path, processing_file, save_upload

router = APIRouter(prefix="/documents", tags=["Medical documents"])


def document_query():
    return select(MedicalDocument).options(
        selectinload(MedicalDocument.items),
        selectinload(MedicalDocument.explanation),
        selectinload(MedicalDocument.followups),
        selectinload(MedicalDocument.medications),
        selectinload(MedicalDocument.timeline_events),
        selectinload(MedicalDocument.questions),
    )


def to_detail(document: MedicalDocument) -> DocumentDetail:
    explanation = None
    if document.explanation:
        explanation = ExplanationRead(
            id=document.explanation.id,
            simple_text=document.explanation.simple_text,
            important_points=json.loads(document.explanation.important_points),
            cautions=json.loads(document.explanation.cautions),
            citations=json.loads(document.explanation.citations),
            model_name=document.explanation.model_name,
            generated_at=document.explanation.generated_at,
        )
    base = DocumentSummary.model_validate(document).model_dump()
    return DocumentDetail(
        **base,
        extracted_text=document.extracted_text,
        items=document.items,
        explanation=explanation,
        followups=document.followups,
        medications=document.medications,
        timeline_events=document.timeline_events,
        questions=document.questions,
    )


async def process_document(document: MedicalDocument, db: Session) -> None:
    document.status = DocumentStatus.processing
    db.commit()
    try:
        with processing_file(document.stored_name) as source_path:
            extraction = extract_text(source_path, document.content_type)
        text = normalize_text(extraction.text)
        if len(text) < 20:
            raise ValueError("No usable text could be extracted. Upload a clearer scan or digital PDF.")
        document.extracted_text = text
        document.extraction_confidence = extraction.confidence
        for data in extract_structured_items(text, extraction.confidence):
            db.add(ExtractedItem(document_id=document.id, **data))
        analysis, model_name = await analyze_record(text, document.doc_type)
        db.add(MedicalExplanation(
            document_id=document.id,
            simple_text=analysis.simple_summary,
            important_points=encode_json(analysis.important_points),
            cautions=encode_json(analysis.cautions),
            citations=encode_json([item.model_dump() for item in analysis.citations]),
            model_name=model_name,
        ))
        for medication in analysis.medications:
            db.add(Medication(document_id=document.id, **medication.model_dump()))
        for followup in analysis.followups:
            db.add(FollowUp(document_id=document.id, **followup.model_dump()))
        for question in analysis.consultation_questions:
            db.add(ConsultationQuestion(user_id=document.user_id, document_id=document.id, question_text=question))
        event_date = next((parse_date(item.item_value) for item in document.items if item.data_type == "date"), None)
        db.add(TimelineEvent(
            document_id=document.id,
            event_type=document.doc_type,
            event_date=event_date or document.uploaded_at.date(),
            summary=analysis.simple_summary[:500],
        ))
        document.status = DocumentStatus.needs_review if extraction.confidence < 0.78 else DocumentStatus.ready
        document.processed_at = datetime.now(timezone.utc)
        document.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        fresh = db.get(MedicalDocument, document.id)
        if fresh:
            fresh.status = DocumentStatus.failed
            fresh.error_message = str(exc)[:1000]
            db.commit()


@router.post("", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("other"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentDetail:
    document_id = str(uuid.uuid4())
    stored_name, file_size, sha256, _ = await save_upload(file, user.id, document_id)
    duplicate = db.scalar(select(MedicalDocument).where(MedicalDocument.user_id == user.id, MedicalDocument.sha256 == sha256))
    if duplicate:
        document_path(stored_name).unlink(missing_ok=True)
        raise HTTPException(status_code=409, detail="This document has already been uploaded")
    document = MedicalDocument(
        id=document_id,
        user_id=user.id,
        original_name=file.filename or "medical-document",
        stored_name=stored_name,
        content_type=file.content_type or "application/octet-stream",
        doc_type=doc_type[:40],
        sha256=sha256,
        file_size=file_size,
    )
    db.add(document)
    db.commit()
    await process_document(document, db)
    loaded = db.scalar(document_query().where(MedicalDocument.id == document.id))
    if not loaded:
        raise HTTPException(status_code=500, detail="Document could not be reloaded")
    return to_detail(loaded)


@router.get("", response_model=list[DocumentSummary])
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[MedicalDocument]:
    return list(db.scalars(select(MedicalDocument).where(MedicalDocument.user_id == user.id).order_by(MedicalDocument.uploaded_at.desc())))


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DocumentDetail:
    document = db.scalar(document_query().where(MedicalDocument.id == document_id, MedicalDocument.user_id == user.id))
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return to_detail(document)


@router.post("/{document_id}/reprocess", response_model=DocumentDetail)
async def reprocess_document(document_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DocumentDetail:
    document = db.scalar(document_query().where(MedicalDocument.id == document_id, MedicalDocument.user_id == user.id))
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    for collection in (document.items, document.followups, document.medications, document.timeline_events, document.questions):
        for row in list(collection):
            db.delete(row)
    if document.explanation:
        db.delete(document.explanation)
    db.commit()
    await process_document(document, db)
    loaded = db.scalar(document_query().where(MedicalDocument.id == document.id))
    return to_detail(loaded)
