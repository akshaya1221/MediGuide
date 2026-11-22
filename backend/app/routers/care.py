from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import ConsultationQuestion, FollowUp, MedicalDocument, Medication, TimelineEvent, User
from ..schemas import FollowUpRead, FollowUpUpdate, MedicationRead, QuestionRead, TimelineRead

router = APIRouter(prefix="/care", tags=["Care organization"])


@router.get("/follow-ups", response_model=list[FollowUpRead])
def followups(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[FollowUp]:
    query = select(FollowUp).join(MedicalDocument).where(MedicalDocument.user_id == user.id).order_by(FollowUp.due_date.asc().nullslast())
    return list(db.scalars(query))


@router.patch("/follow-ups/{followup_id}", response_model=FollowUpRead)
def update_followup(followup_id: str, payload: FollowUpUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> FollowUp:
    item = db.scalar(select(FollowUp).join(MedicalDocument).where(FollowUp.id == followup_id, MedicalDocument.user_id == user.id))
    if not item:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.get("/medications", response_model=list[MedicationRead])
def medications(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Medication]:
    return list(db.scalars(select(Medication).join(MedicalDocument).where(MedicalDocument.user_id == user.id).order_by(Medication.name)))


@router.get("/timeline", response_model=list[TimelineRead])
def timeline(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TimelineEvent]:
    return list(db.scalars(select(TimelineEvent).join(MedicalDocument).where(MedicalDocument.user_id == user.id).order_by(TimelineEvent.event_date.desc())))


@router.get("/questions", response_model=list[QuestionRead])
def questions(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ConsultationQuestion]:
    return list(db.scalars(select(ConsultationQuestion).where(ConsultationQuestion.user_id == user.id).order_by(ConsultationQuestion.created_at.desc())))

