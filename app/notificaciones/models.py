from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class DispositivoToken(Base):
    __tablename__ = "dispositivo_tokens"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token       = Column(String(500), nullable=False, unique=True)
    plataforma  = Column(String(20), default="android")   # android | ios | web
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
