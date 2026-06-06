---
description: Contexto persistente del proyecto CRM. Stack, estructura, estado y convenciones. Cargar siempre.
activation: always_on
---

# Project Context — CRM de Prospección

## Estado actual del proyecto

Fase de arranque. Existe el esqueleto de carpetas y los archivos base. La app
aún no tiene features de producción terminadas. Este documento se actualiza a
medida que el proyecto avanza (modo incremental: añadir, no sobreescribir).

## Hoja de ruta

- **Fase 1** (actual): CRUD de prospectos, vista Kanban, log de actividades,
  empaquetado a ventana de escritorio (pywebview + PyInstaller).
- **Fase 2**: IA — sugerencia de siguiente paso + borrador de email automático.
  Key de Claude provista por el usuario (modelo local).
- **Fase 3**: UI pulida, instalador Inno Setup, onboarding para usuario final.
  Migrar IA a proxy en Cloud Run (la key nunca sale del control del dev).

## Estructura de carpetas

```
crm/
├── AGENTS.md                 # contrato raíz
├── .agents/                  # arnés agéntico (reglas, skills, workflows)
├── data/
│   ├── crm_dev.db            # sandbox local (gitignored)
│   └── crm_prod.db           # generado en runtime para el usuario
├── seeds/seed_dev.py         # 20 prospectos falsos (Faker es_CL)
├── tests/conftest.py         # fixtures pytest, SQLite in-memory
├── templates/                # HTML + HTMX
├── static/                   # css/js/assets
├── main.py                   # app FastAPI + arranque pywebview
├── config.py                 # detección de entorno y rutas
├── database.py               # engine, SessionLocal, get_db, Base
├── models.py                 # Prospecto, ETAPAS
├── ai_client.py              # ÚNICO punto de contacto con Claude
├── crm.spec                  # config PyInstaller (modo carpeta)
└── justfile / dev.bat        # runner de comandos (multiplataforma)
```

## Convenciones de entorno

- `APP_ENV=development` → `data/crm_dev.db`, hot reload, seed disponible.
- `APP_ENV=testing` → SQLite in-memory (lo fija el fixture de pytest).
- `APP_ENV=production` (default) → DB en carpeta de datos del usuario
  (`%APPDATA%/CRM-Prospectos/` en Windows). Nunca en el directorio del `.exe`.

## Decisiones de arquitectura ya tomadas

- **pywebview, no navegador.** El usuario final no debe ver `localhost:8000`.
- **PyInstaller en modo carpeta, no `--onefile`.** Arranque más rápido y menos
  fricción con antivirus.
- **Build en venv limpio.** Conda/miniforge NO sirve para empaquetar.
- **IA detrás de `ai_client.py`.** Migración local→proxy = cambiar una URL.
- **`ETAPAS` como constante única** en `models.py`, importada en todas partes.

## Gitflow

- Ramas `feature/**` para cada feature. PR a `develop`. Releases desde `main`.
- `data/crm_dev.db` y cualquier `.env` van en `.gitignore`.

## Colaboradores

- Usuario / dev principal: Victor (Santiago, Chile).
- Usuario final: familiar no técnico (Windows).
