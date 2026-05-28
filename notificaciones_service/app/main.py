from fastapi import FastAPI
from app.api.notificaciones_routes import router as notificaciones_router

app = FastAPI(title="Notificaciones Service")

app.include_router(notificaciones_router, prefix="/api/v1/notificaciones")

@app.get("/")
async def root():
    return {"message": "Notificaciones Service activo en el puerto 8006"}