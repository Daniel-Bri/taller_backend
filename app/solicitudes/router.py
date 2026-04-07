from fastapi import APIRouter

router = APIRouter()


# CU10 - Ver estado de solicitud
@router.get("/{solicitud_id}/estado")
async def ver_estado(solicitud_id: int):
    return {"msg": f"CU10 - estado solicitud {solicitud_id}"}


# CU11 - Cancelar solicitud
@router.patch("/{solicitud_id}/cancelar")
async def cancelar(solicitud_id: int):
    return {"msg": f"CU11 - cancelar solicitud {solicitud_id}"}


# CU13 - Ver solicitudes disponibles
@router.get("/disponibles")
async def disponibles():
    return {"msg": "CU13 - solicitudes disponibles"}


# CU14 - Ver detalle del incidente
@router.get("/{solicitud_id}")
async def detalle(solicitud_id: int):
    return {"msg": f"CU14 - detalle solicitud {solicitud_id}"}


# CU15 - Aceptar solicitud
@router.patch("/{solicitud_id}/aceptar")
async def aceptar(solicitud_id: int):
    return {"msg": f"CU15 - aceptar solicitud {solicitud_id}"}


# CU16 - Rechazar solicitud
@router.patch("/{solicitud_id}/rechazar")
async def rechazar(solicitud_id: int):
    return {"msg": f"CU16 - rechazar solicitud {solicitud_id}"}
