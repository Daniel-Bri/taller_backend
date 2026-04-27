from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.acceso_registro.models import User
from app.db.session import get_db
from app.notificaciones.models import DispositivoToken

router = APIRouter()


class TokenPayload(BaseModel):
    token: str
    plataforma: str = "android"   # android | ios | web


@router.post("/token", status_code=status.HTTP_200_OK)
async def registrar_token(
    data: TokenPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Registra o actualiza el token FCM del dispositivo actual."""
    # Si el token pertenecía a otro usuario, eliminarlo (sesión nueva)
    await db.execute(
        delete(DispositivoToken).where(
            DispositivoToken.token == data.token,
            DispositivoToken.user_id != current_user.id,
        )
    )
    # Upsert: no duplicar si ya existe para este usuario
    res = await db.execute(
        select(DispositivoToken).where(
            DispositivoToken.token == data.token,
            DispositivoToken.user_id == current_user.id,
        )
    )
    if not res.scalar_one_or_none():
        db.add(DispositivoToken(
            user_id=current_user.id,
            token=data.token,
            plataforma=data.plataforma,
        ))
    await db.commit()
    return {"ok": True}


@router.delete("/token", status_code=status.HTTP_200_OK)
async def eliminar_token(
    data: TokenPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Elimina el token al cerrar sesión para dejar de recibir notificaciones."""
    await db.execute(
        delete(DispositivoToken).where(
            DispositivoToken.token == data.token,
            DispositivoToken.user_id == current_user.id,
        )
    )
    await db.commit()
    return {"ok": True}
