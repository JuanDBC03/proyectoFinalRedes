from beanie import Document
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from typing import Optional

class TipoInstalacionEnum(str, Enum):
    SALON = "salon"
    AUDITORIO = "auditorio"
    LABORATORIO = "laboratorio"
    CANCHA = "cancha"

# --- MODELOS "ESCUDO" (¡Estos se quedan, nos salvaron del 422!) ---
class InstalacionCreate(BaseModel):
    ubicacion: str
    tipo: TipoInstalacionEnum
    capacidad: int

class InstalacionUpdate(BaseModel):
    ubicacion: Optional[str] = None
    tipo: Optional[TipoInstalacionEnum] = None
    capacidad: Optional[int] = None

# --- MODELO DE BASE DE DATOS BEANIE (Corregido) ---
class InstalacionModel(Document):
    # ¡Regresamos tu ID personalizado para que no explote con "SALON-101"!
    id: Optional[str] = Field(alias="_id", default=None) 
    ubicacion: str
    tipo: TipoInstalacionEnum
    capacidad: int

    class Settings:
        name = "instalacion"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        populate_by_name=True
    )