from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.models.models import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    location = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)