from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.comunicacion import service, schemas
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.acceso_registro.models import User

router = APIRouter()


# CU20 - Ver técnico en mapa
@router.get("/tecnicos/{tecnico_id}/ubicacion")
async def ubicacion_tecnico(tecnico_id: int):
    return {"msg": f"CU20 - ubicacion tecnico {tecnico_id}"}


# CU21 - Chatear en tiempo real
@router.post("/mensajes")
async def enviar_mensaje():
    return {"msg": "CU21 - enviar mensaje"}


@router.get("/mensajes/{solicitud_id}")
async def listar_mensajes(solicitud_id: int):
    return {"msg": f"CU21 - mensajes solicitud {solicitud_id}"}


# CU19 - Recibir notificaciones (móvil + web)
@router.get("/notificaciones/mias", response_model=list[schemas.NotificacionResponse])
async def notificaciones_mias(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await service.listar_notificaciones_usuario(current_user.id, db)
    return [schemas.NotificacionResponse.model_validate(n) for n in rows]


@router.patch("/notificaciones/{notificacion_id}/leida", response_model=schemas.NotificacionResponse)
async def marcar_leida(
    notificacion_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await service.marcar_leida(notificacion_id, current_user.id, db)
    if not row:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    return schemas.NotificacionResponse.model_validate(row)
