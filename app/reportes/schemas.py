from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BitacoraEventoResponse(BaseModel):
    id: int
    usuario_id: Optional[int]
    usuario_nombre: Optional[str]
    accion: str
    entidad: Optional[str]
    entidad_id: Optional[int]
    detalle: Optional[str]
    ip: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditoriaListResponse(BaseModel):
    items: list[BitacoraEventoResponse]
    total: int
    page: int
    size: int
    pages: int
