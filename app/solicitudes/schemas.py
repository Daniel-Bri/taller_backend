from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class AceptarSolicitudBody(BaseModel):
    """CU15 – opcional: ETA estimada en minutos."""

    eta: Optional[int] = None

    @field_validator("eta")
    @classmethod
    def eta_valida(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        if v < 1 or v > 24 * 60:
            raise ValueError("La ETA debe estar entre 1 y 1440 minutos")
        return v


class SolicitudDisponibleResponse(BaseModel):
    incidente_id: int
    latitud: float
    longitud: float
    descripcion: Optional[str]
    tipo_problema: str
    prioridad: str
    estado: str
    fotos_urls: list[str]
    tiene_audio: bool = False
    created_at: datetime
