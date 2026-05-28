from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime

from app.db.conexion import connect_to_mongo, close_mongo_connection
from app.models.usuario_model import UsuarioModel 
from app.api.auth_routes import router as auth_router

# --- FUNCIÓN DE SEMBRADO ESPEJO PARA AUTH SERVICE ---
async def poblar_auth_service():
    # Contamos cuántas credenciales existen en db_auth
    cantidad_usuarios = await UsuarioModel.find_all().count()
    if cantidad_usuarios >= 50:
        print(f"✅ Auth Service: La base de datos ya tiene {cantidad_usuarios} credenciales. Se omite el sembrado.")
        return

    print("🔍 Auth Service: Sincronizando las credenciales para los 50 usuarios masivos...")

    usuarios_auth = []

    # A. Espejo de las 12 Secretarias (IDs 1001 al 1012)
    for i in range(12):
        usuarios_auth.append(
            UsuarioModel(
                _id=1001 + i,
                nombre="Secretaria",
                apellidos=f"Número {i+1}",
                email=f"secretaria{i+1}@universidad.edu",
                telefonos=[f"30000010{i:02d}"],
                password=[{"clave": "secreta123", "fechaCambio": datetime.now(), "estado": "activa"}],
                vinculacion=[] # db_auth no necesita vinculación académica detallada
            )
        )

    # B. Espejo de los 15 Docentes (IDs 2001 al 2015)
    for i in range(15):
        usuarios_auth.append(
            UsuarioModel(
                _id=2001 + i,
                nombre="Docente",
                apellidos=f"Número {i+1}",
                email=f"docente{i+1}@universidad.edu",
                telefonos=[f"30000020{i:02d}"],
                password=[{"clave": "docente123", "fechaCambio": datetime.now(), "estado": "activa"}],
                vinculacion=[]
            )
        )

    # C. Espejo de los 23 Estudiantes (IDs 3001 al 3023)
    for i in range(23):
        usuarios_auth.append(
            UsuarioModel(
                _id=3001 + i,
                nombre="Estudiante",
                apellidos=f"Número {i+1}",
                email=f"estudiante{i+1}@universidad.edu",
                telefonos=[f"30000030{i:02d}"],
                password=[{"clave": "estudiante123", "fechaCambio": datetime.now(), "estado": "activa"}],
                vinculacion=[]
            )
        )

    # Inserción masiva en db_auth
    await UsuarioModel.insert_many(usuarios_auth)
    print(f"   -> 🔐 Se sincronizaron las 50 cuentas de acceso de forma masiva en db_auth.")
    print("✅ ¡Sembrado de autenticación completado con éxito!")

# --- ARRANQUE DE LA APLICACIÓN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conexión exclusiva a la base de datos db_auth
    await connect_to_mongo(db_name="db_auth", models=[UsuarioModel])
    
    # Ejecutamos el sembrado espejo
    await poblar_auth_service()
    
    yield
    
    # Cierre limpio de la conexión
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan, title="Auth Service")

app.include_router(auth_router, prefix="/api/v1/auth")

@app.get("/")
async def root():
    return {"message": "Auth Service conectado y funcionando al 100%"}