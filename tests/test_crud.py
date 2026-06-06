import pytest
from models import Prospecto, Actividad, ETAPAS

def test_crear_prospecto(client, db_session):
    data = {
        "nombre": "Juan Perez",
        "empresa": "Acme Corp",
        "telefono": "12345678",
        "email": "juan@acme.com",
        "valor_estimado": 500000,
        "notas": "Nota inicial",
        "etapa": ETAPAS[0]
    }
    response = client.post("/prospectos", data=data)
    assert response.status_code == 200
    # Como HTMX nos devuelve HTML para insertar, podemos buscar que el nombre esté en la respuesta
    assert "Juan Perez" in response.text
    # También debemos validar que se devuelva el OOB del modal para cerrarlo
    assert 'id="modal-container"' in response.text
    assert 'hx-swap-oob="true"' in response.text
    
    # Verificar en DB (ya que estamos)
    resp_get = client.get("/")
    assert "Juan Perez" in resp_get.text
    
    # Comprobar log "creado"
    p = db_session.query(Prospecto).filter_by(nombre="Juan Perez").first()
    actividades = db_session.query(Actividad).filter_by(prospecto_id=p.id).all()
    assert len(actividades) == 1
    assert actividades[0].tipo == "creado"

def test_actualizar_prospecto(client, db_session):
    p = Prospecto(nombre="Test Update", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    
    data = {
        "nombre": "Nombre Actualizado",
        "empresa": "Tech LLC",
        "etapa": ETAPAS[1]
    }
    # Ahora usamos PUT según el plan RESTful para HTMX
    response = client.put(f"/prospectos/{p.id}", data=data)
    assert response.status_code == 200
    assert "Nombre Actualizado" in response.text
    assert 'id="modal-container"' in response.text
    assert 'hx-swap-oob="true"' in response.text
    
    # Comprobar log "editado"
    actividades = db_session.query(Actividad).filter_by(prospecto_id=p.id).all()
    assert len(actividades) == 1
    assert actividades[0].tipo == "editado"

def test_borrar_prospecto(client, db_session):
    p = Prospecto(nombre="A Borrar", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    
    response = client.delete(f"/prospectos/{p.id}")
    assert response.status_code == 200
    assert response.text == ""  # Elimina del DOM
    
    # Validar que ya no existe en la DB a través de la lista
    resp_get = client.get("/")
    assert "A Borrar" not in resp_get.text

def test_cambiar_etapa_kanban(client, db_session):
    p = Prospecto(nombre="Test Kanban", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    
    data = {"etapa": ETAPAS[1]}
    response = client.post(f"/prospectos/{p.id}/etapa", data=data)
    assert response.status_code == 200
    assert 'id="kanban-card-' in response.text
    
    # Refrescamos la sesion
    db_session.refresh(p)
    assert p.etapa == ETAPAS[1]
    
    # Comprobar log
    actividades = db_session.query(Actividad).filter_by(prospecto_id=p.id).all()
    assert len(actividades) == 1
    assert actividades[0].descripcion == f"Cambio de etapa: {ETAPAS[0]} → {ETAPAS[1]}"

def test_cambiar_etapa_invalida(client, db_session):
    p = Prospecto(nombre="Test Kanban Error", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    
    data = {"etapa": "Etapa Invalida 123"}
    response = client.post(f"/prospectos/{p.id}/etapa", data=data)
    assert response.status_code == 400
    
    db_session.refresh(p)
    assert p.etapa == ETAPAS[0]  # No cambió

def test_crear_nota_log(client, db_session):
    p = Prospecto(nombre="Test Actividad", etapa=ETAPAS[0])
    db_session.add(p)
    db_session.commit()
    
    data = {
        "descripcion": "No contestó."
    }
    response = client.post(f"/prospectos/{p.id}/logs", data=data)
    assert response.status_code == 200
    assert "No contestó." in response.text
    
    actividades = db_session.query(Actividad).filter_by(prospecto_id=p.id).all()
    assert len(actividades) == 1
    assert actividades[0].tipo == "nota"
