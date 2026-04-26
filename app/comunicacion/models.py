from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func

from app.db.base import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id"), nullable=True, index=True)
    tipo = Column(String(50), nullable=False, default="general")
    titulo = Column(String(200), nullable=False)
    mensaje = Column(String(500), nullable=False)
    leida = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
