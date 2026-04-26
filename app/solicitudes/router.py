from fastapi import APIRouter, Depends, Body

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_role
from app.acceso_registro.models import User
from app.talleres_tecnicos import service as taller_service
from app.talleres_tecnicos.schemas import AsignacionResponse
from app.solicitudes import service as solicitudes_service
from app.solicitudes.schemas import (
    SolicitudDisponibleResponse,
    AceptarSolicitudBody,
    SolicitudDetalleResponse,
)

router = APIRouter()


# CU13 - Ver solicitudes disponibles (antes de rutas /{id})
@router.get("/disponibles", response_model=list[SolicitudDisponibleResponse])
async def disponibles(
    current_user: User = Depends(require_role("taller")),
    db: AsyncSession = Depends(get_db),
):
    taller = await taller_service.get_taller_by_user(current_user.id, db)
    return await solicitudes_service.listar_solicitudes_disponibles(taller, db)


# CU10 - Ver estado de solicitud (detalle por id — reservado)
@router.get("/{solicitud_id}/estado")
async def ver_estado(solicitud_id: int):
    return {"msg": f"CU10 - estado solicitud {solicitud_id}"}


# CU11 - Cancelar solicitud
@router.patch("/{solicitud_id}/cancelar")
async def cancelar(solicitud_id: int):
    return {"msg": f"CU11 - cancelar solicitud {solicitud_id}"}


# CU15 - Aceptar solicitud (solicitud_id = incidente_id)
@router.patch("/{solicitud_id}/aceptar", response_model=AsignacionResponse)
async def aceptar(
    solicitud_id: int,
    data: AceptarSolicitudBody = Body(default=AceptarSolicitudBody()),
    current_user: User = Depends(require_role("taller")),
    db: AsyncSession = Depends(get_db),
):
    taller = await taller_service.get_taller_by_user(current_user.id, db)
    asig = await solicitudes_service.aceptar_solicitud(
        solicitud_id, taller, db, eta=data.eta
    )
    return AsignacionResponse.model_validate(asig)


# CU14 - Ver detalle del incidente
@router.get("/{solicitud_id}", response_model=SolicitudDetalleResponse)
async def detalle(
    solicitud_id: int,
    current_user: User = Depends(require_role("taller")),
    db: AsyncSession = Depends(get_db),
):
    taller = await taller_service.get_taller_by_user(current_user.id, db)
    return await solicitudes_service.detalle_incidente_para_taller(solicitud_id, taller, db)


# CU16 - Rechazar solicitud
@router.patch("/{solicitud_id}/rechazar")
async def rechazar(solicitud_id: int):
    return {"msg": f"CU16 - rechazar solicitud {solicitud_id}"}
