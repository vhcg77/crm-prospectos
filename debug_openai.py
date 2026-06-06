import sys
from openai import OpenAI

def main():
    print("=== DEBUG OPENAI ===")
    key = input("Pegá acá tu API Key nueva (sk-proj-...): ").strip()
    if not key:
        print("No ingresaste nada.")
        return

    print("\nIntentando conectar con gpt-4o-mini...")
    try:
        client = OpenAI(api_key=key, timeout=15.0)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1,
            messages=[{"role": "user", "content": "Hola"}]
        )
        print("✅ ¡ÉXITO! Conexión perfecta.")
        print(f"Respuesta del modelo: {resp.choices[0].message.content}")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}")
        print(f"Detalle exacto que da OpenAI: {e}")

if __name__ == "__main__":
    main()
