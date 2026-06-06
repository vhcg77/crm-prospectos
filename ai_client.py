"""Único punto de contacto con la API de Claude.

REGLA DE ORO: ninguna ruta, template ni servicio llama a Anthropic directamente.
Todo pasa por aquí. Cambiar de "key local" (Fase 2) a "proxy en Cloud Run" (Fase 3)
significa modificar SOLO la función privada _llamar_claude.

La IA es ADITIVA: si algo falla, el CRM sigue funcionando. Nunca propagamos errores
crudos a la UI.
"""
import os

# NOTA: verificar el identificador de modelo vigente en la documentación oficial
# de Anthropic antes de fijarlo. Los nombres de modelo cambian con el tiempo.
_MODELO = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest")
_MENSAJE_NO_DISPONIBLE = "La IA no está disponible en este momento. Intenta de nuevo."


def _obtener_api_key() -> str | None:
    """De dónde sale la key.

    Fase 2 (local): leer de variable de entorno o de config del usuario.
    Fase 3 (proxy): esta función desaparece; _llamar_claude apunta a una URL del dev.
    """
    return os.getenv("ANTHROPIC_API_KEY")


def _llamar_claude(system: str, user: str) -> str:
    """ÚNICO lugar donde se habla con Claude. Devuelve texto o mensaje degradado.

    Para migrar a proxy (Fase 3): reemplazar el cuerpo por un POST a la URL del
    backend del dev (Cloud Run). La firma no cambia.
    """
    api_key = _obtener_api_key()
    if not api_key:
        return _MENSAJE_NO_DISPONIBLE
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=_MODELO,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
            timeout=30,
        )
        partes = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
        return "\n".join(partes).strip() or _MENSAJE_NO_DISPONIBLE
    except Exception:
        # Degradación elegante: el CRM nunca se rompe por culpa de la IA.
        return _MENSAJE_NO_DISPONIBLE


# --- Funciones de dominio (lo que el resto de la app usa) ---

def sugerir_siguiente_paso(prospecto: dict) -> str:
    system = (
        "Eres un asistente de ventas consultivas en Chile. Sugiere el siguiente "
        "paso concreto y accionable para avanzar este prospecto en el pipeline. "
        "Responde en español de Chile, breve y directo (2-3 frases)."
    )
    user = f"Datos del prospecto:\n{prospecto}"
    return _llamar_claude(system, user)


def redactar_email(prospecto: dict, objetivo: str) -> str:
    system = (
        "Eres un asistente de ventas en Chile. Redacta un email profesional en "
        "español de Chile, tono cordial y directo, con asunto y cuerpo. "
        "Longitud media."
    )
    user = f"Objetivo del email: {objetivo}\n\nDatos del prospecto:\n{prospecto}"
    return _llamar_claude(system, user)
