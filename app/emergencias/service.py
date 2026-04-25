from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.emergencias.models import Incidente
from app.emergencias.schemas import IncidenteCreate, UbicacionUpdate
from app.acceso_registro.models import Taller, Vehiculo
from app.talleres_tecnicos.models import Asignacion


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


async def listar_mis_solicitudes(usuario_id: int, db: AsyncSession) -> list[dict]:
    inc_result = await db.execute(
        select(Incidente)
        .where(Incidente.usuario_id == usuario_id)
        .order_by(Incidente.created_at.desc())
    )
    incidentes = list(inc_result.scalars().all())

    rows = []
    for inc in incidentes:
        asig_result = await db.execute(
            select(Asignacion).where(Asignacion.incidente_id == inc.id)
        )
        asig = asig_result.scalar_one_or_none()

        asig_data = None
        if asig:
            taller_result = await db.execute(
                select(Taller).where(Taller.id == asig.taller_id)
            )
            taller = taller_result.scalar_one_or_none()
            asig_data = {
                "id": asig.id,
                "estado": asig.estado,
                "eta": asig.eta,
                "taller_id": asig.taller_id,
                "taller_nombre": taller.nombre if taller else None,
                "tecnico_id": asig.tecnico_id,
                "observacion": asig.observacion,
            }

        rows.append({
            "incidente": {
                "id": inc.id,
                "vehiculo_id": inc.vehiculo_id,
                "estado": inc.estado,
                "prioridad": inc.prioridad,
                "descripcion": inc.descripcion,
                "latitud": inc.latitud,
                "longitud": inc.longitud,
                "created_at": inc.created_at.isoformat() if inc.created_at else None,
            },
            "asignacion": asig_data,
            "fotos_urls": [],
        })
    return rows


async def crear_incidente_sos(
    usuario_id: int,
    latitud: float | None,
    longitud: float | None,
    db: AsyncSession,
) -> Incidente:
    vehiculo_result = await db.execute(
        select(Vehiculo)
        .where(Vehiculo.usuario_id == usuario_id, Vehiculo.activo == True)
        .order_by(Vehiculo.created_at.asc())
    )
    vehiculo = vehiculo_result.scalars().first()
    if not vehiculo:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Debes tener al menos un vehículo registrado para usar el botón SOS",
        )

    incidente = Incidente(
        usuario_id=usuario_id,
        vehiculo_id=vehiculo.id,
        descripcion="🆘 Alerta SOS — Emergencia urgente enviada desde la app",
        prioridad="alta",
        latitud=latitud,
        longitud=longitud,
    )
    db.add(incidente)
    await db.commit()
    await db.refresh(incidente)
    return incidente


async def actualizar_ubicacion(
    incidente_id: int, usuario_id: int, data: UbicacionUpdate, db: AsyncSession
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
    incidente.latitud = data.latitud
    incidente.longitud = data.longitud
    await db.commit()
    await db.refresh(incidente)
    return incidente
