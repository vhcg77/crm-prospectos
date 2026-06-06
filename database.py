"""Capa de base de datos: engine, sesión y dependencia get_db."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

# check_same_thread=False es necesario para SQLite con FastAPI (varios hilos).
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: una sesión por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea las tablas si no existen. Llamar al arrancar la app."""
    import models  # noqa: F401  (registra los modelos en Base)
    Base.metadata.create_all(bind=engine)
