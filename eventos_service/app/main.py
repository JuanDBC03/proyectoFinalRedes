from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import random

from app.db.conexion import connect_to_mongo, close_mongo_connection
from app.api.eventos_routes import router as eventos_router
from app.models.inscripcion_model import InscripcionModel
from app.api.inscripciones_routes import router as inscripciones_router

from app.models.evento_model import (
    EventoModel, Realizacion, Instalacion, Organizador, 
    Participante, EstadoEventoEnum, TipoEventoEnum, 
    TipoAvalEnum, UsuarioTipo, EstadoParticipacionEnum
)

# --- FUNCIÓN DE SEMBRADO PARA 150 EVENTOS VARIADOS ---
async def poblar_eventos_service():
    cantidad_eventos = await EventoModel.find_all().count()
    if cantidad_eventos >= 150:
        print(f"✅ Eventos Service: La base de datos ya tiene {cantidad_eventos} eventos. Se omite el sembrado.")
        return

    print("🔍 Eventos Service: Generando 150 eventos variados (Académicos, Lúdicos, Culturales)...")

    instalaciones_capacidades = {
        "SALON-101": 30, "SALON-102": 30, "SALON-201": 40, "SALON-202": 40,
        "SALON-301": 25, "SALON-302": 25, "AUD-PRINCIPAL": 200, "AUD-SECUNDARIO": 100,
        "AUD-B": 80, "LAB-SISTEMAS-01": 40, "LAB-SISTEMAS-02": 40, "LAB-FISICA-01": 30,
        "LAB-QUIMICA-01": 25, "CANCHA-FUTBOL": 100, "CANCHA-MULTIPLE": 50
    }

    prefijos = ["Taller de", "Seminario de", "Conferencia:", "Torneo de", "Campeonato de", "Festival de", "Olimpiada de", "Foro sobre"]
    temas = ["Inteligencia Artificial", "Ciberseguridad", "Fútbol 8 Interfacultades", "Ajedrez Relámpago", "MongoDB Avanzado", "Danza Folclórica", "Videojuegos (eSports)", "Salud Mental y Bienestar", "Pintura al Óleo", "Robótica Competitiva"]

    lista_instalaciones = list(instalaciones_capacidades.keys())
    eventos_a_insertar = []

    for i in range(50):
        # 🔥 FIX: Usamos Strings directos para evitar el AttributeError
        for estado_actual in ["aprobado", "rechazado", "registrado"]:
            
            nombre = f"{random.choice(prefijos)} {random.choice(temas)} - Edición {random.randint(1, 99)}"
            inst_id = random.choice(lista_instalaciones)
            capacidad_maxima = instalaciones_capacidades[inst_id]
            cupo_evento = random.randint(15, capacidad_maxima)
            docente_responsable_id = random.randint(2001, 2015)
            
            if estado_actual == "registrado":
                fecha_real = datetime.now(timezone.utc) + timedelta(days=random.randint(1, 30))
            else:
                fecha_real = datetime.now(timezone.utc) + timedelta(days=random.randint(-60, 20))
            
            cantidad_participantes = random.randint(0, min(15, cupo_evento))
            participantes_ids = random.sample(range(3001, 3024), k=cantidad_participantes)
            
            lista_participantes = [
                Participante(usuarioId=uid, estado=random.choice(["pendiente", "confirmado"])) 
                for uid in participantes_ids
            ]

            bloque_realizacion = Realizacion(
                instalaciones=[Instalacion(instalacionId=inst_id, capacidadInstalacion=capacidad_maxima)],
                fecha=fecha_real,
                horaInicio=f"{random.randint(8, 14):02d}:00",
                horaFin=f"{random.randint(15, 18):02d}:00"
            )

            bloque_organizador = [
                Organizador(
                    usuarioId=docente_responsable_id,
                    avalPDF=b"pdf_base64_simulado",
                    tipoAval=TipoAvalEnum.DIRECTOR_PROGRAMA,
                    tipo=UsuarioTipo.PRINCIPAL
                )
            ]

            tipo_al_azar = random.choice(list(TipoEventoEnum))

            eventos_a_insertar.append(
                EventoModel(
                    nombre=nombre,
                    estado=estado_actual,
                    tipo=tipo_al_azar,
                    capacidad=capacidad_maxima,
                    creadoPor=docente_responsable_id,
                    cupoMaximo=cupo_evento,
                    realizacion=bloque_realizacion,
                    organizador=bloque_organizador,
                    participantes=lista_participantes
                )
            )

    await EventoModel.insert_many(eventos_a_insertar)
    print(f"   -> 📅 Se insertaron {len(eventos_a_insertar)} eventos variados.")
    print("✅ ¡Sembrado de eventos completado y verificado!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo(db_name="db_eventos", models=[EventoModel, InscripcionModel])
    await poblar_eventos_service()
    yield
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan, title="Eventos Service")
app.include_router(eventos_router, prefix="/api/v1/eventos")
app.include_router(inscripciones_router, prefix="/api/v1/eventos/inscripciones")

@app.get("/")
async def root():
    return {"message": "Eventos Service conectado en el puerto 8003"}