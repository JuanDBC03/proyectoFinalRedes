from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class Ubicacion(BaseModel): 
    direccion: str
    ciudad: str

class OrganizacionModel(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    nombre: str
    representanteLegal: str
    ubicacion: Ubicacion
    sectorEconomico: str
    actividadPrincipal: str
    telefonos: List[str]

    class Settings:
        name = "organizacion"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        from_attributes=True
    )