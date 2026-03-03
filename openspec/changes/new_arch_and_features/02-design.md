# Design: New Architecture and Features

## Technical Approach

El objetivo es migrar la aplicación actual a una arquitectura basada en contenedores (`docker-compose`) con PostgreSQL como base de datos principal, e introducir una serie de funcionalidades clave: un filtro avanzado de webhooks para manejar chats grupales vs. privados, un sistema de personalización de *prompts* del LLM (DeepSeek), una máquina de estados para el seguimiento de objetivos financieros, y un sistema de control de límites (Paywall) para el plan gratuito. 

La ejecución de tareas pesadas (como llamadas al LLM) se desacoplará utilizando `FastAPI BackgroundTasks` para el MVP. Esta solución permite la ejecución asíncrona sin la sobrecarga inicial de mantener infraestructura adicional como Redis y workers separados (Celery/ARQ), evitando la sobreingeniería en esta etapa.

### Identity & Context
- **Passwordless User Creation**: Los usuarios se crean e identifican puramente por su número de WhatsApp. No hay uso de contraseñas.
- **Goals Ownership**: Los objetivos (Goals) pertenecen al contexto de la entidad en la que se crean. Si se crea dentro de un grupo, el Goal pertenece a ese Grupo. Si se crea en un chat privado, pertenece al Usuario.

### AI Tools
- **Cross-Context Tools**: Se incorpora una nueva herramienta (`get_user_groups_info`) que permite a un usuario, desde su chat PRIVADO, consultar los objetivos y el estado de los grupos a los que pertenece.

## Architecture Decisions

### Decision: Orquestación de Infraestructura

**Choice**: Docker Compose con servicios: `api` (FastAPI) y `db` (PostgreSQL). (Redis y Worker no requeridos para el MVP).
**Alternatives considered**: Despliegue manual, serverless, o mantener estado en memoria/Google Sheets.
**Rationale**: Docker Compose asegura paridad entre entornos de desarrollo y producción. Para el MVP, `FastAPI BackgroundTasks` es suficiente para desacoplar el procesamiento asíncrono sin agregar sobreingeniería de colas externas y workers separados.

### Decision: Base de Datos Principal

**Choice**: PostgreSQL 16.
**Alternatives considered**: MySQL, MongoDB.
**Rationale**: Siguiendo el requerimiento explícito, la flexibilidad del formato `JSONB` de Postgres es superior a la implementación de MySQL, permitiendo guardar dinámicamente el estado conversacional y los prompts de DeepSeek sin migraciones constantes. Además, su MVCC maneja óptimamente la concurrencia ante ráfagas de mensajes en grupos.

### Decision: Librería ORM

**Choice**: SQLAlchemy 2.0 con `asyncpg`.
**Alternatives considered**: Prisma, TortoiseORM, o SQL crudo.
**Rationale**: SQLAlchemy 2.0 ofrece un soporte asíncrono robusto e integración directa con las anotaciones de tipos de Python, siendo un estándar maduro y alineado con FastAPI.

## Data Flow

### Flujo de Webhook y Procesamiento

