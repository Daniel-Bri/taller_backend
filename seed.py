"""
Carga datos iniciales en la base de datos.
Uso: python seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from dotenv import load_dotenv
import os

load_dotenv()

from app.acceso_registro.models import User
from app.db.base import Base
from app.core.security import hash_password

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

USUARIOS_INICIALES = [
    {
        "email": "admin@taller.com",
        "username": "admin",
        "full_name": "Administrador",
        "password": "12345678",
        "is_admin": True,
    },
    {
        "email": "cliente@taller.com",
        "username": "cliente",
        "full_name": "Cliente Demo",
        "password": "12345678",
        "is_admin": False,
    },
    {
        "email": "taller@taller.com",
        "username": "taller",
        "full_name": "Taller Demo",
        "password": "12345678",
        "is_admin": False,
    },
]


async def seed():
    # Crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        for data in USUARIOS_INICIALES:
            result = await db.execute(select(User).where(User.email == data["email"]))
            if result.scalar_one_or_none():
                print(f"  [skip] {data['email']} ya existe")
                continue

            user = User(
                email=data["email"],
                username=data["username"],
                full_name=data["full_name"],
                hashed_password=hash_password(data["password"]),
                is_admin=data["is_admin"],
            )
            db.add(user)
            print(f"  [ok]   {data['email']} creado")

        await db.commit()

    print("\nUsuarios disponibles:")
    print("  admin@taller.com   / 12345678  (admin)")
    print("  cliente@taller.com / 12345678")
    print("  taller@taller.com  / 12345678")


if __name__ == "__main__":
    asyncio.run(seed())
