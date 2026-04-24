from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class Mensaje(Base):
    __tablename__ = "mensajes"

    id            = Column(Integer, primary_key=True, index=True)
    asignacion_id = Column(Integer, ForeignKey("asignaciones.id"), nullable=False)
    usuario_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    contenido     = Column(String(2000), nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
