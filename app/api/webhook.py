from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, Request, BackgroundTasks

from app.config import settings
from app.services import whatsapp
from app.services import transcription

logger = logging.getLogger(__name__)
router = APIRouter()

# Inyectado desde main.py al iniciar la app
_agent = None


def init_dependencies(agent) -> None:
    global _agent
    _agent = agent


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Verificación del webhook (challenge de Meta)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verificado correctamente")
        return int(hub_challenge) if hub_challenge.isdigit() else hub_challenge
    raise HTTPException(status_code=403, detail="Token de verificación inválido")


async def _process_message_background(phone: str, text: str, replied_to_id: str | None = None, msg_type: str = "text", media_id: str | None = None):
    try:
        from app.db.database import async_session_maker
        from app.services.user_service import get_or_create_user
        from app.services.paywall import check_media_allowed, MediaNotAllowed, PaywallException
        
        async with async_session_maker() as session:
            # 6.1 and 6.2 Get or create user
            user = await get_or_create_user(session, phone)
            plan_type = user.plan  # Read from database
            
            # 6.3 Run paywall checks
            try:
                await check_media_allowed(plan_type, msg_type)
            except MediaNotAllowed as e:
                await whatsapp.send_text(phone, f"🚀 Ups! Tu plan actual no permite mensajes tipo {msg_type}. ¡Actualizá a PREMIUM para esto y mucho más!")
                return
            except PaywallException as e:
                await whatsapp.send_text(phone, "🚀 Ups! Alcanzaste un límite de tu plan. ¡Actualizá a PREMIUM para más beneficios!")
                return

        if msg_type == "audio" and media_id:
            await whatsapp.send_text(phone, "Escuchando audio... 🎧")
            audio_bytes = await whatsapp.download_media(media_id)
            if not audio_bytes:
                await whatsapp.send_text(phone, "No pude descargar el audio 😔")
                return
            
            text = await transcription.transcribe_audio(audio_bytes)
            if not text:
                await whatsapp.send_text(phone, "No pude transcribir el audio 😔")
                return
        elif msg_type == "image":
            await whatsapp.send_text(phone, "Recibí tu imagen, pero aún no puedo leer texto en imágenes. ¡Pronto podré hacerlo! 📸")
            return

        reply = await _agent.process(phone, text, replied_to_id=replied_to_id)
        if reply:
            wamid = await whatsapp.send_text(phone, reply)
            if wamid:
                _agent.memory.store_wamid(phone, wamid, reply)
    except Exception as e:
        logger.error("Error procesando mensaje de %s: %s", phone, e, exc_info=True)


@router.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """Recepción de mensajes entrantes de WhatsApp."""
    body = await request.json()

    # Extraer mensaje del payload de Meta
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Ignorar si no hay mensajes (ej: status updates)
        if "messages" not in value:
            return {"status": "ok"}

        message = value["messages"][0]
        phone = message["from"]
        msg_type = message.get("type", "")

        # Solo procesar mensajes de texto, audio e imagen
        if msg_type not in ["text", "audio", "image"]:
            logger.info("Mensaje no soportado ignorado de %s (tipo: %s)", phone, msg_type)
            return {"status": "ok"}

        text = ""
        media_id = None
        is_audio = False
        is_image = False

        if msg_type == "text":
            text = message["text"]["body"]
        elif msg_type == "audio":
            media_id = message["audio"]["id"]
            is_audio = True
        elif msg_type == "image":
            media_id = message["image"]["id"]
            is_image = True

        # Check if it's a group chat (indicated by the presence of group_id)
        group_id = message.get("group_id")
        if group_id:
            # Group chat logic
            if "@Tesorero" not in text:
                logger.info("Ignorando mensaje de grupo %s sin mención al bot", group_id)
                return {"status": "ok"}
            # Clean the text
            text = text.replace("@Tesorero", "").strip()

        # Detectar si el usuario respondió a un mensaje específico (reply nativo de WhatsApp)
        replied_to_id: str | None = message.get("context", {}).get("id")
        if replied_to_id:
            logger.info("Reply detectado de %s → wamid referenciado: %s", phone, replied_to_id)

    except (KeyError, IndexError) as e:
        logger.warning("Payload inválido: %s", e)
        return {"status": "ok"}

    # Verificar whitelist (si está configurada)
    if settings.ALLOWED_PHONE_NUMBERS and phone not in settings.ALLOWED_PHONE_NUMBERS:
        logger.warning("Mensaje de número no autorizado: %s", phone)
        return {"status": "ok"}

    if is_audio:
        logger.info("Mensaje de audio recibido de %s: media_id %s", phone, media_id)
    elif is_image:
        logger.info("Mensaje de imagen recibido de %s: media_id %s", phone, media_id)
    else:
        logger.info("Mensaje recibido de %s: %s", phone, text)

    # Encolar procesamiento en background
    background_tasks.add_task(
        _process_message_background, 
        phone, 
        text, 
        replied_to_id, 
        msg_type, 
        media_id
    )

    # Meta requiere siempre 200
    return {"status": "ok"}
