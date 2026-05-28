from beanie import Document
from pydantic import Field
from datetime import datetime

class InscripcionModel(Document):
    usuario_id: int
    evento_id: str
    evento_titulo: str # Guardamos el título para que la tarjeta se vea bonita sin hacer cruces raros
    fecha_inscripcion: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "inscripciones"