from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

# Le decimos a FastAPI dónde se hace el login (útil para la interfaz de Swagger)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/api/v1/auth/login")

# Estos datos deben ser EXACTAMENTE los mismos que tienes en tu Auth Service
SECRET_KEY = "super_clave_secreta_gestor_eventos" 
ALGORITHM = "HS256"

async def obtener_usuario_actual(token: str = Depends(oauth2_scheme)) -> int:
    """
    Desencripta el token JWT enviado por el frontend,
    valida su autenticidad y extrae el ID del usuario.
    """
    try:
        # Decodificamos usando la misma llave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # En el Auth Service guardamos el ID en la variable "sub"
        usuario_id: str = payload.get("sub") 
        
        if usuario_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token inválido: No contiene información del usuario."
            )
            
        return int(usuario_id)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudieron validar las credenciales. El token expiró o fue alterado.",
            headers={"WWW-Authenticate": "Bearer"},
        )