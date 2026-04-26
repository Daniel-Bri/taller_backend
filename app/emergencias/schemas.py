from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, Any


class UbicacionUpdate(BaseModel):
    latitud: float
    longitud: float


class DescripcionUpdate(BaseModel):
    descripcion: str


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
    tipo_incidente: Optional[str] = None   # §4.5 – clasificación IA
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenciaResponse(BaseModel):
    id: int
    incidente_id: int
    tipo: str
    url: Optional[str]
    analisis_ia: Optional[Any] = None
    transcripcion: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
