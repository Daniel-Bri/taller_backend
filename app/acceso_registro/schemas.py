from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
import re


class UserCreate(BaseModel):
    email: str
    username: str
    full_name: Optional[str] = None
    password: str

    @field_validator("email")
    @classmethod
    def email_valido(cls, v: str) -> str:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Correo electrónico inválido")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_seguro(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v

    @field_validator("username")
    @classmethod
    def username_valido(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("El username debe tener al menos 3 caracteres")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("El username solo puede contener letras, números y _")
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
