from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.acceso_registro import schemas, service
from app.acceso_registro.schemas import UserResponse, VehiculoResponse, VehiculoUpdate, TallerResponse
from app.core.dependencies import get_current_user, require_role
from app.acceso_registro.models import User

router = APIRouter()


# ── CU01 - Registrarse ─────────────────────────────────────
@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
async def register(data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    token, user = await service.registrar_usuario(data, db)
    return schemas.Token(access_token=token, user=UserResponse.model_validate(user))


# ── CU02 - Iniciar sesión ──────────────────────────────────
@router.post("/login", response_model=schemas.Token)
async def login(data: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    token, user = await service.iniciar_sesion(data, db)
    return schemas.Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# ── CU03 - Registrar vehículo ──────────────────────────────
@router.post("/vehiculos", response_model=VehiculoResponse, status_code=status.HTTP_201_CREATED)
async def registrar_vehiculo(
    data: schemas.VehiculoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehiculo = await service.crear_vehiculo(data, current_user, db)
    return VehiculoResponse.model_validate(vehiculo)


# ── CU04 - Listar vehículos ────────────────────────────────
@router.get("/vehiculos", response_model=list[VehiculoResponse])
async def listar_vehiculos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehiculos = await service.listar_vehiculos_usuario(current_user.id, db)
    return [VehiculoResponse.model_validate(v) for v in vehiculos]


@router.patch("/vehiculos/{vehiculo_id}", response_model=VehiculoResponse)
async def actualizar_vehiculo(
    vehiculo_id: int,
    data: VehiculoUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    vehiculo = await service.actualizar_vehiculo(vehiculo_id, current_user.id, data, db)
    return VehiculoResponse.model_validate(vehiculo)


@router.delete("/vehiculos/{vehiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_vehiculo(
    vehiculo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.eliminar_vehiculo(vehiculo_id, current_user.id, db)


# ── CU12 - Registrar taller ────────────────────────────────
@router.post("/talleres", response_model=TallerResponse, status_code=status.HTTP_201_CREATED)
async def registrar_taller(
    data: schemas.TallerCreate,
    current_user: User = Depends(require_role("cliente")),
    db: AsyncSession = Depends(get_db),
):
    taller = await service.crear_taller(data, current_user, db)
    return TallerResponse.model_validate(taller)


# ── CU33 - Listar usuarios (admin) ────────────────────────
@router.get("/usuarios", response_model=list[UserResponse])
async def listar_usuarios(current_user: User = Depends(require_role("admin"))):
    return {"msg": "CU33 - listar usuarios"}


# ── CU34 - Aprobar / rechazar taller ──────────────────────
@router.get("/talleres", response_model=list[TallerResponse])
async def listar_talleres(
    estado: Optional[str] = None,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    talleres = await service.listar_talleres(estado, db)
    return [TallerResponse.model_validate(t) for t in talleres]


@router.patch("/talleres/{taller_id}/aprobar", response_model=TallerResponse)
async def aprobar_taller(
    taller_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    taller = await service.cambiar_estado_taller(taller_id, "aprobado", db)
    return TallerResponse.model_validate(taller)


@router.patch("/talleres/{taller_id}/rechazar", response_model=TallerResponse)
async def rechazar_taller(
    taller_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    taller = await service.cambiar_estado_taller(taller_id, "rechazado", db)
    return TallerResponse.model_validate(taller)
