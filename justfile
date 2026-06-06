# Runner de comandos del CRM. Multiplataforma (funciona en Windows, Linux, macOS).
# Instalar `just`: https://github.com/casey/just
# Uso: `just dev`, `just seed`, `just test`, `just build`, `just reset-dev`

# Arranca FastAPI en modo desarrollo con hot reload (abre en navegador)
dev:
    APP_ENV=development python main.py

# Puebla crm_dev.db con 20 prospectos falsos
seed:
    APP_ENV=development python seeds/seed_dev.py

# Ejecuta los tests (SQLite in-memory, aislamiento por test)
test:
    APP_ENV=testing pytest tests/ -v

# Empaqueta el ejecutable de escritorio (modo carpeta). Usar venv limpio, NO conda.
build:
    pyinstaller crm.spec

# Borra la DB de desarrollo y re-siembra
reset-dev:
    rm -f data/crm_dev.db
    just seed
