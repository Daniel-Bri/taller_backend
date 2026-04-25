from typing import Any, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.acceso_registro.models import User
from app.emergencias import schemas, service
from app.emergencias.schemas import IncidenteResponse, UbicacionUpdate

router = APIRouter()


class SOSCreate(BaseModel):
    latitud: Optional[float] = None
    longitud: Optional[float] = None


# ── CU05 - Reportar emergencia ─────────────────────────────
@router.post("/", response_model=IncidenteResponse, status_code=status.HTTP_201_CREATED)
async def reportar_emergencia(
    data: schemas.IncidenteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incidente = await service.crear_incidente(data, current_user.id, db)
    return IncidenteResponse.model_validate(incidente)


# ── CU10 - Mis solicitudes (incidente + asignación + fotos) ───────────────
@router.get("/mis-solicitudes", response_model=list[dict[str, Any]])
async def listar_mis_solicitudes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_mis_solicitudes(current_user.id, db)


# ── Listar mis incidentes ──────────────────────────────────
@router.get("/mis-incidentes", response_model=list[IncidenteResponse])
async def listar_mis_incidentes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incidentes = await service.listar_incidentes_usuario(current_user.id, db)
    return [IncidenteResponse.model_validate(i) for i in incidentes]


# ── CU06 - Enviar ubicación GPS ────────────────────────────
@router.patch("/{incidente_id}/ubicacion", response_model=IncidenteResponse)
async def enviar_ubicacion(
    incidente_id: int,
    data: UbicacionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incidente = await service.actualizar_ubicacion(incidente_id, current_user.id, data, db)
    return IncidenteResponse.model_validate(incidente)


# ── CU07 - Adjuntar fotos ──────────────────────────────────
@router.post("/{incidente_id}/fotos")
async def adjuntar_fotos(incidente_id: int):
    return {"msg": f"CU07 - fotos emergencia {incidente_id}"}


# ── CU08 - Enviar audio ────────────────────────────────────
@router.post("/{incidente_id}/audio")
async def enviar_audio(incidente_id: int):
    return {"msg": f"CU08 - audio emergencia {incidente_id}"}


# ── CU09 - Agregar descripción texto ──────────────────────
@router.patch("/{incidente_id}/descripcion")
async def agregar_descripcion(incidente_id: int):
    return {"msg": f"CU09 - descripcion emergencia {incidente_id}"}


# ── CU30 - Botón SOS ──────────────────────────────────────
@router.post("/sos", response_model=IncidenteResponse, status_code=status.HTTP_201_CREATED)
async def boton_sos(
    data: SOSCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incidente = await service.crear_incidente_sos(
        current_user.id, data.latitud, data.longitud, db
    )
    return IncidenteResponse.model_validate(incidente)
