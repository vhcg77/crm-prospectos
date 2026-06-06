import pytest
from models import Prospecto, Actividad, ETAPAS

def test_ai_sugerir_paso(client, db_session, monkeypatch):
    monkeypatch.setattr("ai_client._llamar_claude", lambda sys, user: "Sugerencia mockeada")
    monkeypatch.setattr("main.tiene_api_key", lambda: True)
    
    p = Prospecto(nombre="Juan AI", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    
    r = client.post(f"/prospectos/{p.id}/ia/sugerir-paso")
    assert r.status_code == 200
    
    db_session.refresh(p)
    logs_ia = [a for a in p.actividades if a.tipo == "ia"]
    assert len(logs_ia) == 1
    assert "Sugerencia mockeada" in logs_ia[0].descripcion

def test_ai_redactar_email_get(client, db_session):
    p = Prospecto(nombre="Maria Email", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    
    r = client.get(f"/prospectos/{p.id}/ia/redactar-email")
    assert r.status_code == 200
    assert "Tono del mensaje" in r.text

def test_ai_redactar_email_post(client, db_session, monkeypatch):
    monkeypatch.setattr("ai_client._llamar_claude", lambda sys, user: "Email mockeado")
    monkeypatch.setattr("main.tiene_api_key", lambda: True)
    
    p = Prospecto(nombre="Maria Post", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    
    r = client.post(f"/prospectos/{p.id}/ia/redactar-email", data={"tono": "cercano"})
    assert r.status_code == 200
    assert "Email mockeado" in r.text
    
    db_session.refresh(p)
    logs_ia = [a for a in p.actividades if a.tipo == "ia"]
    assert len(logs_ia) == 1
    assert "IA redactó un borrador" in logs_ia[0].descripcion

def test_ai_resumen_pipeline(client, db_session, monkeypatch):
    monkeypatch.setattr("ai_client._llamar_claude", lambda sys, user: "Resumen global mockeado")
    monkeypatch.setattr("main.tiene_api_key", lambda: True)
    
    p1 = Prospecto(nombre="Estancado", etapa=ETAPAS[1])
    db_session.add(p1)
    db_session.commit()
    
    r = client.get("/ia/resumen-pipeline")
    assert r.status_code == 200
    assert "Resumen global mockeado" in r.text

def test_ai_resumen_sin_key(client, monkeypatch):
    monkeypatch.setattr("main.tiene_api_key", lambda: False)
    r = client.get("/ia/resumen-pipeline")
    assert r.status_code == 200
    assert "Configura tu API key" in r.text
