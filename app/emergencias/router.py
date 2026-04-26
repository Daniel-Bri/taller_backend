from fastapi import APIRouter, Depends, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.acceso_registro.models import User
from app.emergencias import schemas, service
from app.emergencias.schemas import (
    IncidenteResponse,
    UbicacionUpdate,
    DescripcionUpdate,
    GestionSolicitudPayload,
    GestionSolicitudResponse,
)
from app.emergencias.service import public_foto_url, public_audio_url

router = APIRouter()


# ── CU05 - Reportar emergencia ─────────────────────────────
@router.post("/", response_model=IncidenteResponse, status_code=status.HTTP_201_CREATED)
async def reportar_emergencia(
    data: schemas.IncidenteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incidente = await service.crear_incidente(data, current_user.id, db)
    return IncidenteResponse.model_validate(incidente)


# ── Listar mis incidentes ──────────────────────────────────
@router.get("/mis-incidentes", response_model=list[IncidenteResponse])
async def listar_mis_incidentes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incidentes = await service.listar_incidentes_usuario(current_user.id, db)
    return [IncidenteResponse.model_validate(i) for i in incidentes]


# ── CU10 · Mis solicitudes (incidente + asignación + fotos) ─
@router.get("/mis-solicitudes", response_model=list[schemas.MisSolicitudItem])
async def mis_solicitudes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.listar_mis_solicitudes_cliente(current_user.id, db)


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
@router.post(
    "/{incidente_id}/fotos",
    response_model=schemas.IncidenteFotoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def adjuntar_fotos(
    incidente_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    row = await service.adjuntar_foto_incidente(incidente_id, current_user.id, file, db)
    return schemas.IncidenteFotoResponse(
        id=row.id,
        incidente_id=row.incidente_id,
        url=public_foto_url(row.url_path),
        created_at=row.created_at,
    )


# ── CU08 - Enviar audio ────────────────────────────────────
@router.post(
    "/{incidente_id}/audio",
    response_model=schemas.IncidenteAudioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enviar_audio(
    incidente_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    duracion_segundos: int | None = Form(default=None),
):
    row = await service.adjuntar_audio_incidente(
        incidente_id=incidente_id,
        usuario_id=current_user.id,
        file=file,
        duracion_segundos=duracion_segundos,
        db=db,
    )
    return schemas.IncidenteAudioResponse(
        id=row.id,
        incidente_id=row.incidente_id,
        url=public_audio_url(row.url_path),
        duracion_segundos=row.duracion_segundos,
        created_at=row.created_at,
    )


# ── CU09 - Agregar descripción texto ──────────────────────
@router.patch("/{incidente_id}/descripcion", response_model=IncidenteResponse)
async def agregar_descripcion(
    incidente_id: int,
    data: DescripcionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    incidente = await service.actualizar_descripcion(incidente_id, current_user.id, data, db)
    return IncidenteResponse.model_validate(incidente)


# ── CU11 - Gestionar solicitud (cliente) ───────────────────
@router.put("/{incidente_id}/estado", response_model=GestionSolicitudResponse)
async def gestionar_solicitud(
    incidente_id: int,
    data: GestionSolicitudPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.gestionar_solicitud_cliente(
        incidente_id=incidente_id,
        usuario_id=current_user.id,
        data=data,
        db=db,
    )
