from fastapi import APIRouter

router = APIRouter()


# CU17 - Asignar técnico
@router.post("/{solicitud_id}/asignar-tecnico")
async def asignar_tecnico(solicitud_id: int):
    return {"msg": f"CU17 - asignar tecnico a solicitud {solicitud_id}"}


# CU18 - Actualizar estado del servicio
@router.patch("/{solicitud_id}/estado")
async def actualizar_estado(solicitud_id: int):
    return {"msg": f"CU18 - actualizar estado {solicitud_id}"}


# CU19 - Gestionar disponibilidad
@router.patch("/tecnicos/{tecnico_id}/disponibilidad")
async def gestionar_disponibilidad(tecnico_id: int):
    return {"msg": f"CU19 - disponibilidad tecnico {tecnico_id}"}


# CU27 - Registrar servicio realizado
@router.post("/{solicitud_id}/servicio-realizado")
async def registrar_servicio(solicitud_id: int):
    return {"msg": f"CU27 - servicio realizado {solicitud_id}"}


# CU30 - Gestionar técnicos
@router.get("/{taller_id}/tecnicos")
async def listar_tecnicos(taller_id: int):
    return {"msg": f"CU30 - tecnicos del taller {taller_id}"}
