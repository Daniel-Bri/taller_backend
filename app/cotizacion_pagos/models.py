from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id             = Column(Integer, primary_key=True, index=True)
    incidente_id   = Column(Integer, ForeignKey("incidentes.id"), nullable=False)
    taller_id      = Column(Integer, ForeignKey("talleres.id"), nullable=False)
    monto_estimado = Column(Float, nullable=False)
    detalle        = Column(String(3000), nullable=True)   # JSON string con items
    estado         = Column(String(20), default="pendiente")  # pendiente | aceptada | rechazada
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
