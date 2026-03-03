# Tasks: Voice-to-Text (Audio Processing)

## Phase 1: Configuration & Foundation

- [x] 1.1 Add `GROQ_API_KEY` and `TRANSCRIPTION_MODEL` to the `Settings` class in `app/config.py`.
- [x] 1.2 Document the new configuration variables (`GROQ_API_KEY`, `TRANSCRIPTION_MODEL`) in `.env.example`.

## Phase 2: Transcription Service (TDD)

- [x] 2.1 **Test**: Create `tests/test_transcription.py` and write a failing test for `transcribe_audio`. Mock `httpx.AsyncClient` to simulate a successful JSON response with transcribed text from the Groq Whisper API.
- [x] 2.2 **Implement**: Create `app/services/transcription.py` and implement the `transcribe_audio(audio_data: bytes) -> str` function using `httpx` and `config.settings.GROQ_API_KEY` to make the test pass. Ensure it supports `.ogg` Opus files.

## Phase 3: WhatsApp Service Enhancements (TDD)

- [x] 3.1 **Test**: Create `tests/test_whatsapp.py` and write a failing test for `download_media(media_id)`. Mock `httpx.AsyncClient` to simulate fetching the URL from the Meta Graph API and then downloading the binary data.
- [x] 3.2 **Implement**: Update `app/services/whatsapp.py` to add `download_media(media_id: str) -> bytes`. Implement the two-step HTTP request logic (first getting the URL, then downloading the binary using `config.settings.WHATSAPP_TOKEN`) to make the test pass.

## Phase 4: Webhook Integration (TDD)

- [x] 4.1 **Test**: Create `tests/test_webhook.py` and write failing tests:
  - Verify the webhook endpoint instantly returns a `200 OK` and enqueues a `BackgroundTask`.
  - Verify that when `msg_type == "audio"`, the background task correctly orchestrates calling `whatsapp.send_text("🎧 Escuchando audio...")`, `whatsapp.download_media(media_id)`, `transcription.transcribe_audio(audio_bytes)`, and finally `_agent.process(phone, text)`. Use mocks for all external services.
- [x] 4.2 **Implement**: Refactor `app/api/webhook.py`. Inject `BackgroundTasks` into the route endpoint, move the existing synchronous processing logic into an async function `_process_message_background(payload: dict)`, and add the new `audio` message type logic to make the tests pass. Ensure the early return for `msg_type == "audio"` is removed.

## Phase 5: Verification & Cleanup

- [ ] 5.1 Run the full test suite (`pytest`) to verify no regressions were introduced to the text message handling.
- [ ] 5.2 Validate end-to-end integration by triggering a simulated payload with an `audio` message type to the webhook route to ensure the background task processes correctly.
