# Implementation Progress: Webhook Hardening and Privacy Controls

## Estado

- Fecha: 2026-03-23
- Resultado: implementación aplicada

## Cambios realizados

- Extendí [app/config.py](/Users/rcarnicer/Desktop/anotamelo/app/config.py) y [.env.example](/Users/rcarnicer/Desktop/anotamelo/.env.example) con policy explícita de firma y límites de media.
- Endurecí [app/api/webhook.py](/Users/rcarnicer/Desktop/anotamelo/app/api/webhook.py) para requerir firma por defecto, aceptar bypass local solo por flag, sanitizar logs y rechazar media fuera de policy antes del procesamiento pesado.
- Separé metadata y descarga en [app/services/whatsapp.py](/Users/rcarnicer/Desktop/anotamelo/app/services/whatsapp.py) para poder hacer preflight por MIME/tamaño.
- Reduje exposición de cuerpos remotos en [app/services/llm_provider.py](/Users/rcarnicer/Desktop/anotamelo/app/services/llm_provider.py).
- Bloqueé persistencia grupal no verificable en [app/services/personality.py](/Users/rcarnicer/Desktop/anotamelo/app/services/personality.py) y devolví feedback explícito en [app/agent/skills.py](/Users/rcarnicer/Desktop/anotamelo/app/agent/skills.py).
- Actualicé la cobertura en [tests/test_webhook.py](/Users/rcarnicer/Desktop/anotamelo/tests/test_webhook.py), [tests/test_whatsapp.py](/Users/rcarnicer/Desktop/anotamelo/tests/test_whatsapp.py), [tests/test_personality.py](/Users/rcarnicer/Desktop/anotamelo/tests/test_personality.py) y [tests/test_llm_provider.py](/Users/rcarnicer/Desktop/anotamelo/tests/test_llm_provider.py).

## Notas

- El webhook ya no entra en modo inseguro por simple ausencia de `WHATSAPP_APP_SECRET`.
- La persistencia de reglas compartidas en grupos quedó deshabilitada hasta contar con una autoridad verificable.
- La carga existente de `custom_prompt` grupal no se migró ni se purgó en esta iteración.
