# CRM de Prospección Personal

Un CRM de escritorio minimalista y sin fricciones diseñado para usuarios no técnicos. 
Se ejecuta como una aplicación nativa gracias a `pywebview`, ocultando terminales, consolas y URLs, pero manteniendo todo el poder de un backend en **FastAPI** y una base de datos local **SQLite**.

El frontend está construido con **HTML, Tailwind CSS (CDN) y HTMX**, manteniendo la simplicidad al máximo y evitando configuraciones pesadas de build de JavaScript (ej. sin Node.js, sin Webpack, sin Vite).

---

## 🛠️ Requisitos Previos

- Python 3.12 o superior.
- [just](https://github.com/casey/just) (Opcional, pero muy recomendado para ejecutar comandos fácilmente). Si usas Windows y no querés instalar `just`, podés usar el script `dev.bat` incluido.

> [!WARNING]
> **Entorno virtual limpio:** Es estrictamente necesario utilizar un entorno virtual estándar de Python (`python -m venv venv`) para que el empaquetado final con PyInstaller funcione correctamente. Evitá usar entornos de Conda o Miniforge.

---

## 🚀 Instalación y Configuración Inicial

1. **Crear y activar el entorno virtual:**
   ```bash
   # En Linux/macOS
   python -m venv venv
   source venv/bin/activate

   # En Windows
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Generar datos de prueba (Seed):**
   Para no empezar con un CRM vacío en desarrollo, podés sembrar la base de datos con 20 prospectos falsos:
   - Con `just`: `just seed`
   - Con Windows `.bat`: `dev.bat seed`

---

## 💻 Desarrollo (Hot Reload)

Para ejecutar la aplicación en tu navegador con recarga automática cuando modificás el código, utilizá el modo de desarrollo:

- Usando `just`:
  ```bash
  just dev
  ```
- En Windows sin `just`:
  ```bash
  dev.bat dev
  ```

*Esto iniciará FastAPI en el puerto 8000 y podrás ver el CRM entrando a `http://127.0.0.1:8000`.*

### Otros comandos útiles en desarrollo:

- **Resetear datos:** Borra la DB local de desarrollo y vuelve a correr el seed.
  `just reset-dev` o `dev.bat reset-dev`
- **Correr Tests:** Ejecuta la suite de pruebas unitarias usando SQLite en memoria.
  `just test` o `dev.bat test`

---

## 📦 Empaquetado a Escritorio (Producción)

Cuando estés listo para probar o entregar la aplicación como un ejecutable de escritorio, ejecutá la fase de *build*. Esto usa **PyInstaller** en modo carpeta (no `--onefile`, para evitar problemas de lentitud o falsos positivos con los antivirus).

- Usando `just`:
  ```bash
  just build
  ```
- En Windows sin `just`:
  ```bash
  dev.bat build
  ```

Esto generará la carpeta final dentro de `dist/`. Al ejecutar el binario generado, la aplicación levantará el servidor en un hilo secundario pidiendo un puerto libre al sistema operativo, y abrirá automáticamente una ventana de interfaz gráfica simulando una aplicación nativa. 

---

## 🏗️ Arquitectura y Principios (SOLID FOUNDATIONS)

- **Cero Build Frontend:** HTMX + Tailwind vía CDN mantienen la capa de presentación simple y rápida de modificar.
- **Entornos Aislados:** `APP_ENV=development` usa la base de datos `data/crm_dev.db`. En producción, la base de datos real del usuario se guarda en su carpeta local segura (ej. `%APPDATA%/CRM-Prospectos/` en Windows).
- **Todo por IA (Fase 2) encapsulado:** Cualquier llamada a modelos de lenguaje (Claude) debe pasar exclusivamente a través de `ai_client.py`. No se dispersan peticiones HTTP a terceros por el resto de la aplicación.
