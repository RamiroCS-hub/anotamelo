# Proposal: Automatización de Gastos Recurrentes

## 1. Intent (El "Qué" y el "Por qué")
**Qué:** Agregar la capacidad al agente de programar, gestionar y ejecutar gastos de forma recurrente automáticamente (ej: alquiler, Netflix, servicios).
**Por qué:** Los usuarios realizan pagos fijos periódicamente. Tener que recordarle al bot que anote un pago todos los meses causa fricción. El bot debe ser lo suficientemente inteligente para crear estos "cronjobs" desde lenguaje natural y ejecutarlos por su cuenta.

## 2. Scope (El Alcance)

**In Scope:**
* Añadir una nueva tool `schedule_recurring_expense` que el agente puede llamar para programar el gasto (monto, descripción, categoría, frecuencia).
* Añadir una nueva tool `get_recurring_expenses` para que el agente pueda consultar los gastos recurrentes activos de un usuario y cancelarlos/modificarlos si este lo pide.
* Un Scheduler interno (ej. `APScheduler` o `asyncio` task) que corra en background, verifique las tareas programadas y registre automáticamente los gastos en Google Sheets.
* El bot debe notificar al usuario por WhatsApp cuando ejecuta un gasto automático ("*He registrado tu gasto recurrente de $10.000 de Netflix.*").

**Out of Scope:**
* Modificar la base de datos de Google Sheets; los gastos recurrentes deben guardarse en un almacenamiento propio del bot (ej. base de datos transaccional o JSON local/Redis) y empujar los registros como gastos normales a Sheets.

## 3. Approach (El Enfoque Técnico)

1. **Persistencia:** Crear un repositorio para gastos recurrentes en la base de datos del bot (PostgreSQL según la nueva arquitectura propuesta).
2. **Nuevas Tools:**
   * `schedule_recurring_expense(amount, description, category, cron_expression)`: El agente entiende el pedido del usuario y genera un patrón.
   * `get_recurring_expenses()`: Devuelve la lista actual.
3. **Mecanismo de Ejecución:** Un Worker interno que evalúe periódicamente la base de datos de "recurring_expenses" y, si toca, use `SheetsService` para registrar el gasto y `whatsapp.send_text` para avisar al usuario.