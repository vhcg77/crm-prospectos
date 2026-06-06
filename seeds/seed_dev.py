"""Puebla crm_dev.db con 20 prospectos de prueba. Solo para desarrollo.

Uso: APP_ENV=development python seeds/seed_dev.py
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# Permite ejecutar el script desde la raíz del proyecto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from faker import Faker  # noqa: E402

from database import SessionLocal, init_db  # noqa: E402
from models import ETAPAS, Prospecto  # noqa: E402

fake = Faker("es_CL")


def seed(n: int = 20):
    init_db()
    db = SessionLocal()
    for _ in range(n):
        p = Prospecto(
            nombre=fake.name(),
            empresa=fake.company(),
            telefono=fake.phone_number(),
            email=fake.email(),
            etapa=random.choice(ETAPAS),
            notas=fake.sentence(nb_words=12),
            valor_estimado=random.choice([0, 500_000, 1_200_000, 3_500_000]),
            ultimo_contacto=date.today() - timedelta(days=random.randint(0, 45)),
            proxima_accion=random.choice(
                ["Llamar", "Enviar propuesta", "Hacer seguimiento", "Agendar reunión"]
            ),
        )
        db.add(p)
    db.commit()
    db.close()
    print(f"✅ {n} prospectos de prueba creados en crm_dev.db")


if __name__ == "__main__":
    seed()
