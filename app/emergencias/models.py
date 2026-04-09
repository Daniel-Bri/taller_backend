from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class Incidente(Base):
    __tablename__ = "incidentes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vehiculo_id = Column(Integer, ForeignKey("vehiculos.id"), nullable=False)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    descripcion = Column(String(1000), nullable=True)
    estado = Column(String(20), default="pendiente")     # pendiente | en_proceso | resuelto | cancelado
    prioridad = Column(String(20), default="media")      # alta | media | baja
    created_at = Column(DateTime(timezone=True), server_default=func.now())
