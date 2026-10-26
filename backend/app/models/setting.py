from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.database.session import Base

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False) # JSON serialized
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
