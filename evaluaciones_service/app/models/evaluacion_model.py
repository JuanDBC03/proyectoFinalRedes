from beanie import Document, PydanticObjectId
from pydantic import Field, ConfigDict
from enum import Enum
from typing import Optional
from datetime import datetime

class EstadoEvaluacionEnum(str, Enum):
    REGISTRADO = "registrado"
    EN_REVISION = "enRevision"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"   
    CANCELADO = "cancelado"   

class EvaluacionModel(Document):
    id: Optional[PydanticObjectId] = Field(default_factory=PydanticObjectId, alias="_id")
    estado: EstadoEvaluacionEnum
    fechaEvaluacion: datetime
    justificacion: str = ""
    actaAprobacion: str = ""
    eventoId: PydanticObjectId
    usuarioId: int 

    class Settings:
        name = "evaluacion"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        from_attributes=True
    )