# Tasks: New Architecture and Features

## Phase 1: Infrastructure & Foundation

- [x] 1.1 Create `docker-compose.yml` with `api` and `db` (PostgreSQL 16) services.
- [x] 1.2 Create `Dockerfile` for the FastAPI application.
- [x] 1.3 Add `sqlalchemy`, `asyncpg`, and `alembic` to `requirements.txt`.
- [x] 1.4 Initialize Alembic by creating `alembic.ini` and the `alembic/` directory.
- [x] 1.5 Create `app/core/db.py` to set up the asynchronous SQLAlchemy PostgreSQL engine and session maker.
- [x] 1.6 Create `app/models/base.py` for the SQLAlchemy declarative base.
- [x] 1.7 Create `app/models/user.py` with `User` model (identified by `whatsapp_number`).
- [x] 1.8 Create `app/models/group.py` with `Group` model (identified by `whatsapp_group_id`).
- [x] 1.9 Create `app/models/group_member.py` with `GroupMember` association model.
- [x] 1.10 Create `app/models/chat_config.py` with `ChatConfig` model (`entity_id`, `custom_prompt`, `plan_type`).
- [x] 1.11 Create `app/models/goal.py` with `Goal` model (`group_id` or `user_id`, `target_amount`, `current_progress`, `status`).
- [x] 1.12 Generate and apply the initial Alembic migration for the new models.
- [x] 1.13 Create `app/services/user_service.py` to implement passwordless user creation, identifying and auto-registering users by their `whatsapp_number` when a message is received.

## Phase 2: Módulo D - Control de Límites (Paywall) (TDD)

- [x] 2.1 Write failing tests in `tests/test_paywall.py` for member limit, group limit, and media block (Módulo D).
- [x] 2.2 Create `app/services/paywall.py` and implement limit checking to raise `MemberLimitExceeded` for >4 members in FREE plan, passing the first test.
- [x] 2.3 Implement limit checking in `app/services/paywall.py` to raise `GroupLimitExceeded` if a FREE admin already has 1 group, passing the second test.
- [x] 2.4 Update paywall service to reject payloads with `audio` or `image` type by raising `MediaNotAllowed`, passing the media block test.

## Phase 3: Módulo A - Filtro de Webhooks (TDD)

- [x] 3.1 Write failing tests in `tests/test_webhook.py` for private chat processing, group chat ignore, and group chat process (Módulo A).
- [x] 3.2 Update `app/api/webhook.py` to process private chats (no `@`) and enqueue them to BackgroundTasks, passing the private chat test.
- [x] 3.3 Update `app/api/webhook.py` to immediately return 200 OK without processing if a group chat payload lacks `@Tesorero`, passing the ignore test.
- [x] 3.4 Update `app/api/webhook.py` to extract the message (stripping `@Tesorero`) from a group chat payload and enqueue it, passing the group process test.

## Phase 4: Módulo B - Personalidad (TDD)

- [x] 4.1 Write failing tests in `tests/test_personality.py` for prompt generation, DB persistence, and context injection (Módulo B).
- [x] 4.2 Create/update `app/services/llm.py` to implement prompt generation via a mocked DeepSeek call, passing the generation test.
- [x] 4.3 Update `app/services/llm.py` to save the generated system prompt into the `chat_configurations` table (`custom_prompt` column), passing the persistence test.
- [x] 4.4 Update `app/services/llm.py` to fetch `custom_prompt` from the database and concatenate it with the user message before sending to DeepSeek, passing the injection test.

## Phase 5: Módulo C - Máquina de Estados del Objetivo (TDD)

- [x] 5.1 Write failing tests in `tests/test_goals.py` for progress sum, target reach trigger, and closing response payload (Módulo C).
- [x] 5.2 Create `app/services/goals.py` and implement progress update logic (adding the saved amount to `current_progress`), passing the sum test.
- [x] 5.3 Update `app/services/goals.py` to emit a `GoalReached` event/status when `current_progress >= target_amount`, passing the trigger test.
- [x] 5.4 Update `app/services/goals.py` (or caller) to include the closing text and private chat invitation in the response payload upon `GoalReached`, passing the closure test.

## Phase 6: MVP Integration

- [x] 6.1 Wire up the newly created services (`paywall.py`, `goals.py`, `user_service.py`) directly into the existing `app/api/webhook.py` BackgroundTasks flow.
- [x] 6.2 Integrate the services within the `AgentLoop` to handle LLM processing and database updates asynchronously.
- [x] 6.3 Write end-to-end integration tests in `tests/test_integration.py` to verify the flow from webhook to BackgroundTasks to database update.

## Phase 7: Cross-Context AI Tools

- [x] 7.1 Create `app/tools/user_groups.py` and implement the `get_user_groups_info` tool to query a user's group affiliations and the associated goals/status.
- [x] 7.2 Register the `get_user_groups_info` tool in the DeepSeek/LLM pipeline specifically for requests originating from a user's private chat.
- [x] 7.3 Write integration tests in `tests/test_tools.py` to verify a user can check group goal status from their private chat.
