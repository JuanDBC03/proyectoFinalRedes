from beanie import Document
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime

class EstadoPasswordEnum(str, Enum):
    ACTIVA = "activa"
    INACTIVA = "inactiva"

class Password(BaseModel):
    clave: str
    fechaCambio: datetime
    estado: EstadoPasswordEnum

# El modelo en Auth Service queda súper ligero y enfocado solo en credenciales
class UsuarioModel(Document):
    id: int = Field(alias="_id")  # El ID numérico (cédula) será la clave primaria de Mongo
    email: EmailStr
    password: List[Password]

    class Settings:
        name = "usuario"  # Colección 'usuario' dentro de db_auth

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        from_attributes=True
    )