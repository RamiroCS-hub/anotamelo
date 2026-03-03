# Product Requirements Document (PRD)

**Producto:** El Tesorero Tóxico (Módulo de Grupos y Objetivos)
**Objetivo del Documento:** Definir el comportamiento, límites y flujos de las nuevas funcionalidades para la gestión de gastos grupales gamificados.

## 1. Funcionalidad: Dinámica de Interacción (Privado vs. Grupo)
El bot debe distinguir el contexto de la conversación para optimizar el consumo de la API y respetar la privacidad.
* **Chat Privado:** Procesa e interpreta el 100% de los mensajes de texto recibidos.
* **Chat Grupal:** Ignora todo el tráfico del grupo por defecto. El webhook solo debe gatillar el procesamiento del LLM si el mensaje incluye la mención directa al bot (ej: `@Tesorero`).

## 2. Funcionalidad: Definición de Personalidad Dinámica
El tono del bot no es estático; se adapta a la tolerancia del usuario o del grupo.
* **Flujo de Onboarding:** En la primera interacción, el bot hace una pregunta para medir el nivel de sarcasmo deseado (ej: *"¿Querés que sea un contador aburrido o que te insulte cada vez que gastás en delivery?"*).
* **Generación de Prompt:** En base a la respuesta, el bot usa DeepSeek para redactar un "System Prompt" detallado y específico.
* **Almacenamiento:** Ese prompt generado se guarda en la base de datos asociado al `chat_id` (sea usuario individual o grupo) y se inyecta como contexto en todas las futuras llamadas al LLM para esa entidad.

## 3. Funcionalidad: Gestión de Objetivos Grupales
El motor del grupo es la meta financiera.
* **Creación:** El administrador del grupo arroba al bot para definir el objetivo (monto, moneda y propósito).
* **Seguimiento:** El bot lleva el progreso actualizado en cada nuevo registro de gasto o ahorro.
* **Cierre de Ciclo:** Al alcanzar la meta, el bot emite un mensaje de felicitación (con su tono respectivo), ofrece iniciar una nueva meta para el grupo, y añade un *Call to Action* recordando a los integrantes que pueden abrirle chat privado para recibir asesoramiento financiero personal.

## 4. Modelo Freemium y Límites (Paywall)
La versión gratuita actuará como un embudo de adquisición hacia la versión de pago.
* **Límites del Plan Gratuito:**
    * Máximo 1 grupo activo por usuario administrador.
    * Máximo 4 integrantes por grupo (incluyendo al bot).
    * Procesamiento exclusivo de texto (bloqueo y mensaje de error amigable si envían audios o imágenes de tickets).
* **Upsell:** Si un usuario intenta agregar un quinto integrante, procesar un audio o crear un segundo grupo, el bot responde explicando el límite y ofreciendo el plan Premium.