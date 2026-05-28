from fastapi import APIRouter, HTTPException, status
from app.schemas.auth_schemas import LoginRequest, TokenResponse
from app.models.usuario_model import UsuarioModel, Password, EstadoPasswordEnum  # <-- Importamos los submodelos
from jose import jwt
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

router = APIRouter(tags=["Autenticación"])

# NOTA DE INFRAESTRUCTURA: En producción, SECRET_KEY debe ir en el archivo .env
SECRET_KEY = "super_clave_secreta_gestor_eventos" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class RegistroRequest(BaseModel):
    id: int
    email: str
    password: str

# --- Endpoint interno para registrar credenciales ---
@router.post("/registro", status_code=status.HTTP_201_CREATED)
async def registrar_credenciales(datos: RegistroRequest):
    # Verificamos si ya existe por su ID único
    existe = await UsuarioModel.get(datos.id)
    if not existe:
        # Creamos el documento pasando 'id' y tipando correctamente la Password
        nuevo_auth = UsuarioModel(
            id=datos.id, 
            email=datos.email, 
            password=[
                Password(
                    clave=datos.password, 
                    fechaCambio=datetime.now(), 
                    estado=EstadoPasswordEnum.ACTIVA
                )
            ]
        )
        await nuevo_auth.insert()
    return {"message": "Credenciales sincronizadas con éxito en Auth Service"}


# --- Tu código de login impecable ---
@router.post("/login", response_model=TokenResponse)
async def login(credenciales: LoginRequest):
    # 1. Buscar al usuario en la BD por email
    usuario = await UsuarioModel.find_one(UsuarioModel.email == credenciales.email)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # 2. Verificar la contraseña
    password_valida = False
    for pwd in usuario.password:
        estado_str = getattr(pwd.estado, 'value', str(pwd.estado))
        if estado_str == "activa" and pwd.clave == credenciales.password:
            password_valida = True
            break
    
    if not password_valida:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    # 3. Generar el Token JWT
    expira = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(usuario.id),  # ID del usuario (_id de mongo)
        "email": usuario.email,
        "exp": expira            
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return TokenResponse(access_token=token, token_type="bearer")

@router.delete("/eliminar/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_credenciales(usuario_id: int):
    # Buscamos si existe la credencial en db_auth
    usuario_auth = await UsuarioModel.get(usuario_id)
    if usuario_auth:
        await usuario_auth.delete() # ¡Lo borramos!
    # Si no existe, no hacemos nada, igual el objetivo era que no estuviera
    return None