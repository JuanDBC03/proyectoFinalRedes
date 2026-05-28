from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.conexion import connect_to_mongo, close_mongo_connection
from app.models.instalacion_model import InstalacionModel, TipoInstalacionEnum
from app.api.instalaciones_routes import router as instalaciones_router

# --- FUNCIÓN DE SEMBRADO PARA INSTALACIONES ---
async def poblar_instalaciones():
    # 💥 BOTÓN DE AUTODESTRUCCIÓN: Borramos la colección para limpiar cualquier ID basura
    # (Una vez que pruebes que funciona, puedes comentar esta línea si no quieres que se borre todo al reiniciar)
    await InstalacionModel.get_motor_collection().drop()
    print("🗑️ Colección de instalaciones limpiada desde cero.")

    # Verificamos cuántas instalaciones existen
    cantidad_instalaciones = await InstalacionModel.find_all().count()
    
    if cantidad_instalaciones >= 15:
        print(f"✅ Instalaciones Service: La BD ya cuenta con {cantidad_instalaciones} espacios. Se omite el sembrado.")
        return

    print("🔍 Instalaciones Service: Iniciando sembrado masivo de 15 instalaciones...")

    instalaciones_base = [
        # 6 Salones
        InstalacionModel(_id="SALON-101", ubicacion="Edificio A - Piso 1", tipo=TipoInstalacionEnum.SALON, capacidad=30),
        InstalacionModel(_id="SALON-102", ubicacion="Edificio A - Piso 1", tipo=TipoInstalacionEnum.SALON, capacidad=30),
        InstalacionModel(_id="SALON-201", ubicacion="Edificio A - Piso 2", tipo=TipoInstalacionEnum.SALON, capacidad=40),
        InstalacionModel(_id="SALON-202", ubicacion="Edificio A - Piso 2", tipo=TipoInstalacionEnum.SALON, capacidad=40),
        InstalacionModel(_id="SALON-301", ubicacion="Edificio B - Piso 3", tipo=TipoInstalacionEnum.SALON, capacidad=25),
        InstalacionModel(_id="SALON-302", ubicacion="Edificio B - Piso 3", tipo=TipoInstalacionEnum.SALON, capacidad=25),
        
        # 3 Auditorios
        InstalacionModel(_id="AUD-PRINCIPAL", ubicacion="Edificio Central - Piso 1", tipo=TipoInstalacionEnum.AUDITORIO, capacidad=200),
        InstalacionModel(_id="AUD-SECUNDARIO", ubicacion="Edificio Central - Piso 2", tipo=TipoInstalacionEnum.AUDITORIO, capacidad=100),
        InstalacionModel(_id="AUD-B", ubicacion="Edificio B - Piso 1", tipo=TipoInstalacionEnum.AUDITORIO, capacidad=80),
        
        # 4 Laboratorios
        InstalacionModel(_id="LAB-SISTEMAS-01", ubicacion="Edificio C - Piso 1", tipo=TipoInstalacionEnum.LABORATORIO, capacidad=40),
        InstalacionModel(_id="LAB-SISTEMAS-02", ubicacion="Edificio C - Piso 1", tipo=TipoInstalacionEnum.LABORATORIO, capacidad=40),
        InstalacionModel(_id="LAB-FISICA-01", ubicacion="Edificio C - Piso 2", tipo=TipoInstalacionEnum.LABORATORIO, capacidad=30),
        InstalacionModel(_id="LAB-QUIMICA-01", ubicacion="Edificio C - Piso 3", tipo=TipoInstalacionEnum.LABORATORIO, capacidad=25),
        
        # 2 Canchas
        InstalacionModel(_id="CANCHA-FUTBOL", ubicacion="Zona Deportiva Sur", tipo=TipoInstalacionEnum.CANCHA, capacidad=100),
        InstalacionModel(_id="CANCHA-MULTIPLE", ubicacion="Zona Deportiva Norte", tipo=TipoInstalacionEnum.CANCHA, capacidad=50)
    ]

    # Inserción masiva y eficiente en MongoDB
    await InstalacionModel.insert_many(instalaciones_base)
    print("   -> 🏢 Se insertaron 15 instalaciones (Salones, Auditorios, Laboratorios y Canchas).")
    print("✅ ¡Sembrado de instalaciones completado con éxito!")

# --- ARRANQUE DE LA APLICACIÓN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conectamos exclusivamente a db_instalaciones con su modelo correspondiente
    await connect_to_mongo(db_name="db_instalaciones", models=[InstalacionModel])
    
    # Ejecutamos el sembrado al arrancar
    await poblar_instalaciones()
    
    yield
    
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan, title="Instalaciones Service")

app.include_router(instalaciones_router, prefix="/api/v1/instalaciones")

@app.get("/")
async def root():
    return {"message": "Instalaciones Service conectado en el puerto 8005"}