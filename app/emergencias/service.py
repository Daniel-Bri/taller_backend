import uuid
from pathlib import Path
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, UploadFile

from app.emergencias.models import Incidente, IncidenteFoto
from app.emergencias.schemas import (
    IncidenteCreate,
    UbicacionUpdate,
    DescripcionUpdate,
    IncidenteResponse,
    MisSolicitudItem,
    AsignacionResumenCliente,
)
from app.acceso_registro.models import Vehiculo, Taller
from app.talleres_tecnicos.models import Asignacion

_UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads"

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def get_upload_root() -> Path:
    _UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return _UPLOAD_ROOT


def public_foto_url(stored_path: str) -> str:
    p = stored_path.strip().lstrip("/")
    return f"/uploads/{p}"


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
    return row


async def listar_mis_solicitudes_cliente(
    usuario_id: int, db: AsyncSession
) -> list[MisSolicitudItem]:
    incidentes = await listar_incidentes_usuario(usuario_id, db)
    if not incidentes:
        return []
    ids = [i.id for i in incidentes]
    fr = await db.execute(select(IncidenteFoto).where(IncidenteFoto.incidente_id.in_(ids)))
    fotos_list = list(fr.scalars().all())
    by_fotos: dict[int, list[str]] = defaultdict(list)
    for f in fotos_list:
        by_fotos[f.incidente_id].append(public_foto_url(f.url_path))

    out: list[MisSolicitudItem] = []
    for inc in incidentes:
        ar = await db.execute(
            select(Asignacion, Taller.nombre)
            .join(Taller, Taller.id == Asignacion.taller_id)
            .where(Asignacion.incidente_id == inc.id)
            .order_by(Asignacion.created_at.desc())
            .limit(1)
        )
        row = ar.first()
        asig_res = None
        if row:
            asig, taller_nombre = row[0], row[1]
            asig_res = AsignacionResumenCliente(
                id=asig.id,
                estado=asig.estado,
                eta=asig.eta,
                taller_nombre=taller_nombre,
            )
        out.append(
            MisSolicitudItem(
                incidente=IncidenteResponse.model_validate(inc),
                asignacion=asig_res,
                fotos_urls=by_fotos.get(inc.id, []),
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
