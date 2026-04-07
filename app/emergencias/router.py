from fastapi import APIRouter

router = APIRouter()


# CU05 - Reportar emergencia
@router.post("/")
async def reportar_emergencia():
    return {"msg": "CU05 - reportar emergencia"}


# CU06 - Enviar ubicación GPS
@router.patch("/{emergencia_id}/ubicacion")
async def enviar_ubicacion(emergencia_id: int):
    return {"msg": f"CU06 - ubicacion emergencia {emergencia_id}"}


# CU07 - Adjuntar fotos
@router.post("/{emergencia_id}/fotos")
async def adjuntar_fotos(emergencia_id: int):
    return {"msg": f"CU07 - fotos emergencia {emergencia_id}"}


# CU08 - Enviar audio
@router.post("/{emergencia_id}/audio")
async def enviar_audio(emergencia_id: int):
    return {"msg": f"CU08 - audio emergencia {emergencia_id}"}


# CU09 - Agregar descripción texto
@router.patch("/{emergencia_id}/descripcion")
async def agregar_descripcion(emergencia_id: int):
    return {"msg": f"CU09 - descripcion emergencia {emergencia_id}"}
