from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine
from app.db.base import Base

# Importar modelos para que SQLAlchemy los registre antes de create_all
import app.acceso_registro.models  # noqa: F401  (User, Vehiculo, Taller)

from app.acceso_registro.router import router as acceso_router
from app.talleres_tecnicos.router import router as talleres_router
from app.emergencias.router import router as emergencias_router
from app.solicitudes.router import router as solicitudes_router
from app.cotizacion_pagos.router import router as pagos_router
from app.comunicacion.router import router as comunicacion_router
from app.reportes.router import router as reportes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas al iniciar (dev). En producción usar Alembic.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Taller Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(acceso_router,       prefix="/api/acceso",       tags=["Acceso y Registro"])
app.include_router(talleres_router,     prefix="/api/talleres",     tags=["Talleres y Técnicos"])
app.include_router(emergencias_router,  prefix="/api/emergencias",  tags=["Emergencias"])
app.include_router(solicitudes_router,  prefix="/api/solicitudes",  tags=["Solicitudes"])
app.include_router(pagos_router,        prefix="/api/pagos",        tags=["Cotización y Pagos"])
app.include_router(comunicacion_router, prefix="/api/comunicacion", tags=["Comunicación"])
app.include_router(reportes_router,     prefix="/api/reportes",     tags=["Reportes"])


@app.get("/")
async def root():
    return {"message": "Taller Backend corriendo"}
