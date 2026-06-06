---
description: Convenciones de backend Python y FastAPI para el CRM. Aplicar al escribir o editar rutas, modelos, servicios o lógica de base de datos.
activation: model_decision
---

# Backend — Python & FastAPI

## Principios

- Python 3.12+. Type hints en toda función pública.
- FastAPI con dependencias inyectadas (`Depends`), nunca estado global mutable.
- SQLAlchemy con sesión por request vía `get_db()` (generador con `yield`).
- Una responsabilidad por módulo. Rutas finas; lógica en funciones de servicio.

## Base de datos

- `Base`, `engine`, `SessionLocal`, `get_db` viven en `database.py`.
- Los modelos en `models.py`. `Prospecto` es el modelo central.
- La constante `ETAPAS` se define UNA vez en `models.py` y se importa donde haga falta.
- Validar `email` solo si viene no vacío. `valor_estimado` default 0 (CLP, entero).
- `creado_en` / `actualizado_en` automáticos (server_default / onupdate).

## Rutas y HTMX

- Las rutas devuelven fragmentos HTML para HTMX (no JSON), salvo endpoints de IA
  que pueden devolver texto/JSON consumido por el fragmento.
- Usar `HTMLResponse` y templates Jinja2 con fragmentos parciales.
- Nombres de ruta en español coherentes con el dominio: `/prospectos`,
  `/prospectos/{id}`, `/prospectos/{id}/etapa`, `/kanban`.

## Errores y robustez

- Nunca dejar que una excepción de la API de Claude tumbe una ruta del CRM. La IA
  es aditiva: si falla, el CRM sigue funcionando. Captura y degrada con elegancia.
- El puerto puede estar ocupado: al arrancar, buscar un puerto libre en vez de
  fallar fijo en 8000 (importante para pywebview en máquina del usuario).

## Testing

- TDD: primero el test que falla, luego la implementación.
- Tests con SQLite in-memory vía el fixture `client` de `tests/conftest.py`.
- Cubrir: creación, edición, cambio de etapa, validación de email, listado/Kanban.
- `pytest tests/ -v`. Aislamiento total entre tests (crear/dropear tablas por test).

## Estilo

- Texto visible al usuario: español de Chile, claro, sin jerga.
- Nombres de código y comentarios técnicos: inglés cuando aporte; consistencia ante todo.
- Formateo: black + ruff si están disponibles.
