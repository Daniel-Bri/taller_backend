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

    @field_validator("descripcion")
    @classmethod
    def descripcion_longitud(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if len(s) > 1000:
            raise ValueError("La descripción no puede exceder 1000 caracteres")
        return s if s else None

    @field_validator("prioridad")
    @classmethod
    def prioridad_valida(cls, v: str) -> str:
        if v not in ("alta", "media", "baja"):
            raise ValueError("La prioridad debe ser alta, media o baja")
        return v


class DescripcionUpdate(BaseModel):
    descripcion: Optional[str] = None

    @field_validator("descripcion")
    @classmethod
    def descripcion_longitud(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        s = v.strip()
        if len(s) > 1000:
            raise ValueError("La descripción no puede exceder 1000 caracteres")
        return s if s else None


class IncidenteFotoResponse(BaseModel):
    id: int
    incidente_id: int
    url: str
    created_at: datetime


class AsignacionResumenCliente(BaseModel):
    id: int
    estado: str
    eta: Optional[int] = None
    taller_nombre: str


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


class MisSolicitudItem(BaseModel):
    incidente: IncidenteResponse
    asignacion: Optional[AsignacionResumenCliente] = None
    fotos_urls: list[str] = []
