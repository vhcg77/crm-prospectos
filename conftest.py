"""Asegura que la raíz del proyecto esté en sys.path para las importaciones
de los tests (database, models, main, etc.)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
