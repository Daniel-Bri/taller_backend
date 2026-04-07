from fastapi import APIRouter

router = APIRouter()


# CU20 - Ver técnico en mapa
@router.get("/tecnicos/{tecnico_id}/ubicacion")
async def ubicacion_tecnico(tecnico_id: int):
    return {"msg": f"CU20 - ubicacion tecnico {tecnico_id}"}


# CU21 - Chatear en tiempo real
@router.post("/mensajes")
async def enviar_mensaje():
    return {"msg": "CU21 - enviar mensaje"}


@router.get("/mensajes/{solicitud_id}")
async def listar_mensajes(solicitud_id: int):
    return {"msg": f"CU21 - mensajes solicitud {solicitud_id}"}


# CU22 - Recibir notificaciones
@router.get("/notificaciones")
async def notificaciones():
    return {"msg": "CU22 - notificaciones"}
