from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import httpx
from typing import List, Dict, Any
from datetime import datetime
from app.core.security import obtener_usuario_actual
from app.models.evaluacion_model import EvaluacionModel

router = APIRouter(tags=["Evaluaciones"])

USUARIOS_SERVICE_URL = "http://usuarios_service:8002/api/v1/usuarios"

class EvaluacionCreate(BaseModel):
    estado: str
    fechaEvaluacion: datetime
    justificacion: str = ""
    actaAprobacion: str = "" 
    eventoId: str
    usuarioId: int

async def validar_secretaria(usuario_id: int):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{USUARIOS_SERVICE_URL}/{usuario_id}/rol")
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo verificar el usuario en el sistema.")
            rol = resp.json().get("rol")
            if rol != "secretariaAcademica":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado. Solo la Secretaria Académica tiene acceso.")
        except httpx.RequestError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="El Servicio de Usuarios no se encuentra disponible.")

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=EvaluacionModel)
async def crear_evaluacion(evaluacion_in: EvaluacionCreate, usuario_actual_id: int = Depends(obtener_usuario_actual)):
    await validar_secretaria(usuario_actual_id)
    evaluacion_db = EvaluacionModel(**evaluacion_in.model_dump())
    evaluacion_db.usuarioId = usuario_actual_id
    await evaluacion_db.insert()
    return evaluacion_db

@router.get("/", response_model=List[EvaluacionModel])
async def buscar_todas_las_evaluaciones():
    return await EvaluacionModel.find_all().to_list()

@router.get("/{evaluacion_id}", response_model=EvaluacionModel)
async def buscar_evaluacion_por_id(evaluacion_id: str):
    evaluacion = await EvaluacionModel.get(evaluacion_id)
    if not evaluacion:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")
    return evaluacion

@router.put("/{evaluacion_id}")
async def actualizar_evaluacion(evaluacion_id: str, datos_actualizados: Dict[str, Any], usuario_actual_id: int = Depends(obtener_usuario_actual)):
    await validar_secretaria(usuario_actual_id)
    evaluacion = await EvaluacionModel.get(evaluacion_id)
    if not evaluacion:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")
    await evaluacion.update({"$set": datos_actualizados})
    return await EvaluacionModel.get(evaluacion_id)

@router.delete("/{evaluacion_id}")
async def eliminar_evaluacion(evaluacion_id: str, usuario_actual_id: int = Depends(obtener_usuario_actual)):
    await validar_secretaria(usuario_actual_id)
    evaluacion = await EvaluacionModel.get(evaluacion_id)
    if not evaluacion:
        raise HTTPException(status_code=404, detail="Evaluación no existe.")
    await evaluacion.delete()
    return {"message": "Evaluación eliminada correctamente"}