from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class IncidenteFoto(Base):
    __tablename__ = "incidente_fotos"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False, index=True)
    # Ruta servida bajo /uploads/... (ej. incidentes/3/uuid.jpg)
    url_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IncidenteAudio(Base):
    __tablename__ = "incidente_audios"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False, index=True)
    url_path = Column(String(500), nullable=False)
    duracion_segundos = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EstadoHistorial(Base):
    __tablename__ = "estado_historial"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    estado_anterior = Column(String(30), nullable=False)
    estado_nuevo = Column(String(30), nullable=False)
    accion = Column(String(30), nullable=False)  # aceptar | rechazar | cancelar
    comentario = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClasificacionIA(Base):
    __tablename__ = "clasificaciones_ia"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id", ondelete="CASCADE"), nullable=False, index=True)
    categoria = Column(String(100), nullable=False)
    confianza = Column(Float, nullable=True)
    resumen = Column(String(500), nullable=True)
    generado_auto = Column(Boolean, default=True)
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
