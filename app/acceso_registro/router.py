from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.acceso_registro import schemas, service
from app.acceso_registro.schemas import UserResponse
from app.core.dependencies import get_current_user
from app.acceso_registro.models import User

router = APIRouter()


# CU01 - Registrarse
@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
async def register(data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    token, user = await service.registrar_usuario(data, db)
    return schemas.Token(access_token=token, user=UserResponse.model_validate(user))


# CU02 - Iniciar sesión
@router.post("/login", response_model=schemas.Token)
async def login(data: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    token, user = await service.iniciar_sesion(data, db)
    return schemas.Token(access_token=token, user=UserResponse.model_validate(user))


# Perfil del usuario autenticado (útil para ambos clientes al iniciar)
@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# CU03 - Registrar vehículo
@router.post("/vehiculos")
async def registrar_vehiculo():
    return {"msg": "CU03 - registrar vehiculo"}


# CU04 - Gestionar vehículos
@router.get("/vehiculos")
async def listar_vehiculos():
    return {"msg": "CU04 - listar vehiculos"}


# CU12 - Registrar taller
@router.post("/talleres")
async def registrar_taller():
    return {"msg": "CU12 - registrar taller"}


# CU33 - Gestionar usuarios
@router.get("/usuarios")
async def listar_usuarios():
    return {"msg": "CU33 - listar usuarios"}


# CU34 - Aprobar talleres
@router.patch("/talleres/{taller_id}/aprobar")
async def aprobar_taller(taller_id: int):
    return {"msg": f"CU34 - aprobar taller {taller_id}"}
