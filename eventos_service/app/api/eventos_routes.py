from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import httpx
from typing import Dict, Any, List
from app.models.evento_model import EventoModel, Participante, EstadoParticipacionEnum
from app.core.security import obtener_usuario_actual

router = APIRouter(tags=["Eventos"])

USUARIOS_SERVICE_URL = "http://usuarios_service:8002/api/v1/usuarios"
INSTALACIONES_SERVICE_URL = "http://instalaciones_service:8005/api/v1/instalaciones"
NOTIFICACIONES_SERVICE_URL = "http://notificaciones_service:8006/api/v1/notificaciones"

class ActualizarEstadoModel(BaseModel):
    estado: str
    justificacion: str = "Sin detalles adicionales."

async def obtener_rol_usuario(usuario_id: int) -> str:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{USUARIOS_SERVICE_URL}/{usuario_id}/rol")
            if resp.status_code == 200:
                return resp.json().get("rol")
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de Usuarios no disponible")
    return None

async def validar_reglas_evento(evento: EventoModel, evento_id_ignorar: str = None):
    fecha_evento = evento.realizacion.fecha
    if fecha_evento.tzinfo is None:
        fecha_evento = fecha_evento.replace(tzinfo=timezone.utc)
    
    fecha_minima = datetime.now(timezone.utc) + timedelta(days=1)
    
    if fecha_evento < fecha_minima:
        raise HTTPException(status_code=400, detail="La fecha del evento debe ser al menos un día posterior a hoy.")

    async with httpx.AsyncClient() as client:
        for inst in evento.realizacion.instalaciones:
            try:
                resp = await client.get(f"{INSTALACIONES_SERVICE_URL}/{inst.instalacionId}")
                if resp.status_code == 200:
                    datos_inst = resp.json()
                    capacidad = datos_inst.get("capacidad", 0)
                    if evento.cupoMaximo > capacidad:
                        raise HTTPException(status_code=400, detail=f"Los cupos ({evento.cupoMaximo}) superan la capacidad de la instalación seleccionada ({capacidad}).")
            except httpx.RequestError:
                raise HTTPException(status_code=503, detail="Servicio de Instalaciones no disponible para validar cupos.")

    inicio_dia = evento.realizacion.fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia = inicio_dia + timedelta(days=1)
    
    eventos_mismo_dia = await EventoModel.find(
        EventoModel.realizacion.fecha >= inicio_dia,
        EventoModel.realizacion.fecha < fin_dia
    ).to_list()

    for e_existente in eventos_mismo_dia:
        if evento_id_ignorar and str(e_existente.id) == str(evento_id_ignorar):
            continue
            
        inst_existentes = [i.instalacionId for i in e_existente.realizacion.instalaciones]
        inst_nuevas = [i.instalacionId for i in evento.realizacion.instalaciones]
        
        cruce_lugar = any(inst in inst_existentes for inst in inst_nuevas)
        
        if cruce_lugar:
            if (e_existente.realizacion.horaInicio < evento.realizacion.horaFin) and \
               (e_existente.realizacion.horaFin > evento.realizacion.horaInicio):
                raise HTTPException(status_code=400, detail="La instalación seleccionada ya se encuentra ocupada en esa fecha y horario.")

# --- RUTAS ---
@router.get("/")
async def obtener_eventos():
    return await EventoModel.find_all().to_list()

@router.get("/instalaciones/disponibles")
async def obtener_instalaciones_disponibles(fecha: str, hora_inicio: str, hora_fin: str, cupo_requerido: int):
    try:
        fecha_obj = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa formato ISO.")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{INSTALACIONES_SERVICE_URL}/")
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Error consultando instalaciones")
            todas_instalaciones = resp.json()
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de Instalaciones no disponible")

    con_capacidad = [inst for inst in todas_instalaciones if inst.get("capacidad", 0) >= cupo_requerido]

    inicio_dia_obj = fecha_obj.replace(hour=0, minute=0, second=0, microsecond=0)
    fin_dia_obj = inicio_dia_obj + timedelta(days=1)

    eventos_dia = await EventoModel.find(
        EventoModel.realizacion.fecha >= inicio_dia_obj,
        EventoModel.realizacion.fecha < fin_dia_obj
    ).to_list()
    
    instalaciones_ocupadas = set()
    for e in eventos_dia:
        if (e.realizacion.horaInicio < hora_fin) and (e.realizacion.horaFin > hora_inicio):
            for inst in e.realizacion.instalaciones:
                instalaciones_ocupadas.add(inst.instalacionId)

    disponibles = [
        inst for inst in con_capacidad 
        if inst.get("_id", inst.get("id")) not in instalaciones_ocupadas
    ]
    return disponibles

