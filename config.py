"""Configuración central: entorno, rutas de datos y resolución de recursos.

Este módulo es el único lugar que decide:
- qué base de datos usar según APP_ENV,
- dónde viven los datos del usuario en producción,
- cómo resolver rutas a recursos (templates/static) en dev vs. empaquetado.
"""
import os
import sys
from pathlib import Path

ENV = os.getenv("APP_ENV", "production")


def resource_path(relative: str) -> Path:
    """Resuelve la ruta a un recurso empaquetado.

    En un build de PyInstaller los recursos viven en sys._MEIPASS.
    En desarrollo viven junto a este archivo.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / relative
    return Path(__file__).parent / relative


def user_data_dir() -> Path:
    """Directorio de datos del usuario en producción.

    En Windows: %APPDATA%/CRM-Prospectos/
    En otros SO: ~/.crm-prospectos/
    Nunca junto al ejecutable (puede ser solo-lectura).
    """
    if os.name == "nt":
        base = Path(os.getenv("APPDATA", Path.home())) / "CRM-Prospectos"
    else:
        base = Path.home() / ".crm-prospectos"
    base.mkdir(parents=True, exist_ok=True)
    return base


# --- Selección de base de datos según entorno ---
if ENV == "development":
    DATA_DIR = Path(__file__).parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'crm_dev.db'}"
elif ENV == "testing":
    # El fixture de pytest fija una DB in-memory; este valor es solo fallback.
    DATABASE_URL = "sqlite:///:memory:"
else:  # production
    DATABASE_URL = f"sqlite:///{user_data_dir() / 'crm_prod.db'}"

# Directorios de recursos (funcionan en dev y empaquetado)
TEMPLATES_DIR = resource_path("templates")
STATIC_DIR = resource_path("static")

APP_NAME = "CRM de Prospección"
DIAS_ESTANCADO = 14
