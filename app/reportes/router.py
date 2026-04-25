import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_role
from app.acceso_registro.models import User
from app.reportes import schemas, service

router = APIRouter()


# ── CU28 - Calificar servicio ──────────────────────────────
@router.post("/{solicitud_id}/calificacion")
async def calificar_servicio(solicitud_id: int):
    return {"msg": f"CU28 - calificar servicio {solicitud_id}"}


# ── CU29 - Ver historial de servicios ─────────────────────
@router.get("/historial")
async def historial():
    return {"msg": "CU29 - historial de servicios"}


# ── Métricas del taller ───────────────────────────────────
@router.get("/metricas/taller")
async def metricas_taller():
    return {"msg": "metricas del taller"}


# ── Métricas globales ─────────────────────────────────────
@router.get("/metricas/globales")
async def metricas_globales():
    return {"msg": "metricas globales"}


# ── CU35 - Auditoría / Bitácora ────────────────────────────
@router.get("/auditoria", response_model=schemas.AuditoriaListResponse)
async def listar_auditoria(
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    accion: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await service.listar_eventos(db, desde, hasta, accion, usuario_id, page, size)
    pages = math.ceil(total / size) if total > 0 else 1
    return schemas.AuditoriaListResponse(
        items=[schemas.BitacoraEventoResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/auditoria/exportar")
async def exportar_auditoria(
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
    accion: Optional[str] = Query(None),
    usuario_id: Optional[int] = Query(None),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    csv_content = await service.exportar_csv(db, desde, hasta, accion, usuario_id)
    headers = {
        "Content-Disposition": "attachment; filename=auditoria.csv",
        "Content-Type": "text/csv; charset=utf-8",
    }
    return Response(content=csv_content.encode("utf-8"), headers=headers)


@router.get("/auditoria/{evento_id}", response_model=schemas.BitacoraEventoResponse)
async def detalle_evento(
    evento_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    evento = await service.obtener_evento(evento_id, db)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return schemas.BitacoraEventoResponse.model_validate(evento)
