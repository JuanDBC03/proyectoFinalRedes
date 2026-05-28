from fastapi import APIRouter, HTTPException, status, Depends
from app.models.instalacion_model import InstalacionModel
import httpx

from app.core.security import obtener_usuario_actual
from pydantic import BaseModel

# Creamos este modelo que hace MATCH EXACTO con lo que envía tu JS
class InstalacionPayload(BaseModel):
    id: str
    ubicacion: str
    tipo: str
    capacidad: int

router = APIRouter(tags=["Instalaciones"])
USUARIOS_SERVICE_URL = "http://usuarios_service:8002/api/v1/usuarios"

async def validar_secretaria(usuario_id: int):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{USUARIOS_SERVICE_URL}/{usuario_id}/rol")
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="No se pudo verificar el usuario.")
            if resp.json().get("rol") != "secretariaAcademica":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Permiso denegado. Solo la Secretaria Académica puede gestionar instalaciones."
                )
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Servicio de Usuarios no disponible")

@router.get("/")
async def listar_instalaciones():
    return await InstalacionModel.find_all().to_list()

@router.get("/{instalacion_id}")
async def buscar_instalacion(instalacion_id: str):
    instalacion = await InstalacionModel.get(instalacion_id)
    if not instalacion:
        raise HTTPException(status_code=404, detail="Instalación no encontrada")
    return instalacion

@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_instalacion(
    payload: InstalacionPayload, 
    usuario_actual_id: int = Depends(obtener_usuario_actual)
):
    await validar_secretaria(usuario_actual_id)
    
    # 1. Verificamos si ya existe
    existente = await InstalacionModel.get(payload.id)
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una instalación con este ID.")
        
    # 2. Creamos el documento de Beanie inyectando el _id manualmente a la fuerza
    nueva_instalacion = InstalacionModel(
        _id=payload.id,
        ubicacion=payload.ubicacion,
        tipo=payload.tipo,
        capacidad=payload.capacidad
    )
    
    # 3. Guardamos en MongoDB
    await nueva_instalacion.insert()
    return {"message": "Instalación creada con éxito"}

@router.put("/{instalacion_id}")
async def editar_instalacion(
    instalacion_id: str, 
    payload: InstalacionPayload, # Usamos el mismo payload que en POST para que no haya cruces
    usuario_actual_id: int = Depends(obtener_usuario_actual)
):
    await validar_secretaria(usuario_actual_id)
    
    inst_bd = await InstalacionModel.get(instalacion_id)
    if not inst_bd:
        raise HTTPException(status_code=404, detail="Instalación no encontrada")
    
    # Actualizamos los campos manualmente (No se actualiza el ID porque en Mongo no se puede)
    inst_bd.ubicacion = payload.ubicacion
    inst_bd.tipo = payload.tipo
    inst_bd.capacidad = payload.capacidad
    
    await inst_bd.save()
        
    return {"message": "Instalación actualizada con éxito"}

@router.delete("/{instalacion_id}")
async def eliminar_instalacion(
    instalacion_id: str, 
    usuario_actual_id: int = Depends(obtener_usuario_actual)
):
    await validar_secretaria(usuario_actual_id)
    
    instalacion = await InstalacionModel.get(instalacion_id)
    if not instalacion:
        raise HTTPException(status_code=404, detail="Instalación no encontrada")
    
    await instalacion.delete()
    return {"message": f"La instalación {instalacion_id} ha sido eliminada"}