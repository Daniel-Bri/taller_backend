from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_role
from app.acceso_registro.models import User
from app.cotizacion_pagos import schemas, service

router = APIRouter()


# ── CU20 · Incidentes disponibles para cotizar ─────────────
@router.get("/incidentes-disponibles", response_model=list[schemas.IncidenteDisponibleResponse])
async def incidentes_disponibles(
    current_user: User = Depends(require_role("taller")),
    db: AsyncSession = Depends(get_db),
):
    from app.talleres_tecnicos.service import get_taller_by_user
    taller = await get_taller_by_user(current_user.id, db)
    return await service.listar_incidentes_disponibles(taller.id, db)


# ── CU20 · Generar cotización ──────────────────────────────
@router.post("/cotizaciones", response_model=schemas.CotizacionResponse, status_code=status.HTTP_201_CREATED)
async def generar_cotizacion(
    data: schemas.CotizacionCreate,
    current_user: User = Depends(require_role("taller")),
    db: AsyncSession = Depends(get_db),
):
    from app.talleres_tecnicos.service import get_taller_by_user
    taller = await get_taller_by_user(current_user.id, db)
    cotizacion = await service.generar_cotizacion(taller.id, data, db)
    return schemas.CotizacionResponse.model_validate(cotizacion)


# ── CU20 · Listar cotizaciones del taller ─────────────────
@router.get("/cotizaciones", response_model=list[schemas.CotizacionResponse])
async def listar_cotizaciones(
    current_user: User = Depends(require_role("taller")),
    db: AsyncSession = Depends(get_db),
):
    from app.talleres_tecnicos.service import get_taller_by_user
    taller = await get_taller_by_user(current_user.id, db)
    cotizaciones = await service.listar_cotizaciones(taller.id, db)
    return [schemas.CotizacionResponse.model_validate(c) for c in cotizaciones]


# ── CU20 · Ver cotización por ID ───────────────────────────
@router.get("/cotizaciones/{cotizacion_id}", response_model=schemas.CotizacionResponse)
async def ver_cotizacion(
    cotizacion_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cotizacion = await service.get_cotizacion(cotizacion_id, db)
    return schemas.CotizacionResponse.model_validate(cotizacion)


# ── CU20 · Confirmar / Rechazar cotización ─────────────────
@router.patch("/cotizaciones/{cotizacion_id}/estado", response_model=schemas.CotizacionResponse)
async def actualizar_estado_cotizacion(
    cotizacion_id: int,
    data: schemas.CotizacionEstadoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cotizacion = await service.actualizar_estado(cotizacion_id, data.estado, db)
    return schemas.CotizacionResponse.model_validate(cotizacion)


# ── CU26 stub · Realizar pago ──────────────────────────────
@router.post("/pagos")
async def realizar_pago():
    return {"msg": "CU26 - realizar pago"}


# ── Stub · Ver comisiones ──────────────────────────────────
@router.get("/comisiones")
async def ver_comisiones():
    return {"msg": "CU32 - ver comisiones"}
