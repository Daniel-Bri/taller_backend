from datetime import datetime

from pydantic import BaseModel


class NotificacionResponse(BaseModel):
    id: int
    user_id: int
    incidente_id: int | None = None
    tipo: str
    titulo: str
    mensaje: str
    leida: bool
    created_at: datetime

    model_config = {"from_attributes": True}