@router.get("/{evento_id}")
async def buscar_evento_por_id(evento_id: str):
    evento = await EventoModel.get(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento

@router.post("/{evento_id}/registrar")
async def registrar_estudiante(evento_id: str, usuario_actual_id: int = Depends(obtener_usuario_actual)):
    evento = await EventoModel.get(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    rol = await obtener_rol_usuario(usuario_actual_id)
    if rol == "secretariaAcademica":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La Secretaria Académica no puede participar en eventos.")

    if evento.realizacion.fecha.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="No puedes registrarte en un evento finalizado")

    participantes_activos = [p for p in evento.participantes if p.estado != EstadoParticipacionEnum.CANCELADO]

    if len(participantes_activos) >= evento.cupoMaximo:
        raise HTTPException(status_code=400, detail="Evento sin cupos disponibles")

    for p in participantes_activos:
        if p.usuarioId == usuario_actual_id:
            raise HTTPException(status_code=400, detail="Ya estás registrado en este evento")

    nuevo_participante = Participante(usuarioId=usuario_actual_id, estado=EstadoParticipacionEnum.PENDIENTE)
    evento.participantes.append(nuevo_participante)
    await evento.save()
    return {"message": "Registro exitoso"}

@router.post("/")
async def crear_evento(evento: EventoModel, usuario_actual_id: int = Depends(obtener_usuario_actual)):
    rol = await obtener_rol_usuario(usuario_actual_id)
    if rol != "docente":
        raise HTTPException(status_code=403, detail="Solo los docentes pueden crear eventos")
    
    await validar_reglas_evento(evento)
    evento.creadoPor = usuario_actual_id
    await evento.insert()

    async with httpx.AsyncClient() as client:
        try:
            payload_email = {
                "destinatario": "secretaria@universidad.edu.co",
                "asunto": f"Nuevo evento pendiente de aprobación: {evento.nombre}",
                "cuerpo": f"El docente (ID: {usuario_actual_id}) ha registrado el evento '{evento.nombre}' para la fecha {evento.realizacion.fecha.strftime('%Y-%m-%d')}. Por favor, ingrese al sistema para evaluar la solicitud."
            }
            await client.post(f"{NOTIFICACIONES_SERVICE_URL}/enviar", json=payload_email)
        except httpx.RequestError as e:
            print(f"⚠️ Alerta: No se pudo conectar con notificaciones_service: {e}")
    return evento

@router.put("/{evento_id}")
async def editar_evento(evento_id: str, datos_actualizados: Dict[str, Any], usuario_actual_id: int = Depends(obtener_usuario_actual)):
    evento = await EventoModel.get(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    rol = await obtener_rol_usuario(usuario_actual_id)
    if evento.creadoPor != usuario_actual_id and rol != "secretariaAcademica":
        raise HTTPException(status_code=403, detail="No tienes permisos para editar este evento")
    
    try:
        evento_dict = evento.model_dump() if hasattr(evento, 'model_dump') else evento.dict()
        evento_dict.update(datos_actualizados)
        evento_borrador = EventoModel(**evento_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Datos de actualización inválidos: {str(e)}")
    
    await validar_reglas_evento(evento_borrador, evento_id_ignorar=evento_id)
    await evento.update({"$set": datos_actualizados})
    return await EventoModel.get(evento_id)

@router.patch("/{evento_id}/estado")
async def cambiar_estado_evento(evento_id: str, payload: ActualizarEstadoModel, usuario_actual_id: int = Depends(obtener_usuario_actual)):
    rol = await obtener_rol_usuario(usuario_actual_id)
    if rol != "secretariaAcademica":
        raise HTTPException(status_code=403, detail="Solo la Secretaria Académica puede aprobar o cambiar el estado.")
    
    evento = await EventoModel.get(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    estados_validos = ["registrado", "aprobado", "rechazado", "cancelado"]
    estado_limpio = payload.estado.lower()
    
    if estado_limpio not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Usa uno de: {estados_validos}")

    evento.estado = estado_limpio
    await evento.save()

    async with httpx.AsyncClient() as client:
        try:
            cuerpo_correo = (
                f"Hola. Se le notifica que la Secretaria Académica ha evaluado su evento '{evento.nombre}' "
                f"y su estado ahora es: <strong>{estado_limpio.upper()}</strong>.<br><br>"
                f"<strong>Motivo / Justificación:</strong> {payload.justificacion}"
            )
            payload_resolucion = {
                "destinatario": f"docente_{evento.creadoPor}@universidad.edu.co",
                "asunto": f"Resolución de evento: {evento.nombre} - {estado_limpio.upper()}",
                "cuerpo": cuerpo_correo
            }
            await client.post(f"{NOTIFICACIONES_SERVICE_URL}/enviar", json=payload_resolucion)
        except httpx.RequestError as e:
            print(f"⚠️ Alerta: No se pudo enviar notificación de cambio de estado: {e}")
    return {"message": f"Estado actualizado a {estado_limpio}", "evento": evento}

@router.delete("/{evento_id}")
async def eliminar_evento(evento_id: str, usuario_actual_id: int = Depends(obtener_usuario_actual)):
    evento = await EventoModel.get(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    rol = await obtener_rol_usuario(usuario_actual_id)
    if evento.creadoPor != usuario_actual_id and rol != "secretariaAcademica":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos. Solo el docente creador o la Secretaria Académica pueden eliminarlo.")
    
    await evento.delete()
    return {"message": "Evento eliminado correctamente"}