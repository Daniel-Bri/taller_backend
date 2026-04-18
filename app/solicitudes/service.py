from math import radians, sin, cos, asin, sqrt
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists

from app.emergencias.models import Incidente, IncidenteFoto
from app.emergencias.service import public_foto_url
from app.talleres_tecnicos.models import Asignacion
from fastapi import HTTPException

from app.acceso_registro.models import Taller
from app.solicitudes.schemas import SolicitudDisponibleResponse

RADIO_ATENCION_KM = 150.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * r * asin(min(1.0, sqrt(h)))


def _tipo_problema_text(descripcion: str | None, prioridad: str) -> str:
    if descripcion and descripcion.strip():
        t = descripcion.strip()
        return t if len(t) <= 200 else t[:197] + "..."
    prioridad_labels = {"alta": "Emergencia alta", "media": "Falla parcial", "baja": "Revisión / baja prioridad"}
    return prioridad_labels.get(prioridad, prioridad)


async def listar_solicitudes_disponibles(
    taller: Taller, db: AsyncSession, radio_km: float = RADIO_ATENCION_KM
) -> list[SolicitudDisponibleResponse]:
    asig_exists = exists().where(Asignacion.incidente_id == Incidente.id)
    result = await db.execute(
        select(Incidente)
        .where(
            Incidente.estado == "pendiente",
            Incidente.latitud.isnot(None),
            Incidente.longitud.isnot(None),
            ~asig_exists,
        )
        .order_by(Incidente.created_at.desc())
    )
    incidentes = list(result.scalars().all())

    if taller.latitud is not None and taller.longitud is not None:
        incidentes = [
            i
            for i in incidentes
            if _haversine_km(taller.latitud, taller.longitud, i.latitud, i.longitud) <= radio_km
        ]
        incidentes.sort(
            key=lambda i: _haversine_km(taller.latitud, taller.longitud, i.latitud, i.longitud)
        )
    else:
        incidentes.sort(key=lambda i: i.created_at.timestamp(), reverse=True)

    if not incidentes:
        return []

    ids = [i.id for i in incidentes]
    fr = await db.execute(select(IncidenteFoto).where(IncidenteFoto.incidente_id.in_(ids)))
    fotos_rows = list(fr.scalars().all())
    by_inc: dict[int, list[str]] = defaultdict(list)
    for f in fotos_rows:
        by_inc[f.incidente_id].append(public_foto_url(f.url_path))

    out: list[SolicitudDisponibleResponse] = []
    for inc in incidentes:
        out.append(
            SolicitudDisponibleResponse(
                incidente_id=inc.id,
                latitud=inc.latitud,
                longitud=inc.longitud,
                descripcion=inc.descripcion,
                tipo_problema=_tipo_problema_text(inc.descripcion, inc.prioridad or "media"),
                prioridad=inc.prioridad or "media",
                estado=inc.estado,
                fotos_urls=by_inc.get(inc.id, []),
                tiene_audio=False,
                created_at=inc.created_at,
            )
        )
    return out


async def aceptar_solicitud(
    incidente_id: int,
    taller: Taller,
    db: AsyncSession,
    eta: int | None = None,
):
    """CU15: crea asignación del taller al incidente y marca el incidente en proceso."""
    result = await db.execute(select(Incidente).where(Incidente.id == incidente_id))
    incidente = result.scalar_one_or_none()
    if not incidente:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if incidente.estado != "pendiente":
        raise HTTPException(status_code=400, detail="La solicitud ya no está disponible")
    if incidente.latitud is None or incidente.longitud is None:
        raise HTTPException(status_code=400, detail="La solicitud no tiene ubicación registrada")

    r_asig = await db.execute(
        select(Asignacion).where(Asignacion.incidente_id == incidente_id)
    )
    if r_asig.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Esta solicitud ya fue asignada a un taller")

    if taller.latitud is not None and taller.longitud is not None:
        dist = _haversine_km(
            taller.latitud, taller.longitud, incidente.latitud, incidente.longitud
        )
        if dist > RADIO_ATENCION_KM:
            raise HTTPException(
                status_code=403,
                detail="La solicitud está fuera del radio de atención de tu taller",
            )

    asig = Asignacion(
        incidente_id=incidente_id,
        taller_id=taller.id,
        tecnico_id=None,
        estado="aceptado",
        eta=eta,
    )
    db.add(asig)
    incidente.estado = "en_proceso"
    await db.commit()
    await db.refresh(asig)
    return asig
