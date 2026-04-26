from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.comunicacion.models import Notificacion


async def crear_notificacion(
    user_id: int,
    titulo: str,
    mensaje: str,
    tipo: str,
    incidente_id: int | None,
    db: AsyncSession,
    commit: bool = True,
) -> Notificacion:
    row = Notificacion(
        user_id=user_id,
        incidente_id=incidente_id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        leida=False,
    )
    db.add(row)
    if commit:
        await db.commit()
        await db.refresh(row)
    return row


async def listar_notificaciones_usuario(user_id: int, db: AsyncSession) -> list[Notificacion]:
    result = await db.execute(
        select(Notificacion)
        .where(Notificacion.user_id == user_id)
        .order_by(Notificacion.created_at.desc())
    )
    return list(result.scalars().all())


async def marcar_leida(notificacion_id: int, user_id: int, db: AsyncSession) -> Notificacion | None:
    result = await db.execute(
        select(Notificacion).where(
            Notificacion.id == notificacion_id,
            Notificacion.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    row.leida = True
    await db.commit()
    await db.refresh(row)
    return row
