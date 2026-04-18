from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class ItemCotizacion(BaseModel):
    descripcion: str
    cantidad: int
    precio_unitario: float

    @field_validator("cantidad")
    @classmethod
    def cantidad_positiva(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return v

    @field_validator("precio_unitario")
    @classmethod
    def precio_positivo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("El precio no puede ser negativo")
        return v


class CotizacionCreate(BaseModel):
    incidente_id: int
    items: list[ItemCotizacion]

    @field_validator("items")
    @classmethod
    def items_no_vacios(cls, v: list) -> list:
        if not v:
            raise ValueError("Debes agregar al menos un ítem a la cotización")
        return v


class CotizacionEstadoUpdate(BaseModel):
    estado: str   # aceptada | rechazada

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, v: str) -> str:
        if v not in ("aceptada", "rechazada"):
            raise ValueError("Estado debe ser 'aceptada' o 'rechazada'")
        return v


class IncidenteDisponibleResponse(BaseModel):
    asignacion_id: int
    incidente_id: int
    estado_asignacion: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CotizacionResponse(BaseModel):
    id: int
    incidente_id: int
    taller_id: int
    monto_estimado: float
    detalle: Optional[str]
    estado: str
    created_at: datetime

    model_config = {"from_attributes": True}
