from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import DocumentStatus, FollowUp, MedicalDocument, Medication, User
from ..schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardStats)
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardStats:
    documents = list(db.scalars(select(MedicalDocument).where(MedicalDocument.user_id == user.id).order_by(MedicalDocument.uploaded_at.desc())))
    followups = list(db.scalars(select(FollowUp).join(MedicalDocument).where(MedicalDocument.user_id == user.id, FollowUp.status == "pending").order_by(FollowUp.due_date.asc().nullslast())))
    medication_count = db.scalar(select(func.count(Medication.id)).join(MedicalDocument).where(MedicalDocument.user_id == user.id)) or 0
    return DashboardStats(
        document_count=len(documents),
        ready_count=sum(document.status == DocumentStatus.ready for document in documents),
        needs_review_count=sum(document.status == DocumentStatus.needs_review for document in documents),
        pending_followups=len(followups),
        medication_count=medication_count,
        recent_documents=documents[:5],
        upcoming_followups=followups[:5],
    )

