from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class UnidadAcademica(BaseModel):
    unidadId: PydanticObjectId = Field(default_factory=PydanticObjectId)
    nombre: str

class Programa(BaseModel):
    programaId: PydanticObjectId = Field(default_factory=PydanticObjectId)
    nombre: str

class FacultadModel(Document):
    nombre: str
    unidadAcademica: List[UnidadAcademica] = []
    programa: List[Programa] = []

    class Settings:
        name = "facultad"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True
    )