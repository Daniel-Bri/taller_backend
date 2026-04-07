from fastapi import APIRouter

router = APIRouter()


# CU23 - Generar cotización
@router.post("/cotizaciones")
async def generar_cotizacion():
    return {"msg": "CU23 - generar cotizacion"}


# CU24 - Ver cotización
@router.get("/cotizaciones/{cotizacion_id}")
async def ver_cotizacion(cotizacion_id: int):
    return {"msg": f"CU24 - ver cotizacion {cotizacion_id}"}


# CU25 - Confirmar cotización
@router.patch("/cotizaciones/{cotizacion_id}/confirmar")
async def confirmar_cotizacion(cotizacion_id: int):
    return {"msg": f"CU25 - confirmar cotizacion {cotizacion_id}"}


# CU26 - Realizar pago
@router.post("/pagos")
async def realizar_pago():
    return {"msg": "CU26 - realizar pago"}


# CU32 - Ver comisiones
@router.get("/comisiones")
async def ver_comisiones():
    return {"msg": "CU32 - ver comisiones"}
