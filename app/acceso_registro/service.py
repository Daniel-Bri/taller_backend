from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.acceso_registro.models import User
from app.acceso_registro.schemas import UserCreate, UserLogin
from app.core.security import hash_password, verify_password, create_access_token


async def registrar_usuario(data: UserCreate, db: AsyncSession) -> tuple[str, User]:
    # Verificar email único
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # Verificar username único
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El username ya está en uso")

    user = User(
        email=data.email.lower(),
        username=data.username,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return token, user
