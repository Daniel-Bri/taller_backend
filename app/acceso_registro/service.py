from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.acceso_registro.models import User, Vehiculo, Taller
from app.acceso_registro.schemas import UserCreate, UserLogin, VehiculoCreate, TallerCreate
from app.core.security import hash_password, verify_password, create_access_token


# ── Autenticación ──────────────────────────────────────────
async def registrar_usuario(data: UserCreate, db: AsyncSession) -> tuple[str, User]:
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El username ya está en uso")

    user = User(
        email=data.email.lower(),
        username=data.username,
        full_name=data.full_name,
        telefono=data.telefono,
        hashed_password=hash_password(data.password),
        role="cliente",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return token, user


async def iniciar_sesion(data: UserLogin, db: AsyncSession) -> tuple[str, User]:
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return token, user


# ── CU03 / CU04 - Vehículos ────────────────────────────────
async def crear_vehiculo(data: VehiculoCreate, user: User, db: AsyncSession) -> Vehiculo:
    result = await db.execute(select(Vehiculo).where(Vehiculo.placa == data.placa))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="La placa ya está registrada en el sistema")

    vehiculo = Vehiculo(
        usuario_id=user.id,
        placa=data.placa,
        marca=data.marca,
        modelo=data.modelo,
        anio=data.anio,
        color=data.color,
    )
    db.add(vehiculo)
    await db.commit()
    await db.refresh(vehiculo)
    return vehiculo


async def listar_vehiculos_usuario(usuario_id: int, db: AsyncSession) -> list[Vehiculo]:
    result = await db.execute(
        select(Vehiculo).where(Vehiculo.usuario_id == usuario_id, Vehiculo.activo == True)
    )
    return list(result.scalars().all())


async def eliminar_vehiculo(vehiculo_id: int, usuario_id: int, db: AsyncSession) -> None:
    result = await db.execute(
        select(Vehiculo).where(Vehiculo.id == vehiculo_id, Vehiculo.usuario_id == usuario_id)
    )
    vehiculo = result.scalar_one_or_none()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    vehiculo.activo = False
    await db.commit()


# ── CU12 - Taller ──────────────────────────────────────────
async def crear_taller(data: TallerCreate, user: User, db: AsyncSession) -> Taller:
    result = await db.execute(select(Taller).where(Taller.usuario_id == user.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya tienes un taller registrado")

    taller = Taller(
        usuario_id=user.id,
        nombre=data.nombre,
        direccion=data.direccion,
        telefono=data.telefono,
        email_comercial=data.email_comercial,
        latitud=data.latitud,
        longitud=data.longitud,
    )
    db.add(taller)
    user.role = "taller"
    await db.commit()
    await db.refresh(taller)
    return taller


async def listar_talleres(estado: str | None, db: AsyncSession) -> list[Taller]:
    query = select(Taller)
    if estado:
        query = query.where(Taller.estado == estado)
    result = await db.execute(query)
    return list(result.scalars().all())


async def cambiar_estado_taller(taller_id: int, nuevo_estado: str, db: AsyncSession) -> Taller:
    result = await db.execute(select(Taller).where(Taller.id == taller_id))
    taller = result.scalar_one_or_none()
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado")
    taller.estado = nuevo_estado
    await db.commit()
    await db.refresh(taller)
    return taller
