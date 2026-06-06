"""Tests de humo. Demuestran el patrón; añade más por feature con /add-feature."""
from models import ETAPAS, Prospecto


def test_home_responde(client):
    r = client.get("/")
    assert r.status_code == 200


def test_kanban_responde(client):
    r = client.get("/kanban")
    assert r.status_code == 200


def test_etapas_son_cinco():
    assert len(ETAPAS) == 5
    assert ETAPAS[0] == "Contacto Inicial"
    assert ETAPAS[-1] == "Perdido"


def test_crear_prospecto_en_db(db_session):
    p = Prospecto(nombre="Juana Pérez", empresa="Acme SpA", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    guardado = db_session.query(Prospecto).filter_by(nombre="Juana Pérez").first()
    assert guardado is not None
    assert guardado.etapa == "Contacto Inicial"
    assert guardado.valor_estimado == 0  # default


def test_ia_degrada_sin_key(monkeypatch):
    """Sin API key, la IA devuelve mensaje degradado, no rompe."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from ai_client import sugerir_siguiente_paso

    resultado = sugerir_siguiente_paso({"nombre": "Test"})
    assert "no está disponible" in resultado.lower()
