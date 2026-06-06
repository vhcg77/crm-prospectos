# Workflow: build-release

Genera el ejecutable de escritorio listo para distribuir. Invocar con `/build-release`.

> Antes de empezar, carga la regla `.agents/rules/packaging-rules.md` (es @manual).

## Pre-requisitos (verificar)

- Estás en un **venv limpio** (`python -m venv`), NO en conda/miniforge.
- Las dependencias de producción están instaladas en ese venv.
- Todos los tests pasan: `pytest tests/ -v`.

## Pasos

1. **Tests verdes.** Ejecuta `pytest tests/ -v`. Si algo falla, detente y reporta.

2. **Verificar `config.py`.** Confirma que `resource_path()` resuelve rutas con
   `sys._MEIPASS` (build) y directorio del proyecto (dev), y que la DB de producción
   apunta a `%APPDATA%/CRM-Prospectos/`.

3. **Revisar `crm.spec`.** Confirma que `datas` incluye `templates/` y `static/`,
   que está en **modo carpeta (one-dir)**, no one-file, y que el `name` y el icono
   son los correctos.

4. **Empaquetar.** `pyinstaller crm.spec`. La salida queda en `dist/CRM-Prospectos/`.

5. **Prueba de humo del binario.**
   - Ejecuta el `.exe` desde `dist/`. Debe abrir la ventana pywebview sin consola.
   - Crea un prospecto, cámbialo de etapa, ciérralo y reábrelo: la DB persiste en APPDATA.
   - Verifica que NO aparece ninguna URL, consola ni mensaje técnico.

6. **(Fase 3) Instalador.** Empaqueta `dist/CRM-Prospectos/` con Inno Setup para
   generar el instalador. Considera incluir el runtime de WebView2.

## Checklist de seguridad antes de distribuir

- [ ] La API key NO está embebida en el binario.
- [ ] La DB de prod va a APPDATA, no junto al `.exe`.
- [ ] La app arranca sin internet (degradando la IA con gracia).
- [ ] Ningún mensaje técnico visible al usuario final.
