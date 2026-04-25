import json
import math
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.reportes.models import BitacoraEvento


async def log_evento(
    db: AsyncSession,
    accion: str,
    usuario_id: Optional[int] = None,
    usuario_nombre: Optional[str] = None,
    entidad: Optional[str] = None,
    entidad_id: Optional[int] = None,
    detalle: Optional[dict] = None,
    ip: Optional[str] = None,
) -> None:
    try:
        evento = BitacoraEvento(
            usuario_id=usuario_id,
            usuario_nombre=usuario_nombre,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=json.dumps(detalle, default=str, ensure_ascii=False) if detalle else None,
            ip=ip,
        )
        db.add(evento)
        await db.commit()
    except Exception:
        await db.rollback()


async def listar_eventos(
    db: AsyncSession,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    accion: Optional[str] = None,
    usuario_id: Optional[int] = None,
    page: int = 1,
    size: int = 50,
) -> tuple[list[BitacoraEvento], int]:
    filters = []
    if desde:
        filters.append(BitacoraEvento.created_at >= desde)
    if hasta:
        filters.append(BitacoraEvento.created_at <= hasta)
    if accion:
        filters.append(BitacoraEvento.accion == accion)
    if usuario_id:
        filters.append(BitacoraEvento.usuario_id == usuario_id)

    base_q = select(BitacoraEvento)
    if filters:
        base_q = base_q.where(and_(*filters))

    count_result = await db.execute(
        select(func.count()).select_from(base_q.subquery())
    )
    total = count_result.scalar_one()

    query = base_q.order_by(desc(BitacoraEvento.created_at)).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def obtener_evento(evento_id: int, db: AsyncSession) -> Optional[BitacoraEvento]:
    result = await db.execute(select(BitacoraEvento).where(BitacoraEvento.id == evento_id))
    return result.scalar_one_or_none()


async def exportar_csv(
    db: AsyncSession,
    desde: Optional[datetime] = None,
    hasta: Optional[datetime] = None,
    accion: Optional[str] = None,
    usuario_id: Optional[int] = None,
) -> str:
    eventos, _ = await listar_eventos(db, desde, hasta, accion, usuario_id, page=1, size=10000)
    lines = ["id,fecha_hora,usuario,accion,entidad,entidad_id,ip,detalle"]
    for e in eventos:
        det = (e.detalle or "").replace('"', "'").replace("\n", " ")
        fecha = e.created_at.strftime("%Y-%m-%d %H:%M:%S") if e.created_at else ""
        lines.append(
            f'{e.id},{fecha},"{e.usuario_nombre or ""}",{e.accion},"{e.entidad or ""}",{e.entidad_id or ""},'
            f'{e.ip or ""},"{det}"'
        )
    return "\n".join(lines)
