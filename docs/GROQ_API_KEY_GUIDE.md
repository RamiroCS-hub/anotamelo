# 🔑 Cómo obtener tu API Key de Groq

Groq ofrece un motor de inferencia de inteligencia artificial extremadamente rápido (LPU), ideal para tareas que requieren muy baja latencia, como la transcripción de audios de WhatsApp (Voice-to-Text).

Sigue estos pasos para obtener tu clave:

## Pasos

1. **Crear una cuenta en GroqCloud:**
   * Ve a [console.groq.com](https://console.groq.com/).
   * Regístrate o inicia sesión usando tu cuenta de Google o GitHub.

2. **Acceder a las API Keys:**
   * Una vez en la consola, en el panel lateral izquierdo, haz clic en **"API Keys"**.
   * Haz clic en el botón superior derecho que dice **"Create API Key"**.

3. **Generar y copiar la clave:**
   * Asígnale un nombre descriptivo a tu clave (por ejemplo: `finance_wpp_bot`).
   * Haz clic en "Submit" o "Create".
   * **⚠️ IMPORTANTE:** Copia la clave alfanumérica que aparece en pantalla inmediatamente. Por razones de seguridad, Groq no volverá a mostrártela. Si la pierdes, tendrás que crear una nueva.

4. **Configurar el proyecto:**
   * Abre tu archivo `.env` en la raíz del proyecto.
   * Pega la clave copiada en la variable `GROQ_API_KEY`:
     ```env
     GROQ_API_KEY=gsk_tu_clave_super_secreta_aqui
     TRANSCRIPTION_MODEL=whisper-large-v3-turbo
     ```

¡Listo! Con esto tu bot ya estará listo para transcribir audios a velocidad ultra-rápida.