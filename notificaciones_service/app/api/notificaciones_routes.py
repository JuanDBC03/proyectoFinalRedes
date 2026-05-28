from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
import httpx
import base64
from email.header import decode_header

router = APIRouter(tags=["Notificaciones"])

# --- CONFIGURACIÓN DE MAILHOG ---
conf = ConnectionConfig(
    MAIL_USERNAME="test",
    MAIL_PASSWORD="test",
    MAIL_FROM="notificaciones@universidad.edu.co",
    MAIL_PORT=1025,
    MAIL_SERVER="mailhog",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=False,
    VALIDATE_CERTS=False
)

# --- MODELO DEL PAYLOAD ---
class CorreoPayload(BaseModel):
    destinatario: EmailStr
    asunto: str
    cuerpo: str

# --- LIMPIADORES MÁGICOS PARA EL BUZÓN ---
def decodificar_asunto(asunto_raw: str) -> str:
    """Quita el formato =?utf-8?q?... de los asuntos de correo."""
    if not asunto_raw:
        return "Sin asunto"
    try:
        fragmentos = decode_header(asunto_raw)
        asunto_limpio = ""
        for texto, codificacion in fragmentos:
            if isinstance(texto, bytes):
                asunto_limpio += texto.decode(codificacion or "utf-8", errors="ignore")
            else:
                asunto_limpio += texto
        return asunto_limpio
    except Exception:
        return asunto_raw

def extraer_cuerpo_limpio(msg: dict) -> str:
    """Decodifica el cuerpo en Base64 y limpia el ruido multiparte de MailHog."""
    # 1. Intentar por las partes MIME estructuradas de MailHog
    partes = msg.get("MIME", {}).get("Parts", [])
    if partes:
        for parte in partes:
            headers = parte.get("Headers", {})
            content_type = "".join(headers.get("Content-Type", [])).lower()
            transfer_encoding = "".join(headers.get("Content-Transfer-Encoding", [])).lower()
            cuerpo = parte.get("Body", "")

            if "base64" in transfer_encoding:
                try:
                    cuerpo = base64.b64decode(cuerpo).decode("utf-8", errors="ignore")
                except Exception:
                    pass
            
            if "text/html" in content_type or "text/plain" in content_type:
                return cuerpo

    # 2. Fallback: Si viene crudo en el Content Body principal
    cuerpo_raw = msg.get("Content", {}).get("Body", "")
    if "Content-Transfer-Encoding: base64" in cuerpo_raw:
        try:
            lineas = cuerpo_raw.splitlines()
            bloque_base64 = ""
            empezar_captura = False
            for linea in lineas:
                if empezar_captura and linea.startswith("----"):
                    break
                if empezar_captura:
                    bloque_base64 += linea.strip()
                if linea.strip() == "":
                    empezar_captura = True
            if bloque_base64:
                return base64.b64decode(bloque_base64).decode("utf-8", errors="ignore")
        except Exception:
            pass

    return cuerpo_raw

# --- ENDPOINT PARA ENVIAR CORREOS ---
@router.post("/enviar")
async def enviar_correo(payload: CorreoPayload, background_tasks: BackgroundTasks):
    message = MessageSchema(
        subject=payload.asunto,
        recipients=[payload.destinatario],
        body=payload.cuerpo,
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    return {"message": f"Correo encolado para {payload.destinatario}"}

# ➕👇 ENDPOINT OPTIMIZADO: LEER EL BUZÓN LIMPIO PARA EL FRONTEND
@router.get("/buzon")
async def obtener_buzon_simulado():
    url_mailhog_api = "http://mailhog:8025/api/v1/messages"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url_mailhog_api)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="No se pudo conectar con el servidor de correos.")
            
            datos = response.json()
            correos_limpios = []
            
            for msg in datos:
                remitente = msg.get("From", {}).get("Mailbox", "") + "@" + msg.get("From", {}).get("Domain", "")
                
                to_list = msg.get("To", [])
                destinatario = ""
                if to_list:
                    destinatario = to_list[0].get("Mailbox", "") + "@" + to_list[0].get("Domain", "")
                
                # Procesamos con las funciones de limpieza
                asunto_raw = msg.get("Content", {}).get("Headers", {}).get("Subject", ["Sin asunto"])[0]
                asunto = decodificar_asunto(asunto_raw)
                cuerpo = extraer_cuerpo_limpio(msg)
                
                correos_limpios.append({
                    "id": msg.get("ID"),
                    "fecha": msg.get("Created"),
                    "remitente": remitente,
                    "destinatario": destinatario,
                    "asunto": asunto,
                    "cuerpo": cuerpo
                })
                
            return correos_limpios
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error de conexión con MailHog: {e}")