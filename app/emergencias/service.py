import uuid
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, UploadFile

from app.emergencias.models import (
    Incidente,
    IncidenteFoto,
    IncidenteAudio,
    EstadoHistorial,
    ClasificacionIA,
)
from app.emergencias.schemas import (
    IncidenteCreate,
    UbicacionUpdate,
    DescripcionUpdate,
    IncidenteResponse,
    MisSolicitudItem,
    AsignacionResumenCliente,
    GestionSolicitudPayload,
    GestionSolicitudResponse,
)
from app.acceso_registro.models import Vehiculo, Taller, User
from app.talleres_tecnicos.models import Asignacion
from app.comunicacion import service as notif_service
from app.ia import service as ia_service

_UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads"

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
}
MAX_AUDIO_BYTES = 15 * 1024 * 1024


def get_upload_root() -> Path:
    _UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return _UPLOAD_ROOT


def public_foto_url(stored_path: str) -> str:
    p = stored_path.strip().lstrip("/")
    return f"/uploads/{p}"


def public_audio_url(stored_path: str) -> str:
    p = stored_path.strip().lstrip("/")
    return f"/uploads/{p}"


async def _upsert_clasificacion_ia(
    incidente: Incidente,
    db: AsyncSession,
    categoria: str | None = None,
    confianza: float | None = None,
    resumen_extra: str | None = None,
) -> None:
    result = await db.execute(
        select(ClasificacionIA)
        .where(ClasificacionIA.incidente_id == incidente.id)
        .order_by(ClasificacionIA.created_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        row = ClasificacionIA(
            incidente_id=incidente.id,
            categoria=categoria or "otros",
            confianza=confianza if confianza is not None else 0.5,
            resumen=resumen_extra or "Clasificación inicial automática",
            generado_auto=True,
        )
        db.add(row)
        await db.commit()
        return
    if categoria:
        row.categoria = categoria
    if confianza is not None:
        row.confianza = confianza
    if resumen_extra:
        base = (row.resumen or "").strip()
        row.resumen = f"{base}\n{resumen_extra}".strip() if base else resumen_extra
    await db.commit()


async def _notificar_talleres_nueva_solicitud(incidente: Incidente, db: AsyncSession) -> None:
    result = await db.execute(
        select(User.id)
        .join(Taller, Taller.usuario_id == User.id)
        .where(User.role == "taller", User.is_active == True, Taller.estado == "aprobado")
    )
    talleres_user_ids = [r[0] for r in result.all()]
    for uid in talleres_user_ids:
        await notif_service.crear_notificacion(
            user_id=uid,
            titulo="Nueva solicitud disponible",
            mensaje=f"Incidente #{incidente.id} pendiente para atención",
            tipo="nueva_solicitud",
            incidente_id=incidente.id,
            db=db,
            commit=False,
        )


async def crear_incidente(
    data: IncidenteCreate, usuario_id: int, db: AsyncSession
) -> Incidente:
    # Verificar que el vehículo pertenece al usuario
    result = await db.execute(
        select(Vehiculo).where(
            Vehiculo.id == data.vehiculo_id,
            Vehiculo.usuario_id == usuario_id,
            Vehiculo.activo == True,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vehículo no encontrado o no pertenece al usuario")

    incidente = Incidente(
        usuario_id=usuario_id,
        vehiculo_id=data.vehiculo_id,
        descripcion=data.descripcion,
        prioridad=data.prioridad or "media",
    )
    db.add(incidente)
    await db.commit()
    await db.refresh(incidente)
    await _notificar_talleres_nueva_solicitud(incidente, db)
    await _upsert_clasificacion_ia(
        incidente=incidente,
        db=db,
        categoria="otros",
        confianza=0.5,
        resumen_extra="Clasificación inicial automática pendiente de evidencias",
    )
    return incidente


async def listar_incidentes_usuario(usuario_id: int, db: AsyncSession) -> list[Incidente]:
    result = await db.execute(
        select(Incidente)
        .where(Incidente.usuario_id == usuario_id)
        .order_by(Incidente.created_at.desc())
    )
    return list(result.scalars().all())


async def obtener_incidente(incidente_id: int, db: AsyncSession) -> Incidente:
    result = await db.execute(select(Incidente).where(Incidente.id == incidente_id))
    incidente = result.scalar_one_or_none()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    return incidente


async def _incidente_de_usuario(
    incidente_id: int, usuario_id: int, db: AsyncSession
) -> Incidente:
    result = await db.execute(
        select(Incidente).where(
            Incidente.id == incidente_id,
            Incidente.usuario_id == usuario_id,
        )
    )
    incidente = result.scalar_one_or_none()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    return incidente


async def actualizar_descripcion(
    incidente_id: int, usuario_id: int, data: DescripcionUpdate, db: AsyncSession
) -> Incidente:
    incidente = await _incidente_de_usuario(incidente_id, usuario_id, db)
    if data.descripcion is not None:
        incidente.descripcion = data.descripcion
    await db.commit()
    await db.refresh(incidente)
    return incidente


async def adjuntar_foto_incidente(
    incidente_id: int, usuario_id: int, file: UploadFile, db: AsyncSession
) -> IncidenteFoto:
    incidente = await _incidente_de_usuario(incidente_id, usuario_id, db)
    ctype = (file.content_type or "").split(";")[0].strip().lower()
    if ctype not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Formato no válido. Use JPEG, PNG o WEBP",
        )
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 5 MB")
    ext = ALLOWED_IMAGE_TYPES[ctype]
    root = get_upload_root()
    sub = root / "incidentes" / str(incidente_id)
    sub.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    (sub / fname).write_bytes(data)
    rel = f"incidentes/{incidente_id}/{fname}"
    row = IncidenteFoto(incidente_id=incidente.id, url_path=rel)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    # IA imagen: labels -> categoría
    cls = await ia_service.clasificar_imagen(sub / fname)
    if cls.get("ok"):
        labels = ", ".join(cls.get("labels") or [])
        await _upsert_clasificacion_ia(
            incidente=incidente,
            db=db,
            categoria=cls.get("categoria"),
            resumen_extra=f"Análisis de imagen: {labels}" if labels else "Análisis de imagen completado",
        )
    return row


async def adjuntar_audio_incidente(
    incidente_id: int,
    usuario_id: int,
    file: UploadFile,
    db: AsyncSession,
    duracion_segundos: int | None = None,
) -> IncidenteAudio:
    incidente = await _incidente_de_usuario(incidente_id, usuario_id, db)
    ctype = (file.content_type or "").split(";")[0].strip().lower()
    if ctype not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Formato de audio no válido. Use mp3/wav/m4a/webm/ogg",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Audio corrupto o vacío")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=400, detail="El audio no puede superar 15 MB")
    ext = ALLOWED_AUDIO_TYPES[ctype]
    root = get_upload_root()
    sub = root / "audios" / str(incidente_id)
    sub.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    (sub / fname).write_bytes(data)
    rel = f"audios/{incidente_id}/{fname}"
    row = IncidenteAudio(
        incidente_id=incidente.id,
        url_path=rel,
        duracion_segundos=duracion_segundos,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    # IA audio: transcripción + resumen automático.
    tr = await ia_service.transcribir_audio(sub / fname)
    transcripcion = tr.get("text")
    if transcripcion:
        rs = await ia_service.resumir_incidente(
            texto_usuario=incidente.descripcion,
            transcripcion=transcripcion,
            categoria=None,
        )
        resumen = rs.get("resumen") or f"Transcripción audio: {transcripcion[:250]}"
        await _upsert_clasificacion_ia(
            incidente=incidente,
            db=db,
            categoria=rs.get("categoria"),
            confianza=rs.get("confianza"),
            resumen_extra=f"Audio->texto: {transcripcion}\nResumen IA: {resumen}",
        )
    return row


def _estado_incidente_desde_accion(accion: str) -> str:
    # "aceptado" aplica sobre asignación/taller y mantiene el incidente en proceso.
    # "rechazado/cancelado" terminan la solicitud para este flujo simplificado.
    return {
        "aceptado": "en_proceso",
        "rechazado": "cancelado",
        "cancelado": "cancelado",
    }[accion]


async def gestionar_solicitud_cliente(
    incidente_id: int,
    usuario_id: int,
    data: GestionSolicitudPayload,
    db: AsyncSession,
) -> GestionSolicitudResponse:
    incidente = await _incidente_de_usuario(incidente_id, usuario_id, db)
    estado_anterior = incidente.estado

    if estado_anterior in ("resuelto", "cancelado"):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede actualizar una solicitud en estado '{estado_anterior}'",
        )
    ar = await db.execute(
        select(Asignacion, Taller.usuario_id)
        .join(Taller, Taller.id == Asignacion.taller_id)
        .where(Asignacion.incidente_id == incidente.id)
        .order_by(Asignacion.created_at.desc())
        .limit(1)
    )
    row = ar.first()

    # Regla de negocio: sin taller asignado solo se permite cancelar.
    if data.estado in ("aceptado", "rechazado") and not row:
        raise HTTPException(
            status_code=400,
            detail="Aún no hay taller asignado. Solo puedes cancelar la solicitud por ahora.",
        )

    estado_nuevo = _estado_incidente_desde_accion(data.estado)
    if estado_anterior == estado_nuevo:
        raise HTTPException(
            status_code=400,
            detail=f"La solicitud ya se encuentra en estado '{estado_nuevo}'",
        )

    incidente.estado = estado_nuevo
    hist = EstadoHistorial(
        incidente_id=incidente.id,
        usuario_id=usuario_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        accion=data.estado,
        comentario=data.comentario,
    )
    db.add(hist)

    # Notificar al taller asignado más reciente si existe.
    if row:
        _, taller_user_id = row[0], row[1]
        await notif_service.crear_notificacion(
            user_id=taller_user_id,
            titulo="Cambio en solicitud",
            mensaje=f"El cliente actualizó la solicitud #{incidente.id} a '{estado_nuevo}'",
            tipo="estado_actualizado",
            incidente_id=incidente.id,
            db=db,
            commit=False,
        )

    await db.commit()
    await db.refresh(incidente)
    return GestionSolicitudResponse(
        incidente_id=incidente.id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        accion=data.estado,
        updated_at=datetime.now(timezone.utc),
    )


async def listar_mis_solicitudes_cliente(
    usuario_id: int, db: AsyncSession
) -> list[MisSolicitudItem]:
    incidentes = await listar_incidentes_usuario(usuario_id, db)
    if not incidentes:
        return []
    ids = [i.id for i in incidentes]
    fr = await db.execute(select(IncidenteFoto).where(IncidenteFoto.incidente_id.in_(ids)))
    fotos_list = list(fr.scalars().all())
    ar = await db.execute(select(IncidenteAudio).where(IncidenteAudio.incidente_id.in_(ids)))
    audios_list = list(ar.scalars().all())
    by_fotos: dict[int, list[str]] = defaultdict(list)
    for f in fotos_list:
        by_fotos[f.incidente_id].append(public_foto_url(f.url_path))
    by_audios: dict[int, list[str]] = defaultdict(list)
    for a in audios_list:
        by_audios[a.incidente_id].append(public_audio_url(a.url_path))

    out: list[MisSolicitudItem] = []
    for inc in incidentes:
        ar = await db.execute(
            select(Asignacion, Taller.nombre, Taller.latitud, Taller.longitud)
            .join(Taller, Taller.id == Asignacion.taller_id)
            .where(Asignacion.incidente_id == inc.id)
            .order_by(Asignacion.created_at.desc())
            .limit(1)
        )
        row = ar.first()
        asig_res = None
        if row:
            asig, taller_nombre, tlat, tlon = row[0], row[1], row[2], row[3]
            asig_res = AsignacionResumenCliente(
                id=asig.id,
                estado=asig.estado,
                eta=asig.eta,
                taller_nombre=taller_nombre,
                taller_latitud=tlat,
                taller_longitud=tlon,
            )
        out.append(
            MisSolicitudItem(
                incidente=IncidenteResponse.model_validate(inc),
                asignacion=asig_res,
                fotos_urls=by_fotos.get(inc.id, []),
                audios_urls=by_audios.get(inc.id, []),
            )
        )
    return out


async def actualizar_ubicacion(
    incidente_id: int, usuario_id: int, data: UbicacionUpdate, db: AsyncSession
) -> Incidente:
    incidente = await _incidente_de_usuario(incidente_id, usuario_id, db)
    incidente.latitud = data.latitud
    incidente.longitud = data.longitud
    await db.commit()
    await db.refresh(incidente)
    return incidente
