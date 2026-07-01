from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Meetings

router = APIRouter(
    prefix="/meetings",
    tags=["meetings"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create")
async def create_meeting(title: str,summary: str,db: Session = Depends(get_db)):
    meeting = Meetings(
        title=title,
        summary=summary
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting