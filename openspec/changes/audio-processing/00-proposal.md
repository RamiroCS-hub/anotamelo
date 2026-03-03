# Proposal: Voice-to-Text (Audio Processing)

## Intent

Enable the WhatsApp bot to receive, understand, and process voice notes sent by users. Currently, the bot explicitly ignores non-text messages. By adding audio transcription (Voice-to-Text), users can quickly log expenses or ask questions via voice notes, improving accessibility and user experience without changing the core LLM processing logic.

## Scope

### In Scope
- Modify the WhatsApp webhook to accept messages of type `audio`.
- Retrieve the media URL from the Meta Graph API using the provided `media_id`.
- Download the audio file securely using the existing WhatsApp authentication token.
- Transcribe the downloaded audio (typically `.ogg` Opus format) to text using an external API (e.g., Groq or OpenAI Whisper API via `httpx`).
- Inject the transcribed text into the existing agent workflow (`_agent.process`).

### Out of Scope
- Voice synthesis (Text-to-Speech) for bot replies (the bot will still reply with text).
- Processing other media types (video, images, documents).
- Local, on-device transcription models (e.g., local Whisper via `transformers` or `ffmpeg` dependencies) to keep the deployment lightweight.

## Approach

1. **Webhook Update**: In `app/api/webhook.py`, remove the early return for `msg_type == "audio"` and extract the `media_id` from the payload.
2. **Media Download**: Add a `download_media(media_id: str)` function in `app/services/whatsapp.py` that hits the Meta Graph API `/{media_id}` to get the URL, then downloads the binary data.
3. **Transcription Service**: Create a new service (e.g., `app/services/audio.py`) with a `transcribe_audio(audio_data: bytes)` function. This function will use the `httpx` client (already in `requirements.txt`) to send the binary data to a Whisper-compatible API (like Groq or OpenAI) for fast transcription.
4. **Integration**: In the webhook, if the message is audio, download it, transcribe it, and pass the resulting text string to `_agent.process(phone, transcribed_text)`.
5. **Configuration**: Add necessary environment variables (e.g., `TRANSCRIPTION_API_KEY`, `TRANSCRIPTION_PROVIDER_URL`) to `app/config.py` and `.env.example`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/api/webhook.py` | Modified | Add logic to handle `msg_type == "audio"` and trigger transcription. |
| `app/services/whatsapp.py` | Modified | Add Meta Graph API media download integration. |
| `app/services/audio.py` | New | Service to handle HTTP requests to the Whisper-compatible transcription API. |
| `app/config.py` | Modified | Add configuration for the transcription API credentials. |
| `.env.example` | Modified | Document the new transcription environment variables. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| **Webhook Timeout** | Medium | Meta expects a webhook response within 15 seconds. Downloading audio + transcribing + LLM processing might exceed this. **Mitigation**: Use a very fast transcription provider (e.g., Groq Whisper) and ensure HTTP timeouts are configured. In the future, processing should be moved to a background task (`BackgroundTasks` in FastAPI). |
| **Audio Format Incompatibility** | Low | WhatsApp audio is usually OGG/Opus. Some APIs might reject it. **Mitigation**: The standard OpenAI Whisper API and Groq support `.ogg` out of the box. Verify API documentation before implementation. |

## Rollback Plan

Revert the changes in `app/api/webhook.py` to restore the condition that ignores `msg_type != "text"`. Remove the new transcription environment variables from the deployment configuration to prevent unauthorized API usage.

## Dependencies

- **Meta Graph API**: Access to download media (requires the existing `WHATSAPP_TOKEN`).
- **Transcription API**: An external service (Groq or OpenAI) that supports Whisper and accepts `.ogg` files. Requires a new API Key.
- No new Python packages are strictly necessary since `httpx` is already used for HTTP requests.

## Success Criteria

- [ ] A user sends a voice note to the WhatsApp bot.
- [ ] The bot successfully downloads the media from Meta.
- [ ] The audio is transcribed to text accurately.
- [ ] The bot replies with a text message corresponding to the user's spoken intent (e.g., successfully categorizing an expense).
- [ ] The webhook returns a 200 OK within the Meta timeout window.