from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class UbicacionUpdate(BaseModel):
    latitud: float
    longitud: float


class IncidenteCreate(BaseModel):
    vehiculo_id: int
    descripcion: Optional[str] = None
    prioridad: Optional[str] = "media"

    @field_validator("prioridad")
    @classmethod
    def prioridad_valida(cls, v: str) -> str:
        if v not in ("alta", "media", "baja"):
            raise ValueError("La prioridad debe ser alta, media o baja")
        return v


class IncidenteResponse(BaseModel):
    id: int
    usuario_id: int
    vehiculo_id: int
    latitud: Optional[float]
    longitud: Optional[float]
    descripcion: Optional[str]
    estado: str
    prioridad: str
    created_at: datetime

    model_config = {"from_attributes": True}
