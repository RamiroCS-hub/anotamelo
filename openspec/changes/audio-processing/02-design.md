# Design: Voice-to-Text (Audio Processing)

## Technical Approach

Refactor the FastAPI webhook to accept messages and immediately delegate processing to `fastapi.BackgroundTasks`. This avoids Meta's 15-second webhook timeout and prevents blocking. For audio messages, download the binary file via Meta's Graph API, send it to the Groq/OpenAI Whisper API using `httpx`, and finally pass the transcribed text to the existing `AgentLoop` for normal processing.

## Architecture Decisions

### Decision: Webhook Asynchronous Processing
**Choice**: Use FastAPI's native `BackgroundTasks`.
**Alternatives considered**: Celery + Redis, RQ, `asyncio.create_task`.
**Rationale**: Keeps the architecture simple and avoids new infrastructure dependencies. It ensures the webhook returns a 200 OK instantly to Meta, satisfying the architectural requirement without over-engineering.

### Decision: Media Download
**Choice**: Fetch media URL via Meta Graph API and download binary data using `httpx`.
**Alternatives considered**: Passing the Meta URL directly to the transcription provider.
**Rationale**: Meta's media URLs are secured and require the `WHATSAPP_TOKEN` Authorization header to download. The bot must download the file itself into memory before passing it to the external API.

### Decision: Transcription Service
**Choice**: Groq Whisper API (`whisper-large-v3-turbo`) via a new `app/services/transcription.py` module using `httpx`.
**Alternatives considered**: Local Whisper inference (via `transformers`), Google Cloud Speech-to-Text.
**Rationale**: Using an external API avoids heavy local ML dependencies (e.g., PyTorch, ffmpeg). Groq provides extremely fast inference and natively supports the `.ogg` Opus files sent by WhatsApp.

### Decision: Proactive Feedback
**Choice**: Send "🎧 Escuchando audio..." immediately when processing an audio message.
**Alternatives considered**: Wait for the final LLM response without intermediate feedback.
**Rationale**: Downloading, transcribing, and running the `AgentLoop` can take several seconds. Providing immediate feedback improves user experience and confirms the bot received the audio.

## Data Flow

```text
WhatsApp ──→ Webhook (POST) ──→ Returns 200 OK instantly
                  │
           BackgroundTask
                  │
            [Is it Audio?] 
            /            \
          No             Yes
          |               │
          |               ├──→ whatsapp.send_text("🎧 Escuchando audio...")
          |               │
          |               ├──→ whatsapp.download_media(media_id)
          |               │
          |               └──→ transcription.transcribe_audio(audio_bytes)
          |               │
          \______   ______/
                 \ /
                  V
        _agent.process(phone, text)
                  │
        whatsapp.send_text(phone, reply)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/api/webhook.py` | Modify | Inject `BackgroundTasks` in the endpoint. Move processing logic to a new async function `_process_message_background`. Add logic to handle `msg_type == "audio"`. |
| `app/services/whatsapp.py` | Modify | Add `download_media(media_id: str) -> bytes` making two HTTP requests (one for the URL, one for the file binary). |
| `app/services/transcription.py` | Create | New service containing `transcribe_audio(audio_data: bytes) -> str` that calls the Whisper API. |
| `app/config.py` | Modify | Add `GROQ_API_KEY` and `TRANSCRIPTION_MODEL` to the `Settings` class. |
| `.env.example` | Modify | Document the new configuration variables. |

## Interfaces / Contracts

```python
# app/services/whatsapp.py
async def download_media(media_id: str) -> bytes:
    """Fetches media URL from Graph API and downloads the binary payload."""
    pass

# app/services/transcription.py
async def transcribe_audio(audio_data: bytes) -> str:
    """Sends the audio bytes to the Whisper API and returns the transcribed text."""
    pass
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Media Download | Mock `httpx.AsyncClient` in `whatsapp.py` to return a fake URL and fake binary data, validating the headers. |
| Unit | Transcription | Mock `httpx.AsyncClient` in `transcription.py` to return a JSON response with the transcribed text. |
| Integration | Webhook Route | Send a fake webhook payload with `type="audio"` and assert that a `BackgroundTask` is enqueued and 200 OK is returned. |

## Migration / Rollout

No data migration required. The deployment environment must be updated to include the new `GROQ_API_KEY` environment variable before releasing this change.

## Open Questions

- None.
