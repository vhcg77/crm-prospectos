---
description: Reglas críticas de empaquetado a aplicación de escritorio (pywebview + PyInstaller + Inno Setup). Activar manualmente al trabajar en build, release o distribución.
activation: manual
---

# Empaquetado y distribución

> Esta es la parte de mayor riesgo del proyecto. Léela entera antes de tocar el build.

## Objetivo

El usuario final hace doble clic en un icono y se abre una **ventana de aplicación
nativa** con el CRM. No ve consola, ni navegador, ni URL, ni terminal.

## pywebview (la ventana)

- `main.py` arranca el servidor FastAPI en un hilo y abre una ventana pywebview
  apuntando a `http://127.0.0.1:<puerto_libre>`.
- Buscar un **puerto libre** en runtime (no fijar 8000): en la máquina del usuario
  el puerto puede estar ocupado. Abrir un socket en puerto 0 y leer el asignado.
- En Windows, pywebview usa el WebView2 de Edge (presente en Windows 10/11 modernos).
  Documentar el requisito; considerar el runtime de WebView2 en el instalador (Fase 3).
- Cerrar la ventana debe terminar el proceso del servidor limpiamente.

## PyInstaller (el empaquetado)

- Usar un **`.spec` custom**, NO la línea de comandos `--onefile`.
- **Modo carpeta (one-dir), NO one-file.** Razones:
  - Arranque mucho más rápido (one-file se auto-extrae en cada arranque).
  - Muchos menos falsos positivos de antivirus (el patrón self-extracting de
    one-file es justo lo que disparan las heurísticas de AV).
- El `.spec` debe incluir explícitamente los datos: `templates/`, `static/`, y
  cualquier asset, vía `datas=[...]`. HTMX/Tailwind son CDN, no hace falta empaquetarlos
  (pero entonces la app requiere internet; si se quiere offline, descargar los assets
  y empaquetarlos — decidir según necesidad del usuario).
- Resolver rutas con el patrón `sys._MEIPASS`: en build empaquetado los recursos
  están en `sys._MEIPASS`; en dev están en el directorio del proyecto. Centralizar
  esta lógica en `config.py` (`resource_path()`).

## Entorno de build (CRÍTICO)

- **Construir SIEMPRE desde un venv limpio (`python -m venv`), NUNCA desde conda/
  miniforge.** Conda usa características que rompen el empaquetado de PyInstaller/py2app.
- Instalar solo las deps de producción en ese venv antes de empaquetar.

## Datos del usuario

- La DB de producción va en `%APPDATA%/CRM-Prospectos/crm_prod.db` (Windows),
  NUNCA junto al `.exe` (puede estar en una carpeta de solo lectura).
- Crear el directorio si no existe en el primer arranque.

## Antivirus / confianza (Fase 3)

- Falsos positivos de AV son el problema #1 de PyInstaller en Windows. Mitigaciones:
  - Modo carpeta (ya cubierto).
  - Envolver en instalador **Inno Setup** (Windows trata instaladores distinto que
    .exe sueltos; mejor confianza y experiencia de instalación).
  - Considerar **Briefcase (BeeWare)** como alternativa que genera MSI, si el AV
    sigue dando problemas.
  - Firma de código (certificado) elimina la mayoría de flags pero cuesta dinero/año;
    evaluar solo si se va a vender en serio.

## API key (NUNCA olvidar)

- La key de Claude NO se embebe en el `.exe`. Es extraíble trivialmente del bytecode.
- Fase 2: el usuario pega su propia key, se guarda en config local del usuario.
- Fase 3 / vendible: la app llama a un proxy del dev en Cloud Run; la key vive
  en el servidor del dev. Cambiar de un modelo a otro = cambiar una URL en `ai_client.py`.
