# Software Design Document (SDD) & TDD Specs

**Objetivo del Documento:** Especificaciones técnicas para la implementación de las nuevas *features*, enfocadas en guiar el desarrollo guiado por pruebas (TDD) mediante agentes de código.

## 1. Arquitectura y Stack
* **Infraestructura:** Todo el entorno (API, Base de Datos, Workers) correrá orquestado mediante `docker-compose`.
* **LLM Engine:** DeepSeek (consumido vía API).
* **Enfoque de Testing:** Se definen los casos de prueba (Test Cases) de alto nivel. El agente de consola deberá implementar los tests (unitarios y de integración) verificando estas condiciones antes de escribir la lógica de negocio.

## 2. Trade-off de Base de Datos: PostgreSQL vs. MySQL
* **Veredicto para este MVP:** **PostgreSQL**. 
* **Justificación:** La flexibilidad del formato `JSONB` de Postgres es superior a la implementación JSON de MySQL. Esto es crítico para guardar dinámicamente el estado del contexto conversacional, los metadatos y los prompts inyectados de DeepSeek sin tener que hacer migraciones de esquema constantemente. Además, maneja mejor la concurrencia (MVCC) ante ráfagas de mensajes simultáneos en grupos de WhatsApp.

## 3. Especificaciones para TDD (Requisitos para el Agente)

El agente de consola debe generar los tests asumiendo la siguiente lógica:

### Módulo A: Filtro de Webhooks (Grupos vs. Privados)
* **Test 1 (Privado):** Simular un payload de WhatsApp de un chat privado (sin `@`). Afirmar (`assert`) que el evento pasa a la cola de procesamiento del LLM.
* **Test 2 (Grupo - Ignorado):** Simular un payload de un chat grupal sin arrobar al bot. Afirmar que el evento es descartado inmediatamente (retorna 200 OK a WhatsApp pero no llama a DeepSeek).
* **Test 3 (Grupo - Procesado):** Simular un payload de un chat grupal incluyendo `@Tesorero`. Afirmar que el evento es extraído (limpiando el `@Tesorero` del string) y pasa a la cola de procesamiento.

### Módulo B: Generación y Almacenamiento de Personalidad
* **Test 1 (Generación de Prompt):** Simular la respuesta del usuario al onboarding (*"Quiero que seas muy agresivo"*). Afirmar que se ejecuta la llamada mockeada a DeepSeek para generar el System Prompt.
* **Test 2 (Persistencia):** Afirmar que el string resultante se guarda en la base de datos (ej. tabla `chat_configurations` bajo la columna `custom_prompt`).
* **Test 3 (Inyección de Contexto):** Simular un mensaje normal de registro de gasto. Afirmar que el payload enviado a DeepSeek concatena correctamente el `custom_prompt` almacenado junto con el mensaje del usuario.

### Módulo C: Máquina de Estados del Objetivo
* **Test 1 (Suma de progreso):** Dado un grupo con objetivo de $100.000 y progreso actual de $50.000. Simular un mensaje de ahorro de $10.000. Afirmar que la base de datos actualiza el progreso a $60.000.
* **Test 2 (Trigger de Meta Alcanzada):** Simular un registro de gasto/ahorro que iguala o supera el monto del objetivo. Afirmar que el sistema emite el evento `GoalReached`.
* **Test 3 (Respuesta de Cierre):** Al capturar el evento `GoalReached`, afirmar que el payload de respuesta incluye el texto ofreciendo crear un nuevo objetivo y la invitación al chat privado.

### Módulo D: Control de Límites (Paywall)
* **Test 1 (Límite de Integrantes):** Intentar registrar un 5to integrante en un grupo del plan gratuito. Afirmar que la operación falla y lanza una excepción manejada `MemberLimitExceeded`.
* **Test 2 (Límite de Grupos):** Dado un usuario admin Free que ya tiene 1 grupo, intentar crear un segundo grupo. Afirmar que lanza excepción `GroupLimitExceeded`.
* **Test 3 (Bloqueo de Media):** Simular un payload de WhatsApp con tipo `audio` o `image`. Afirmar que la petición se rechaza sin procesar en el LLM y devuelve el string de upsell predefinido.