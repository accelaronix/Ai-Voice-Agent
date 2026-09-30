from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.scheduler.call_scheduler import scheduler, fake_ai_call

from app.database.db import SessionLocal
from app.database.models import Lead


router = APIRouter(
    prefix="/leads",
    tags=["Leads"]
)


class LeadCreate(BaseModel):
    name: str
    phone: str
    source: str | None = None


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("")
def create_lead(
    data: LeadCreate,
    db: Session = Depends(get_db)
):
    call_time = datetime.now(timezone.utc) + timedelta(seconds=10)

    lead = Lead(
        name=data.name,
        phone=data.phone,
        source=data.source,
        status="scheduled",
        call_at=call_time
    )

    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    scheduler.add_job(
        fake_ai_call,
        "date",
        run_date=call_time,
        args=[
            lead.id,
            lead.name,
            lead.phone
        ]
    )

    return {
        "id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "source": lead.source,
        "status": lead.status,
        "call_at": lead.call_at
    }