from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.report import Report

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/reports")
def create_report(location: str, description: str, db: Session = Depends(get_db)):
    report = Report(location=location, description=description)

    db.add(report)
    db.commit()
    db.refresh(report)

    return report