```text
    Meta WA API ──→ [ API Webhook Filter ]
                          │
          (Falla o Ignora)├─────→ [ Rechazo Inmediato (Ej. Grupo sin @ o Audio bloqueado) ]
                          │
                          ↓
                  [ FastAPI BackgroundTasks ]
                          │
                          ↓
                [ AgentLoop (Async) ]
                          │
         ┌────────────────┴───────────────┐
         ↓                                ↓
[ DB: Validación Plan ]            [ DB: Fetch Personality ]
 (Límites de Grupos/Miembros)      (Tabla chat_configurations)
         │                                │
         └──────────────┬─────────────────┘
                        ↓
                 [ DeepSeek API ]
                        │
                        ↓
           [ Máquina de Estados (Goal) ] ──→ [ DB: Update Progreso ]
                        │
                        ├─────→ (Si Goal >= Target) ──→ [ Evento: GoalReached ]
                        │
                        ↓
                [ WA Send Message ]
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `docker-compose.yml` | Create | Define los servicios `api` y `db`. |
| `Dockerfile` | Create | Empaquetado de la aplicación FastAPI. |
| `requirements.txt` | Modify | Agregar `sqlalchemy`, `asyncpg`, `alembic`. |
| `alembic.ini` | Create | Configuración de migraciones de base de datos. |
| `app/core/db.py` | Create | Configuración de la conexión asíncrona a PostgreSQL. |
| `app/models/` | Create | Modelos SQLAlchemy: `User`, `Group`, `GroupMember`, `ChatConfig`, `Goal`. |
| `app/api/webhook.py` | Modify | Lógica Módulo A y D (filtrado de grupos sin `@`, bloqueo de audios, ejecución vía BackgroundTasks). |
| `app/services/llm.py` | Modify | Lógica Módulo B (inyección de `custom_prompt` desde DB). |
| `app/services/goals.py` | Create | Lógica Módulo C (actualización de métricas, trigger de `GoalReached`). |
| `app/services/billing.py` | Create | Lógica Módulo D (validación de límites de miembros y grupos). |
| `app/tools/user_groups.py` | Create | Lógica Cross-Context: herramienta `get_user_groups_info` para consultar objetivos de grupo en privado. |

## Interfaces / Contracts

### DB Schema (Aproximación inicial en SQLAlchemy)

```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    whatsapp_number: Mapped[str] = mapped_column(unique=True, index=True)

class Group(Base):
    __tablename__ = "groups"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    whatsapp_group_id: Mapped[str] = mapped_column(unique=True, index=True)

class GroupMember(Base):
    __tablename__ = "group_members"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id"), primary_key=True)

class ChatConfig(Base):
    __tablename__ = "chat_configurations"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    entity_id: Mapped[str] = mapped_column(unique=True) # Phone o Group ID
    custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_type: Mapped[str] = mapped_column(default="FREE") # FREE, PRO

class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    group_id: Mapped[UUID | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    target_amount: Mapped[float]
    current_progress: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(default="ACTIVE") # ACTIVE, REACHED
```

## Testing Strategy

Como se especifica en TDD, todos los tests deben implementarse antes de la lógica de negocio.

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit / API | **Módulo A**: Webhook Filter | Mockear payload de Meta en `test_webhook.py`. Validar que grupos sin `@` retornen 200 sin encolar, y que audios en plan Free sean bloqueados con el mensaje de upsell. |
| Integration | **Módulo B**: Personality | Insertar config en DB Test. Mockear API de DeepSeek para validar que el prompt generado se persista, y que en consultas posteriores, el prompt inyectado concatene el DB state. |
| Integration | **Módulo C**: Goal State | Insertar un Goal activo. Procesar un mensaje simulado que incremente el saldo. Validar que el valor en DB aumente, y que si supera el `target_amount`, cambie el estado y se genere el texto de cierre. |
| Unit / Service | **Módulo D**: Paywall Limits | Llamar a `billing.add_member_to_group()` y verificar que lance `MemberLimitExceeded` si > 4 en plan Free. Probar análogamente `GroupLimitExceeded`. |

## Migration / Rollout

1. **Infraestructura**: Desplegar `docker-compose` con la nueva base de datos vacía (PostgreSQL).
2. **Migración de Datos**: Si la instancia actual guarda datos en `Gspread` (como sugiere el `requirements.txt`), se deberá desarrollar un script ad-hoc de migración ETL para poblar Postgres con los usuarios y balances existentes.
3. **Rollout**: Desplegar API. Actualizar el endpoint del Webhook en Meta Developers para apuntar a la nueva instancia una vez estabilizado.

## Open Questions

- [ ] ¿Cómo se identificará unívocamente un grupo en el payload del Webhook de Meta (para extraer el ID o determinar el tipo)? (Meta usa WAMIDs pero la estructura de grupos depende de la API usada, ej. Cloud API vs WA Business API o un proveedor no oficial).
- [ ] ¿Los audios transcritos con OpenAI/Local Whisper tendrán límite de duración en el plan Free, o estarán totalmente bloqueados? (El spec sugiere bloqueo total del *media* en Free).