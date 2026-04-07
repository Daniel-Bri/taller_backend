from fastapi import APIRouter

router = APIRouter()


# CU28 - Calificar servicio
@router.post("/{solicitud_id}/calificacion")
async def calificar_servicio(solicitud_id: int):
    return {"msg": f"CU28 - calificar servicio {solicitud_id}"}


# CU29 - Ver historial de servicios
@router.get("/historial")
async def historial():
    return {"msg": "CU29 - historial de servicios"}


# CU31 - Ver métricas del taller
@router.get("/metricas/taller")
async def metricas_taller():
    return {"msg": "CU31 - metricas del taller"}


# CU35 - Ver métricas globales
@router.get("/metricas/globales")
async def metricas_globales():
    return {"msg": "CU35 - metricas globales"}


# CU36 - Ver auditoría del sistema
@router.get("/auditoria")
async def auditoria():
    return {"msg": "CU36 - auditoria del sistema"}
