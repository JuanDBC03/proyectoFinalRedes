from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
import random
from fastapi.middleware.cors import CORSMiddleware 
from app.core.config import settings               
from app.db.conexion import connect_to_mongo, close_mongo_connection
from app.models.usuario_model import UsuarioModel
from app.models.facultad_model import FacultadModel, UnidadAcademica, Programa
from app.api.usuarios_routes import router as usuarios_router

# --- FUNCIÓN DE SEMBRADO MASIVO Y RELACIONAL ---
async def poblar_base_de_datos():
    # Verificamos si ya hay datos para no duplicar en cada reinicio
    cantidad_usuarios = await UsuarioModel.find_all().count()
    if cantidad_usuarios >= 50:
        print(f"✅ La base de datos ya tiene {cantidad_usuarios} usuarios. Se omite el sembrado masivo.")
        return

    print("🔍 Iniciando sembrado masivo de 12 Facultades, 15 Programas/Unidades y 50 Usuarios...")

    # 1. NOMBRES BASE PARA LA UNIVERSIDAD
    nombres_facultades = ["Ingeniería", "Ciencias de la Salud", "Ciencias Básicas", "Ciencias Económicas", "Humanidades", "Artes", "Educación", "Derecho", "Ciencias Agrarias", "Odontología", "Medicina Veterinaria", "Ciencias Sociales"]
    nombres_unidades = ["Depto. de Sistemas", "Depto. de Matemáticas", "Depto. de Física", "Depto. de Medicina", "Depto. de Economía", "Depto. de Lenguas", "Depto. de Diseño", "Depto. de Pedagogía", "Depto. de Derecho Penal", "Depto. de Agronomía", "Depto. de Biología", "Depto. de Historia", "Depto. de Química", "Depto. de Cirugía", "Depto. de Finanzas"]
    nombres_programas = ["Ing. de Sistemas", "Ing. Industrial", "Matemáticas", "Medicina", "Enfermería", "Economía", "Administración", "Filosofía", "Diseño Gráfico", "Licenciatura en Inglés", "Derecho", "Ing. Agronómica", "Biología", "Historia", "Contaduría"]
    
    # 2. CREACIÓN DE 12 FACULTADES CON 15 PROGRAMAS/UNIDADES REPARTIDOS
    facultades_creadas = []
    lista_unidades_global = []
    lista_programas_global = []
    
    idx_item = 0
    for i, nom_fac in enumerate(nombres_facultades):
        # Las primeras 3 facultades tendrán 2 programas/unidades cada una. El resto, 1. (Total = 15)
        items_a_asignar = 2 if i < 3 else 1
        
        unidades_locales = []
        programas_locales = []
        
        for _ in range(items_a_asignar):
            unidades_locales.append(UnidadAcademica(nombre=nombres_unidades[idx_item]))
            programas_locales.append(Programa(nombre=nombres_programas[idx_item]))
            idx_item += 1
            
        facultad = FacultadModel(nombre=f"Facultad de {nom_fac}", unidadAcademica=unidades_locales, programa=programas_locales)
        await facultad.insert()
        facultades_creadas.append(facultad)
        
        # Guardamos referencias planas para asignar fácilmente a docentes y estudiantes
        for u in facultad.unidadAcademica:
            lista_unidades_global.append(u.unidadId)
        for p in facultad.programa:
            lista_programas_global.append(p.programaId)

    print("   -> 🏢 12 Facultades con sus 15 Unidades y 15 Programas creados.")

    # 3. LISTAS DE NOMBRES PARA GENERAR 50 USUARIOS ALEATORIOS
    nombres = ["Ana", "Carlos", "Luis", "Maria", "Juan", "Pedro", "Laura", "Sofia", "Jorge", "Marta", "Diego", "Valentina", "Andres", "Camila", "Daniel", "Natalia", "Alejandro", "Paula", "Kevin", "Daniela"]
    apellidos = ["Gomez", "Lopez", "Perez", "Rodriguez", "Garcia", "Martinez", "Hernandez", "Gonzalez", "Diaz", "Ramirez", "Alvarez", "Ruiz", "Fernandez", "Jimenez", "Moreno"]

    usuarios_a_insertar = []

    # A. Crear 12 Secretarias (1 por cada Facultad) - IDs 1001 al 1012
    for i, fac in enumerate(facultades_creadas):
        usuarios_a_insertar.append(
            UsuarioModel(
                _id=1001 + i, nombre=random.choice(nombres), apellidos=random.choice(apellidos), email=f"secretaria{i+1}@universidad.edu", telefonos=[f"30000010{i:02d}"],
                password=[{"clave": "secreta123", "fechaCambio": datetime.now(), "estado": "activa"}],
                vinculacion=[{"rol": "secretariaAcademica", "facultadId": fac.id, "estado": "activo", "fecha": datetime.now()}]
            )
        )

    # B. Crear 15 Docentes (1 por cada Unidad Académica) - IDs 2001 al 2015
    for i, uni_id in enumerate(lista_unidades_global):
        usuarios_a_insertar.append(
            UsuarioModel(
                _id=2001 + i, nombre=random.choice(nombres), apellidos=random.choice(apellidos), email=f"docente{i+1}@universidad.edu", telefonos=[f"30000020{i:02d}"],
                password=[{"clave": "docente123", "fechaCambio": datetime.now(), "estado": "activa"}],
                vinculacion=[{"rol": "docente", "unidadId": uni_id, "estado": "activo", "fecha": datetime.now()}]
            )
        )

    # C. Crear 23 Estudiantes (Asignados aleatoriamente a los 15 programas) - IDs 3001 al 3023
    for i in range(23):
        prog_id = random.choice(lista_programas_global)
        usuarios_a_insertar.append(
            UsuarioModel(
                _id=3001 + i, nombre=random.choice(nombres), apellidos=random.choice(apellidos), email=f"estudiante{i+1}@universidad.edu", telefonos=[f"30000030{i:02d}"],
                password=[{"clave": "estudiante123", "fechaCambio": datetime.now(), "estado": "activa"}],
                vinculacion=[{"rol": "estudiante", "programaId": prog_id, "estado": "activo", "fecha": datetime.now()}]
            )
        )

    # 4. INSERCIÓN MASIVA
    await UsuarioModel.insert_many(usuarios_a_insertar)
    print(f"   -> 👤 Se insertaron 50 usuarios masivamente (12 Secretarias, 15 Docentes, 23 Estudiantes).")
    print("✅ ¡Sembrado masivo completado exitosamente!")

# --- ARRANQUE DE LA APLICACIÓN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conexión exclusiva a db_usuarios con sus dos modelos
    await connect_to_mongo(db_name="db_usuarios", models=[UsuarioModel, FacultadModel])
    
    # Ejecutamos el sembrado inteligente justo después de conectar
    await poblar_base_de_datos()
    
    yield
    
    # Cierre limpio de la conexión
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan, title="Usuarios Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, PUT, DELETE, etc.
    allow_headers=["*"], # Permite enviar Tokens en los headers

)

app.include_router(usuarios_router, prefix="/api/v1/usuarios")

@app.get("/")
async def root():
    return {"message": "Usuarios Service conectado en el puerto 8002"}