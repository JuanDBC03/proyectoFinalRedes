from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum

# --- ENUMS ---

class EstadoEventoEnum(str, Enum):
    REGISTRADO = "registrado"
    EN_REVISION = "enRevision"
    APROVADO = "aprobado"
    RECHAZADO = "rechazado"
    CANCELADO = "cancelado"

class TipoEventoEnum(str, Enum):
    LUDICO = "ludico"
    ACADEMICO = "academico"

class TipoAvalEnum(str, Enum):
    DIRECTOR_PROGRAMA = "directorPrograma"
    DIRECTOR_DOCENCIA = "directorDocencia"

class OrganizacionParticipante(str, Enum):
    REPRESENTANTE_LEGAL = "representanteLegal"
    OTRO = "otro"

class UsuarioTipo(str, Enum):
    PRINCIPAL = "principal"
    SECUNDARIO = "secundario"

# Nuevo Enum para el estado de participación
class EstadoParticipacionEnum(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"

# --- SUBDOCUMENTOS ---

class Instalacion(BaseModel):
    instalacionId: str
    capacidadInstalacion: int

class Realizacion(BaseModel):
    instalaciones: List[Instalacion]
    fecha: datetime
    horaInicio: str
    horaFin: str

class Organizador(BaseModel):
    usuarioId: int
    avalPDF: bytes
    tipoAval: TipoAvalEnum
    tipo: UsuarioTipo
    model_config = ConfigDict(arbitrary_types_allowed=True)

class Organizacion(BaseModel):
    organizacionId: PydanticObjectId
    participante: OrganizacionParticipante
    nombreParticipante: str
    certificadoParticipacion: bytes
    model_config = ConfigDict(arbitrary_types_allowed=True)

# Nuevo subdocumento para manejar participantes
class Participante(BaseModel):
    usuarioId: int
    fechaRegistro: datetime = Field(default_factory=datetime.utcnow)
    estado: EstadoParticipacionEnum = EstadoParticipacionEnum.PENDIENTE

# --- DOCUMENTO PRINCIPAL ---

class EventoModel(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    nombre: str
    estado: EstadoEventoEnum
    tipo: TipoEventoEnum
    realizacion: Realizacion
    organizador: List[Organizador]
    organizacion: List[Organizacion] = Field(default_factory=list)
    capacidad: int # Capacidad física total
    
    # Nuevos campos de lógica de negocio
    creadoPor: int # ID del Docente (validaremos esto contra usuarios_service)
    cupoMaximo: int # Límite para registros
    participantes: List[Participante] = Field(default_factory=list)
    fechaCreacion: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "evento"

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        from_attributes=True
    )