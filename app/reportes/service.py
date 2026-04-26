import json
import math
from datetime import datetime, timezone
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


# ── CU32 - Recordatorios de mantenimiento ─────────────────
async def obtener_recordatorios_mantenimiento(
    usuario_id: int, db: AsyncSession
) -> list[dict]:
    from app.acceso_registro.models import Vehiculo
    from app.talleres_tecnicos.models import ServicioRealizado, Asignacion
    from app.emergencias.models import Incidente

    vehiculos_result = await db.execute(
        select(Vehiculo).where(Vehiculo.usuario_id == usuario_id, Vehiculo.activo.is_(True))
    )
    vehiculos = list(vehiculos_result.scalars().all())

    recordatorios = []
    UMBRAL_GLOBAL = 90  # fallback cuando no hay historial suficiente

    CATEGORIAS: dict[str, list[str]] = {
        "batería":    ["batería", "bateria", "battery", "arranque", "carga eléctrica"],
        "frenos":     ["freno", "frenos", "pastilla", "disco", "frena"],
        "aceite":     ["aceite", "lubricante", "cambio de aceite"],
        "llantas":    ["llanta", "neumático", "neumatico", "goma", "ponchadura", "pinchazo"],
        "motor":      ["motor", "radiador", "sobrecalentamiento", "culata"],
        "suspensión": ["suspensión", "suspension", "amortiguador", "dirección", "direccion"],
        "eléctrico":  ["eléctrico", "electrico", "alternador", "fusible", "corto"],
    }

    for v in vehiculos:
        query = (
            select(ServicioRealizado)
            .join(Asignacion, ServicioRealizado.asignacion_id == Asignacion.id)
            .join(Incidente, Asignacion.incidente_id == Incidente.id)
            .where(Incidente.vehiculo_id == v.id)
            .order_by(ServicioRealizado.fecha_cierre.asc())
        )
        srv_result = await db.execute(query)
        servicios = list(srv_result.scalars().all())

        if not servicios:
            recordatorios.append({
                "vehiculo_id": v.id,
                "placa": v.placa,
                "marca": v.marca,
                "modelo": v.modelo,
                "anio": v.anio,
                "dias_desde_ultimo_servicio": None,
                "ultimo_servicio": None,
                "intervalo_recomendado": None,
                "problemas_recurrentes": [],
                "mensaje": f"El vehículo {v.marca} {v.modelo} ({v.placa}) no tiene historial de servicios en la plataforma.",
                "urgencia": "sin_historial",
            })
            continue

        fechas = []
        for s in servicios:
            f = s.fecha_cierre
            if f.tzinfo is None:
                f = f.replace(tzinfo=timezone.utc)
            fechas.append(f)

        intervalo_recomendado: int | None = None
        if len(fechas) >= 2:
            intervalos = [(fechas[i] - fechas[i - 1]).days for i in range(1, len(fechas))]
            promedio = sum(intervalos) / len(intervalos)
            intervalo_recomendado = max(30, int(promedio))

        umbral = intervalo_recomendado if intervalo_recomendado else UMBRAL_GLOBAL

        conteo: dict[str, int] = {}
        for s in servicios:
            texto = ((s.descripcion_trabajo or "") + " " + (s.observaciones or "")).lower()
            for categoria, palabras in CATEGORIAS.items():
                if any(p in texto for p in palabras):
                    conteo[categoria] = conteo.get(categoria, 0) + 1
        recurrentes = [cat for cat, cnt in conteo.items() if cnt >= 2]

        ahora = datetime.now(timezone.utc)
        dias = (ahora - fechas[-1]).days

        if dias >= int(umbral * 1.5):
            urgencia = "alta"
        elif dias >= umbral:
            urgencia = "media"
        elif dias >= int(umbral * 0.75):
            urgencia = "baja"
        else:
            continue

        if intervalo_recomendado:
            base = (
                f"Han pasado {dias} días desde el último servicio de {v.marca} {v.modelo} ({v.placa}). "
                f"Basado en tu historial, este vehículo se revisa cada ~{intervalo_recomendado} días."
            )
        else:
            base = (
                f"Han pasado {dias} días desde el último servicio de {v.marca} {v.modelo} ({v.placa}). "
                f"Se recomienda mantenimiento preventivo cada {UMBRAL_GLOBAL} días."
            )
        if recurrentes:
            base += f" Problemas frecuentes detectados: {', '.join(recurrentes)}."

        recordatorios.append({
            "vehiculo_id": v.id,
            "placa": v.placa,
            "marca": v.marca,
            "modelo": v.modelo,
            "anio": v.anio,
            "dias_desde_ultimo_servicio": dias,
            "ultimo_servicio": fechas[-1].isoformat(),
            "intervalo_recomendado": intervalo_recomendado,
            "problemas_recurrentes": recurrentes,
            "mensaje": base,
            "urgencia": urgencia,
        })

    return recordatorios


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
