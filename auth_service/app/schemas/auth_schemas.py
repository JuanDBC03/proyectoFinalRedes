from pydantic import BaseModel, EmailStr

# Lo que el frontend nos envía
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Lo que nosotros le devolvemos al frontend
class TokenResponse(BaseModel):
    access_token: str
    token_type: str