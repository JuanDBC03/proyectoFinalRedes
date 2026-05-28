from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime

class EstadoPasswordEnum(str, Enum):
    ACTIVA = "activa"
    INACTIVA = "inactiva"

class RolUsuarioEnum(str, Enum):
    ESTUDIANTE = "estudiante"
    DOCENTE = "docente"
    SECRETARIA = "secretariaAcademica"

class EstadoVinculacionEnum(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"

class Password(BaseModel):
    clave: str
    fechaCambio: datetime
    estado: EstadoPasswordEnum

class Vinculacion(BaseModel):
    rol: RolUsuarioEnum
    programaId: Optional[PydanticObjectId] = None
    unidadId: Optional[PydanticObjectId] = None
    facultadId: Optional[PydanticObjectId] = None
    fecha: Optional[datetime] = None
    estado: Optional[EstadoVinculacionEnum] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

class UsuarioModel(Document):
    id: Optional[int] = Field(alias="_id")
    nombre: str
    apellidos: str
    email: EmailStr
    telefonos: List[str]
    password: List[Password]
    vinculacion: List[Vinculacion]

    class Settings:
        name = "usuario"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        from_attributes=True
    )