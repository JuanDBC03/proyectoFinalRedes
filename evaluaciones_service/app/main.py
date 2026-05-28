from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import random
import httpx
from beanie import PydanticObjectId

from app.db.conexion import connect_to_mongo, close_mongo_connection
from app.api.evaluaciones_routes import router as evaluaciones_router
from app.models.evaluacion_model import EvaluacionModel, EstadoEvaluacionEnum

# --- FUNCIÓN DE SEMBRADO PARA 100 EVALUACIONES ---
async def poblar_evaluaciones():
    cantidad_evaluaciones = await EvaluacionModel.find_all().count()
    if cantidad_evaluaciones >= 100:
        print(f"✅ Evaluaciones Service: La BD ya tiene {cantidad_evaluaciones} evaluaciones. Se omite el sembrado.")
        return

    print("🔍 Evaluaciones Service: Iniciando sembrado para los 100 eventos procesados...")

    eventos_reales = []
    try:
        # Aumentamos el timeout un poco por si FastAPI tarda un segundo enviando los 150
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get("http://eventos_service:8003/api/v1/eventos")
            if resp.status_code == 200:
                eventos_reales = resp.json()
    except Exception as e:
        print(f"⚠️ No se pudo contactar al servicio de eventos: {e}")
        return

    evaluaciones_a_insertar = []
    justificaciones_rechazo = [
        "Falta información sobre los avales institucionales.",
        "El cupo supera la capacidad de la instalación solicitada.",
        "La fecha choca con la semana de exámenes parciales.",
        "No se especificaron claramente los objetivos del evento."
    ]

    for evento in eventos_reales:
        estado_ev = evento.get("estado", "").lower()
        
        # Filtramos solo los que ya fueron procesados
        if estado_ev in ["aprobado", "rechazado"]:
            # Manejo seguro del ID
            evento_id = PydanticObjectId(evento.get("_id") or evento.get("id"))
            docente_id = evento.get("creadoPor", 2001)
            nombre_evento = evento.get("nombre", "Evento Genérico")
            
            estado_enum = EstadoEvaluacionEnum.APROBADO if estado_ev == "aprobado" else EstadoEvaluacionEnum.RECHAZADO
            justificacion = "El evento cumple con todos los requisitos académicos y logísticos." if estado_enum == EstadoEvaluacionEnum.APROBADO else random.choice(justificaciones_rechazo)

            evaluaciones_a_insertar.append(
                EvaluacionModel(
                    nombre=f"Acta de Revisión Técnica - {nombre_evento}",
                    descripcion="Evaluación formal de viabilidad y pertinencia académica.",
                    estado=estado_enum,
                    fechaEvaluacion=datetime.now() - timedelta(days=random.randint(1, 10)),
                    justificacion=justificacion,
                    actaAprovacion=b"pdf_base64_generico",
                    eventoId=evento_id,
                    usuarioId=docente_id,
                    creadoPor=random.randint(1001, 1012)
                )
            )

    if evaluaciones_a_insertar:
        await EvaluacionModel.insert_many(evaluaciones_a_insertar)
        print(f"   -> 📝 Se insertaron {len(evaluaciones_a_insertar)} evaluaciones asociadas a eventos.")
        print("✅ ¡Sembrado de evaluaciones completado con éxito!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo(db_name="db_evaluaciones", models=[EvaluacionModel])
    await poblar_evaluaciones()
    yield
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan, title="Evaluaciones Service")
app.include_router(evaluaciones_router, prefix="/api/v1/evaluaciones")

@app.get("/")
async def root():
    return {"message": "Evaluaciones Service conectado en el puerto 8004"}