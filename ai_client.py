"""Único punto de contacto con la API de Claude.

REGLA DE ORO: ninguna ruta, template ni servicio llama a Anthropic directamente.
Todo pasa por aquí. Cambiar de "key local" (Fase 2) a "proxy en Cloud Run" (Fase 3)
significa modificar SOLO la función privada _llamar_claude.

La IA es ADITIVA: si algo falla, el CRM sigue funcionando. Nunca propagamos errores
crudos a la UI.
"""
import os

# NOTA: verificar el identificador de modelo vigente en la documentación oficial
# de OpenAI antes de fijarlo. Los nombres de modelo cambian con el tiempo.
_MODELO = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_MENSAJE_NO_DISPONIBLE = "La IA no está disponible en este momento. Intenta de nuevo."


def _obtener_api_key() -> str | None:
    """De dónde sale la key.

    Fase 2 (local): leer de variable de entorno o de config del usuario.
    Fase 3 (proxy): esta función desaparece; _llamar_claude apunta a una URL del dev.
    """
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key.strip()
        
    from config import API_KEY_PATH
    try:
        if API_KEY_PATH.exists():
            content = API_KEY_PATH.read_text().strip()
            if content:
                return content
    except Exception:
        pass
    return None

def tiene_api_key() -> bool:
    """Comprueba si hay una key configurada (útil para la UI)."""
    return bool(_obtener_api_key())

def test_conexion(api_key: str) -> bool:
    """Valida que la key funcione con una llamada mínima."""
    if not api_key:
        return False
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, timeout=10.0)
        client.chat.completions.create(
            model=_MODELO,
            max_tokens=1,
            messages=[{"role": "user", "content": "Hola"}]
        )
        return True
    except Exception:
        return False


def _llamar_claude(system: str, user: str) -> str:
    """ÚNICO lugar donde se habla con Claude. Devuelve texto o mensaje degradado.

    Para migrar a proxy (Fase 3): reemplazar el cuerpo por un POST a la URL del
    backend del dev (Cloud Run). La firma no cambia.
    """
    api_key = _obtener_api_key()
    if not api_key:
        return _MENSAJE_NO_DISPONIBLE
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=30.0)
        resp = client.chat.completions.create(
            model=_MODELO,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        return resp.choices[0].message.content.strip() or _MENSAJE_NO_DISPONIBLE
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


def redactar_email(prospecto: dict, objetivo: str, tono: str = "formal") -> str:
    system = (
        f"Eres un asistente de ventas en Chile. Redacta un email profesional en "
        f"español de Chile. Tono requerido: {tono}. "
        f"Debe incluir asunto y cuerpo, sin placeholders genéricos si tienes la info. "
        f"Longitud media."
    )
    user = f"Objetivo del email: {objetivo}\n\nDatos del prospecto:\n{prospecto}"
    return _llamar_claude(system, user)


def resumen_pipeline(datos_pipeline: dict) -> str:
    system = (
        "Eres un gerente de ventas en Chile analizando el embudo de prospectos. "
        "Recibes un resumen estadístico (totales por etapa y estancados). "
        "Devuelve un párrafo breve (máximo 4 líneas) con un diagnóstico rápido "
        "y una recomendación accionable, en español de Chile, directo y al grano."
    )
    user = f"Datos del pipeline:\n{datos_pipeline}"
    return _llamar_claude(system, user)
