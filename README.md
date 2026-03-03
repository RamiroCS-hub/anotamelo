# Bot de Gastos por WhatsApp (Setup mínimo)

Bot en FastAPI que recibe mensajes de WhatsApp por webhook, interpreta gastos con un LLM y los guarda en Google Sheets.

## Requisitos

- Python 3.11+
- Cuenta de Meta WhatsApp Cloud API
- API key de LLM (Gemini o DeepSeek/OpenRouter)
- Google Service Account + Spreadsheet compartido

## Setup mínimo

1. Crear entorno e instalar dependencias:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Crear `.env` desde ejemplo:

```bash
cp .env.example .env
```

3. Completar en `.env` estas variables mínimas:

```env
# WhatsApp
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=mi_token_secreto

# Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/service_account.json
GOOGLE_SPREADSHEET_ID=

# LLM
LLM_PROVIDER=gemini
GEMINI_API_KEY=
```

4. Guardar credenciales de Google en:

```text
credentials/service_account.json
```

5. Ejecutar la app:

```bash
uvicorn app.main:app --reload --port 8000
```

## Webhook

- Verificación: `GET /webhook`
- Recepción de mensajes: `POST /webhook`

En Meta, configurar el callback como:

```text
https://tu-dominio.com/webhook
```

Si probás local, podés exponerlo con ngrok y usar su URL pública.

## Notas rápidas

- Si falla Google Sheets, la app inicia igual pero no guarda gastos.
- `ALLOWED_PHONE_NUMBERS` en `.env` permite limitar qué números pueden usar el bot.
- Para guía completa, ver `SETUP.md`.
