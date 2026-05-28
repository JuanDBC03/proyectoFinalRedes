from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from bson import ObjectId
from passlib.context import CryptContext
from typing import Optional, List  # <-- NUEVO: Para poder usar datos opcionales y listas en el PUT
import httpx  # <-- Importamos httpx para comunicarnos con el Auth Service
from app.models.usuario_model import (
    UsuarioModel, Password, Vinculacion, 
    EstadoPasswordEnum, RolUsuarioEnum, EstadoVinculacionEnum
)

# Configuramos el encriptador de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# URL interna de Docker hacia el Auth Service
AUTH_SERVICE_URL = "http://auth_service:8001/api/v1/auth"

router = APIRouter(tags=["Usuarios"])

@router.get("/")
async def obtener_todos_los_usuarios():
    # Va a la base de datos db_usuarios y trae todos los registros
    usuarios = await UsuarioModel.find_all().to_list()
    return usuarios

# 👇 AQUÍ ESTÁ EL ENDPOINT NUEVO: OBTENER USUARIO POR ID
@router.get("/{usuario_id}")
async def obtener_usuario_por_id(usuario_id: int):
    usuario = await UsuarioModel.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Devolvemos los datos básicos seguros (sin exponer las contraseñas ni vinculaciones)
    # Unimos nombre y apellido para que el frontend lo muestre completo
    return {
        "id": usuario.id,
        "nombre": f"{usuario.nombre} {usuario.apellidos}", 
        "email": usuario.email
    }

@router.get("/{usuario_id}/rol")
async def obtener_rol_usuario(usuario_id: int):
    usuario = await UsuarioModel.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Buscamos en su vinculación cuál es su rol activo
    for vinc in usuario.vinculacion:
        if vinc.estado == "activo":
            return {"rol": vinc.rol}
            
    # Si no tiene vinculación activa
    raise HTTPException(status_code=400, detail="El usuario no tiene una vinculación activa")

# --- MODELO PAYLOAD (Recibe los datos del frontend para CREAR) ---
class CrearUsuarioPayload(BaseModel):
    id: int
    nombre: str
    apellidos: str
    email: EmailStr
    telefono: str
    password: str
    rol: str
    entidad_id: str

# --- ENDPOINT: CREAR USUARIOS (Solo Secretaria Académica) ---
@router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_nuevo_usuario(payload: CrearUsuarioPayload, creador_id: int):
    # 1. Buscamos al usuario que está intentando crear el registro
    creador = await UsuarioModel.get(creador_id)
    if not creador:
        raise HTTPException(status_code=404, detail="El usuario creador no existe.")
    
    # 2. Verificamos que el creador tenga el rol adecuado (secretariaAcademica)
    es_secretaria = False
    for vinc in creador.vinculacion:
        if vinc.estado == "activo" and vinc.rol == "secretariaAcademica":
            es_secretaria = True
            break
            
    if not es_secretaria:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Permiso denegado. Solo la Secretaria Académica puede crear usuarios."
        )
        
    # 3. VALIDACIÓN: Que no se repita el ID
    if await UsuarioModel.get(payload.id):
        raise HTTPException(status_code=400, detail=f"El ID o Cédula {payload.id} ya existe en el sistema.")
        
    # 4. VALIDACIÓN: Que no se repita el Correo
    if await UsuarioModel.find_one(UsuarioModel.email == payload.email):
        raise HTTPException(status_code=400, detail="El correo electrónico ya está en uso.")

    # 5. ARMAMOS LA CONTRASEÑA (AHORA SÍ ENCRIPTADA)
    password_encriptada = pwd_context.hash(payload.password)
    
    nueva_password = Password(
        clave=password_encriptada, 
        fechaCambio=datetime.now(timezone.utc),
        estado=EstadoPasswordEnum.ACTIVA
    )

    # 6. ARMAMOS LA VINCULACIÓN DEPENDIENDO DEL ROL
    vinc = Vinculacion(
        rol=RolUsuarioEnum(payload.rol),
        fecha=datetime.now(timezone.utc),
        estado=EstadoVinculacionEnum.ACTIVO
    )

    # Transformar el string del ID a ObjectId de Mongo
    try:
        entidad_oid = ObjectId(payload.entidad_id) if payload.entidad_id else None
    except Exception:
        raise HTTPException(status_code=400, detail="ID de entidad académica inválido.")

    if payload.rol == RolUsuarioEnum.ESTUDIANTE:
        vinc.programaId = entidad_oid
    elif payload.rol == RolUsuarioEnum.DOCENTE:
        vinc.unidadId = entidad_oid
    elif payload.rol == RolUsuarioEnum.SECRETARIA:
        vinc.facultadId = entidad_oid

    # 7. GUARDAMOS EL NUEVO USUARIO EN DB_USUARIOS
    nuevo_usuario = UsuarioModel(
        id=payload.id,
        nombre=payload.nombre,
        apellidos=payload.apellidos,
        email=payload.email,
        telefonos=[payload.telefono],
        password=[nueva_password],
        vinculacion=[vinc]
    )

    await nuevo_usuario.insert()

    # 8. SINCRONIZAMOS CON AUTH SERVICE
    async with httpx.AsyncClient() as client:
        try:
            payload_auth = {
                "id": nuevo_usuario.id,
                "email": nuevo_usuario.email,
                "password": payload.password  # Enviamos la clave en plano para que el Auth Service la encripte allá
            }
            resp = await client.post(f"{AUTH_SERVICE_URL}/registro", json=payload_auth)
            
            if resp.status_code != 201:
                print("Advertencia: Se creó el usuario, pero falló la sincronización con Auth Service.")
        except httpx.RequestError as e:
            print(f"Error de red contactando al Auth Service: {e}")

    return {"message": "Usuario creado y sincronizado exitosamente", "usuario_id": str(nuevo_usuario.id)}


# --- MODELO PAYLOAD (Recibe los datos del frontend para ACTUALIZAR) ---
class ActualizarUsuarioPayload(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    telefonos: Optional[List[str]] = None


# --- ENDPOINT: ACTUALIZAR PERFIL DE USUARIO ---
@router.put("/{usuario_id}")
async def actualizar_usuario(usuario_id: int, payload: ActualizarUsuarioPayload):
    # 1. Buscamos el usuario en db_usuarios
    usuario = await UsuarioModel.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # 2. Extraemos solo los campos que no vengan nulos
    datos_actualizar = payload.model_dump(exclude_unset=True)
    
    # 3. Aplicamos la actualización en la BD
    if datos_actualizar:
        await usuario.update({"$set": datos_actualizar})
        
    return {"message": "Perfil de usuario actualizado con éxito"}


# --- ENDPOINT: ELIMINAR USUARIO ---
@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(usuario_id: int):
    # 1. Buscamos el perfil en db_usuarios
    usuario = await UsuarioModel.get(usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2. Lo eliminamos de db_usuarios
    await usuario.delete()

    # 3. Le avisamos al Auth Service que borre sus credenciales
    url_auth = f"{AUTH_SERVICE_URL}/eliminar/{usuario_id}"
    
    async with httpx.AsyncClient() as client:
        try:
            await client.delete(url_auth)
        except httpx.RequestError as e:
            print(f"Advertencia: Se borró el perfil, pero falló la conexión con Auth Service: {e}")
            
    return None