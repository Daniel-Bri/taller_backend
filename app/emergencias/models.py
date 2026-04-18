from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class IncidenteFoto(Base):
    __tablename__ = "incidente_fotos"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False, index=True)
    # Ruta servida bajo /uploads/... (ej. incidentes/3/uuid.jpg)
    url_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


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
