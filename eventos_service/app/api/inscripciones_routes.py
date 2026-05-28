from fastapi import APIRouter, HTTPException, Depends, status
from app.models.inscripcion_model import InscripcionModel
from app.core.security import obtener_usuario_actual
from pydantic import BaseModel
from app.models.evento_model import EventoModel, Participante, EstadoParticipacionEnum

router = APIRouter(tags=["Inscripciones"])

# Modelo para recibir los datos desde el frontend
class InscripcionPayload(BaseModel):
    evento_id: str
    evento_titulo: str

# 1. RUTA PARA INSCRIBIRSE (La que usa el botón verde)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def inscribirse_evento(
    payload: InscripcionPayload, 
    usuario_actual_id: int = Depends(obtener_usuario_actual)
):
    # 1. Buscamos primero el evento para asegurarnos de que existe
    evento = await EventoModel.get(payload.evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="El evento no existe.")

    # 2. Verificamos si el estudiante ya se había inscrito antes en InscripcionModel
    existente = await InscripcionModel.find_one(
        InscripcionModel.usuario_id == usuario_actual_id,
        InscripcionModel.evento_id == payload.evento_id
    )
    if existente:
        raise HTTPException(status_code=400, detail="Ya estás inscrito en este evento.")
    
    # 3. Guardamos la inscripción independiente
    nueva_inscripcion = InscripcionModel(
        usuario_id=usuario_actual_id, 
        evento_id=payload.evento_id,
        evento_titulo=payload.evento_titulo
    )
    await nueva_inscripcion.insert()

    # 🌟 👇 LAS LÍNEAS MÁGICAS 👇 🌟
    # 4. Agregamos al estudiante al array interno del evento
    nuevo_participante = Participante(
        usuarioId=usuario_actual_id, 
        estado=EstadoParticipacionEnum.PENDIENTE # O el estado por defecto que uses
    )
    evento.participantes.append(nuevo_participante)
    await evento.save() # Guardamos los cambios en el Evento
    # 🌟 👆 FIN LÍNEAS MÁGICAS 👆 🌟

    return {"message": "¡Inscripción exitosa y cupo reservado en el evento!"}


# 2. RUTA PARA CONSULTAR MIS INSCRIPCIONES (La que usa la pestaña lateral)
@router.get("/mis-inscripciones")
async def obtener_mis_inscripciones(usuario_actual_id: int = Depends(obtener_usuario_actual)):
    # Buscamos solo las inscripciones de este estudiante
    inscripciones = await InscripcionModel.find(InscripcionModel.usuario_id == usuario_actual_id).to_list()
    return inscripciones


@router.delete("/{inscripcion_id}", status_code=status.HTTP_200_OK)
async def cancelar_inscripcion(
    inscripcion_id: str, 
    # usuario_autenticado = Depends(obtener_usuario_actual) # Descomenta si validas token en el back
):
    try:
        # 1. Buscamos la inscripción en la base de datos
        inscripcion = await InscripcionModel.get(inscripcion_id)
        
        if not inscripcion:
            raise HTTPException(
                status_code=404, 
                detail="La inscripción no existe o ya fue cancelada."
            )

        # 2. Obtenemos los datos clave antes de borrarla
        evento_id = inscripcion.evento_id
        usuario_id = getattr(inscripcion, "usuario_id", None) 

        # 3. Buscamos el evento para remover al participante de su lista anidada
        if evento_id:
            evento = await EventoModel.get(evento_id)
            if evento and evento.participantes:
                # Filtramos la lista para dejar por fuera al estudiante que cancela
                evento.participantes = [
                    p for p in evento.participantes if p.usuarioId != usuario_id
                ]
                # Guardamos el evento actualizado con el cupo liberado
                await evento.save()

        # 4. Finalmente, eliminamos la inscripción de la base de datos
        await inscripcion.delete()

        return {"message": "Inscripción cancelada exitosamente y cupo liberado."}

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al cancelar la inscripción: {str(e)}"
        )