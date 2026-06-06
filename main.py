"""Punto de entrada del CRM.

En desarrollo (APP_ENV=development) se ejecuta con uvicorn/fastapi dev y se abre
en el navegador. En producción (empaquetado), arranca el servidor en un hilo y
abre una ventana pywebview nativa (sin consola, sin navegador, sin URL visible).
"""
import os
import socket
import threading
from contextlib import asynccontextmanager

import jinja2
import uvicorn
from typing import Optional

from fastapi import Depends, FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from config import APP_NAME, ENV, STATIC_DIR, TEMPLATES_DIR
from database import get_db, init_db
from models import COLOR_ETAPA, ETAPAS, Prospecto, Actividad


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR.resolve())),
    autoescape=jinja2.select_autoescape(),
    cache_size=0,  # evita el bug de cache_key no hasheable en Starlette 1.2.x
)
templates = Jinja2Templates(env=_jinja_env)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    prospectos = db.query(Prospecto).order_by(Prospecto.actualizado_en.desc()).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "prospectos": prospectos,
            "etapas": ETAPAS,
            "color_etapa": COLOR_ETAPA,
            "app_name": APP_NAME,
        },
    )


@app.get("/kanban", response_class=HTMLResponse)
def kanban(request: Request, db: Session = Depends(get_db)):
    columnas = {
        etapa: db.query(Prospecto).filter(Prospecto.etapa == etapa).all()
        for etapa in ETAPAS
    }
    return templates.TemplateResponse(
        request,
        "kanban.html",
        {
            "columnas": columnas,
            "etapas": ETAPAS,
            "color_etapa": COLOR_ETAPA,
            "app_name": APP_NAME,
        },
    )


# TODO (Fase 1): CRUD de prospectos, cambio de etapa por drag&drop, log de actividades.
@app.get("/prospectos/nuevo", response_class=HTMLResponse)
def form_nuevo_prospecto(request: Request):
    return templates.TemplateResponse(
        request,
        "form_prospecto.html",
        {"prospecto": None, "etapas": ETAPAS}
    )

@app.post("/prospectos")
def crear_prospecto(
    request: Request,
    nombre: str = Form(...),
    empresa: Optional[str] = Form(None),
    telefono: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    valor_estimado: int = Form(0),
    notas: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    p = Prospecto(
        nombre=nombre,
        empresa=empresa,
        telefono=telefono,
        email=email,
        valor_estimado=valor_estimado,
        notas=notas
    )
    db.add(p)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/prospectos/{id}/editar", response_class=HTMLResponse)
def form_editar_prospecto(id: int, request: Request, db: Session = Depends(get_db)):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    return templates.TemplateResponse(
        request,
        "form_prospecto.html",
        {"prospecto": p, "etapas": ETAPAS}
    )

@app.post("/prospectos/{id}/editar")
def actualizar_prospecto(
    id: int,
    request: Request,
    nombre: str = Form(...),
    empresa: Optional[str] = Form(None),
    telefono: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    valor_estimado: int = Form(0),
    notas: Optional[str] = Form(None),
    etapa: str = Form(None),
    db: Session = Depends(get_db)
):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    if p:
        p.nombre = nombre
        p.empresa = empresa
        p.telefono = telefono
        p.email = email
        p.valor_estimado = valor_estimado
        p.notas = notas
        if etapa:
            p.etapa = etapa
        db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.delete("/prospectos/{id}")
def borrar_prospecto(id: int, db: Session = Depends(get_db)):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    if p:
        db.delete(p)
        db.commit()
    return HTMLResponse("")

@app.post("/prospectos/{id}/etapa")
def cambiar_etapa(id: int, etapa: str = Form(...), db: Session = Depends(get_db)):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    if p:
        p.etapa = etapa
        act = Actividad(prospecto_id=p.id, tipo="Cambio de Etapa", descripcion=f"Movido a {etapa}")
        db.add(act)
        db.commit()
    return HTMLResponse("OK")

@app.get("/prospectos/{id}/actividades", response_class=HTMLResponse)
def ver_actividades(id: int, request: Request, db: Session = Depends(get_db)):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    return templates.TemplateResponse(
        request,
        "detalle_prospecto.html",
        {"prospecto": p}
    )

@app.post("/prospectos/{id}/actividades")
def crear_actividad(
    id: int,
    tipo: str = Form(...),
    descripcion: str = Form(...),
    db: Session = Depends(get_db)
):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    if p:
        act = Actividad(prospecto_id=p.id, tipo=tipo, descripcion=descripcion)
        db.add(act)
        db.commit()
    return RedirectResponse(url=f"/prospectos/{id}/actividades", status_code=303)

# TODO (Fase 2): rutas /prospectos/{id}/ai/... usando ai_client (degradación elegante).
@app.post("/prospectos/{id}/ai/sugerir-accion")
def ai_sugerir_accion(id: int):
    return HTMLResponse("Sugerencia de IA: Llamar para seguimiento.")

@app.post("/prospectos/{id}/ai/redactar-email")
def ai_redactar_email(id: int):
    return HTMLResponse("Borrador generado por IA...")


def _puerto_libre() -> int:
    """Pide al SO un puerto libre. Nunca fijar 8000 en la máquina del usuario."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _correr_servidor(puerto: int):
    uvicorn.run(app, host="127.0.0.1", port=puerto, log_level="warning")


def main():
    """Arranque en producción: servidor en hilo + ventana pywebview."""
    import webview  # import diferido: solo se necesita en el binario empaquetado

    puerto = _puerto_libre()
    hilo = threading.Thread(target=_correr_servidor, args=(puerto,), daemon=True)
    hilo.start()

    ventana = webview.create_window(
        APP_NAME,
        f"http://127.0.0.1:{puerto}",
        width=1200,
        height=800,
    )
    webview.start()  # bloquea hasta que se cierra la ventana
    # Al cerrar la ventana, el proceso termina (el hilo es daemon).


if __name__ == "__main__":
    if ENV == "development":
        # En dev: arranque simple en el navegador.
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    else:
        main()
