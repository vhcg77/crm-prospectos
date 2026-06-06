---
name: ai-integration
description: Cómo integrar la API de Claude (Anthropic) en el CRM de forma segura y aislada. Cargar al implementar las features de IA de Fase 2 (sugerir siguiente paso, redactar email) o al tocar ai_client.py.
---

# Skill: Integración con Claude

## Regla central

**Toda interacción con Claude pasa por `ai_client.py`.** Ninguna ruta, template ni
servicio llama a la API de Anthropic directamente. Esto permite cambiar el origen de
la key (local → proxy en Cloud Run) modificando un solo archivo.

## Diseño de `ai_client.py`

Expón funciones de dominio de alto nivel, NO un cliente genérico:

```python
def sugerir_siguiente_paso(prospecto: dict) -> str: ...
def redactar_email(prospecto: dict, objetivo: str) -> str: ...
```

Internamente, ambas usan una función privada única `_llamar_claude(system, user)`
que es el ÚNICO lugar donde se decide:

- de dónde sale la key (config local en Fase 2; proxy en Fase 3),
- el modelo,
- el manejo de errores y timeouts.

## Modelos

- Verifica el identificador del modelo actual en la documentación oficial de Anthropic
  antes de fijarlo (los nombres de modelo cambian). No lo hardcodees de memoria.
- Usa un modelo rápido y económico para tareas cortas (sugerencias, drafts de email).

## Manejo de errores (innegociable)

- La IA es **aditiva**. Si la llamada falla (sin key, sin internet, rate limit,
  error de API), el CRM debe seguir funcionando sin romperse.
- `_llamar_claude` captura excepciones y devuelve un resultado degradado claro
  ("La IA no está disponible ahora. Intenta de nuevo."), nunca propaga el stack.
- Timeouts razonables. No bloquees la UI indefinidamente.

## Seguridad de la key

- **NUNCA** hardcodear la key. **NUNCA** embeberla en el `.exe`.
- Fase 2 (local): el usuario pega su key una vez; se guarda en config del usuario
  (`%APPDATA%/CRM-Prospectos/`), no en el repo, no en el binario.
- Fase 3 (proxy): `_llamar_claude` apunta a una URL del backend del dev (Cloud Run).
  La key vive en el servidor. El cliente nunca la ve.

## Prompts

- System prompt en español, orientado a venta consultiva chilena.
- Pasa al modelo solo los datos del prospecto necesarios (nombre, empresa, etapa,
  notas, última actividad). No envíes la base entera.
- Para "redactar email": tono profesional, español de Chile, longitud media,
  con asunto y cuerpo.

## Testing

- En tests, `_llamar_claude` se mockea. Nunca llames a la API real en pytest.
- Verifica el camino degradado: cuando la IA falla, la ruta del CRM responde igual.
