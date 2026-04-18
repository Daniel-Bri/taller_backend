import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.cotizacion_pagos.models import Cotizacion
from app.talleres_tecnicos.models import Asignacion
from app.acceso_registro.models import Taller
from app.cotizacion_pagos.schemas import CotizacionCreate, IncidenteDisponibleResponse


async def _get_taller(user_id: int, db: AsyncSession) -> Taller:
    result = await db.execute(
        select(Taller).where(Taller.usuario_id == user_id, Taller.estado == "aprobado")
    )
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=403, detail="No tienes un taller aprobado")
    return taller


# ── CU20 · Incidentes disponibles para cotizar ─────────────
async def listar_incidentes_disponibles(taller_id: int, db: AsyncSession) -> list[IncidenteDisponibleResponse]:
    # Asignaciones aceptadas del taller
    result = await db.execute(
        select(Asignacion).where(
            Asignacion.taller_id == taller_id,
            Asignacion.estado == "aceptado",
        )
    )
    asignaciones = list(result.scalars().all())

    # Incidentes que ya tienen cotización de este taller
    result = await db.execute(
        select(Cotizacion.incidente_id).where(Cotizacion.taller_id == taller_id)
    )
    ya_cotizados = {row for row in result.scalars().all()}

    return [
        IncidenteDisponibleResponse(
            asignacion_id=a.id,
            incidente_id=a.incidente_id,
            estado_asignacion=a.estado,
            created_at=a.created_at,
        )
        for a in asignaciones
        if a.incidente_id not in ya_cotizados
    ]


# ── CU20 · Generar cotización ──────────────────────────────
async def generar_cotizacion(taller_id: int, data: CotizacionCreate, db: AsyncSession) -> Cotizacion:
    # Verificar que la asignación le pertenece al taller
    result = await db.execute(
        select(Asignacion).where(
            Asignacion.incidente_id == data.incidente_id,
            Asignacion.taller_id == taller_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Este incidente no está asignado a tu taller")

    # Verificar que no existe ya una cotización
    result = await db.execute(
        select(Cotizacion).where(
            Cotizacion.incidente_id == data.incidente_id,
            Cotizacion.taller_id == taller_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe una cotización para este incidente")

    monto_total = sum(item.cantidad * item.precio_unitario for item in data.items)
    detalle_json = json.dumps([item.model_dump() for item in data.items], ensure_ascii=False)

    cotizacion = Cotizacion(
        incidente_id=data.incidente_id,
        taller_id=taller_id,
        monto_estimado=round(monto_total, 2),
        detalle=detalle_json,
    )
    db.add(cotizacion)
    await db.commit()
    await db.refresh(cotizacion)
    return cotizacion


# ── CU20 · Listar cotizaciones del taller ─────────────────
async def listar_cotizaciones(taller_id: int, db: AsyncSession) -> list[Cotizacion]:
    result = await db.execute(
        select(Cotizacion)
        .where(Cotizacion.taller_id == taller_id)
        .order_by(Cotizacion.created_at.desc())
    )
    return list(result.scalars().all())


# ── CU20 · Ver cotización por ID ───────────────────────────
async def get_cotizacion(cotizacion_id: int, db: AsyncSession) -> Cotizacion:
    result = await db.execute(select(Cotizacion).where(Cotizacion.id == cotizacion_id))
    cotizacion = result.scalar_one_or_none()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return cotizacion


# ── CU20 · Confirmar / Rechazar ────────────────────────────
async def actualizar_estado(cotizacion_id: int, nuevo_estado: str, db: AsyncSession) -> Cotizacion:
    cotizacion = await get_cotizacion(cotizacion_id, db)
    if cotizacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Solo se pueden confirmar cotizaciones en estado pendiente")
    cotizacion.estado = nuevo_estado
    await db.commit()
    await db.refresh(cotizacion)
    return cotizacion
