from fastapi import APIRouter

router = APIRouter()


# CU01 - Registrarse
@router.post("/register")
async def register():
    return {"msg": "CU01 - register"}


# CU02 - Iniciar sesión
@router.post("/login")
async def login():
    return {"msg": "CU02 - login"}


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
