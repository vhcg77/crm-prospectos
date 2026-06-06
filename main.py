"""Punto de entrada del CRM.

En desarrollo (APP_ENV=development) se ejecuta con uvicorn/fastapi dev y se abre
en el navegador. En producción (empaquetado), arranca el servidor en un hilo y
abre una ventana pywebview nativa (sin consola, sin navegador, sin URL visible).
"""
import os
import socket
import threading
import re
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

import jinja2
import uvicorn
from typing import Optional

from fastapi import Depends, FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from config import APP_NAME, ENV, STATIC_DIR, TEMPLATES_DIR, API_KEY_PATH
from database import get_db, init_db
from models import COLOR_ETAPA, ETAPAS, Prospecto, Actividad
from ai_client import tiene_api_key, test_conexion


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

def format_datetime_cl(dt):
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    local_dt = dt.astimezone(ZoneInfo("America/Santiago"))
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    mes = meses[local_dt.month - 1]
    return f"{local_dt.day} {mes} {local_dt.year}, {local_dt.strftime('%H:%M')}"

def format_clp(valor):
    if not valor: return "$0"
    return f"${valor:,}".replace(",", ".")

def format_clp_raw(valor):
    if not valor: return "0"
    return f"{valor:,}".replace(",", ".")

def parse_clp(valor_str: str) -> int:
    if not valor_str: return 0
    clean = re.sub(r"[^\d]", "", str(valor_str))
    return int(clean) if clean else 0

def validar_prospecto(nombre: str, email: str, telefono: str, valor_int: int, etapa: str) -> list[str]:
    errores = []
    if not nombre or not nombre.strip():
        errores.append("El nombre es obligatorio.")
    if email:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errores.append("El email no tiene un formato válido.")
    if telefono:
        if not re.match(r"^[\d\s\+\-\(\)\.]+$", telefono):
            errores.append("El teléfono solo puede contener números, espacios y los símbolos + - ( ) .")
    if valor_int < 0:
        errores.append("El valor estimado no puede ser negativo.")
    if etapa and etapa not in ETAPAS:
        errores.append("La etapa seleccionada no es válida.")
    return errores

_jinja_env.filters["datetime_cl"] = format_datetime_cl
_jinja_env.filters["format_clp"] = format_clp
_jinja_env.filters["format_clp_raw"] = format_clp_raw
templates = Jinja2Templates(env=_jinja_env)

def registrar_actividad(db: Session, prospecto_id: int, tipo: str, descripcion: str):
    act = Actividad(prospecto_id=prospecto_id, tipo=tipo, descripcion=descripcion)
    db.add(act)
    db.commit()


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

@app.get("/prospectos/buscar", response_class=HTMLResponse)
def buscar_prospectos(request: Request, q: str = "", etapa: str = "", db: Session = Depends(get_db)):
    query = db.query(Prospecto)
    if q:
        search = f"%{q}%"
        query = query.filter(or_(Prospecto.nombre.ilike(search), Prospecto.empresa.ilike(search)))
    if etapa:
        query = query.filter(Prospecto.etapa == etapa)
    
    prospectos = query.order_by(Prospecto.actualizado_en.desc()).all()
    return templates.TemplateResponse(
        request,
        "partials/prospectos_tbody.html",
        {"prospectos": prospectos, "color_etapa": COLOR_ETAPA}
    )


@app.get("/kanban/columna/{etapa}", response_class=HTMLResponse)
def kanban_col_header(etapa: str, request: Request, db: Session = Depends(get_db)):
    if etapa not in ETAPAS:
        return HTMLResponse("", status_code=400)
    prospectos = db.query(Prospecto).filter(Prospecto.etapa == etapa).all()
    return templates.TemplateResponse(
        request,
        "partials/kanban_col_header.html",
        {"etapa": etapa, "columnas": {etapa: prospectos}}
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
    nombre: str = Form(""),
    empresa: Optional[str] = Form(None),
    telefono: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    valor_estimado: str = Form("0"),
    notas: Optional[str] = Form(None),
    etapa: str = Form(ETAPAS[0]),
    db: Session = Depends(get_db)
):
    valor_int = parse_clp(valor_estimado)
    errores = validar_prospecto(nombre, email, telefono, valor_int, etapa)
    
    if errores:
        p = Prospecto(
            nombre=nombre, empresa=empresa, telefono=telefono,
            email=email, valor_estimado=valor_int, notas=notas, etapa=etapa
        )
        html = templates.get_template("form_prospecto.html").render(
            {"request": request, "prospecto": p, "etapas": ETAPAS, "errores": errores}
        )
        return HTMLResponse(html, headers={"HX-Retarget": "#modal-container", "HX-Reswap": "innerHTML"})

    p = Prospecto(
        nombre=nombre,
        empresa=empresa,
        telefono=telefono,
        email=email,
        valor_estimado=valor_int,
        notas=notas,
        etapa=etapa
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    
    registrar_actividad(db, p.id, "creado", "Prospecto creado")
    html = templates.get_template("partials/prospecto_row.html").render(p=p, color_etapa=COLOR_ETAPA)
    return HTMLResponse(html + '<div id="modal-container" hx-swap-oob="true"></div>')

@app.get("/prospectos/{id}/editar", response_class=HTMLResponse)
def form_editar_prospecto(id: int, request: Request, db: Session = Depends(get_db)):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    return templates.TemplateResponse(
        request,
        "form_prospecto.html",
        {"prospecto": p, "etapas": ETAPAS}
    )

@app.put("/prospectos/{id}")
def actualizar_prospecto(
    id: int,
    request: Request,
    nombre: str = Form(""),
    empresa: Optional[str] = Form(None),
    telefono: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    valor_estimado: str = Form("0"),
    notas: Optional[str] = Form(None),
    etapa: str = Form(None),
    db: Session = Depends(get_db)
):
    valor_int = parse_clp(valor_estimado)
    errores = validar_prospecto(nombre, email, telefono, valor_int, etapa)
    
    if errores:
        p = Prospecto(
            id=id, nombre=nombre, empresa=empresa, telefono=telefono,
            email=email, valor_estimado=valor_int, notas=notas, etapa=etapa
        )
        html = templates.get_template("form_prospecto.html").render(
            {"request": request, "prospecto": p, "etapas": ETAPAS, "errores": errores}
        )
        return HTMLResponse(html, headers={"HX-Retarget": "#modal-container", "HX-Reswap": "innerHTML"})

    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    if p:
        p.nombre = nombre
        p.empresa = empresa
        p.telefono = telefono
        p.email = email
        p.valor_estimado = valor_int
        p.notas = notas
        if etapa:
            p.etapa = etapa
        db.commit()
        db.refresh(p)
        
        registrar_actividad(db, p.id, "editado", "Datos del prospecto actualizados")
        html = templates.get_template("partials/prospecto_row.html").render(p=p, color_etapa=COLOR_ETAPA)
        return HTMLResponse(html + '<div id="modal-container" hx-swap-oob="true"></div>')
    return HTMLResponse("No encontrado", status_code=404)

@app.delete("/prospectos/{id}")
def borrar_prospecto(id: int, db: Session = Depends(get_db)):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    if p:
        db.delete(p)
        db.commit()
    return HTMLResponse("")

@app.post("/prospectos/{id}/etapa")
def cambiar_etapa(id: int, etapa: str = Form(...), db: Session = Depends(get_db)):
    if etapa not in ETAPAS:
        return HTMLResponse("Etapa inválida", status_code=400)
        
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    if p:
        etapa_anterior = p.etapa
        if etapa_anterior != etapa:
            p.etapa = etapa
            db.commit()
            db.refresh(p)
            registrar_actividad(db, p.id, "etapa", f"Cambio de etapa: {etapa_anterior} → {etapa}")
        html = templates.get_template("partials/kanban_card.html").render(p=p, color_etapa=COLOR_ETAPA)
        return HTMLResponse(html, headers={"HX-Trigger": "etapaCambiada"})
    return HTMLResponse("No encontrado", status_code=404)

@app.get("/prospectos/{id}/logs", response_class=HTMLResponse)
def ver_actividades(id: int, request: Request, db: Session = Depends(get_db)):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    return templates.TemplateResponse(
        request,
        "detalle_prospecto.html",
        {"prospecto": p, "tiene_ia": tiene_api_key()}
    )

@app.post("/prospectos/{id}/logs")
def crear_actividad(
    id: int,
    request: Request,
    descripcion: str = Form(...),
    db: Session = Depends(get_db)
):
    p = db.query(Prospecto).filter(Prospecto.id == id).first()
    if p and descripcion.strip():
        registrar_actividad(db, p.id, "nota", descripcion.strip())
    
    return templates.TemplateResponse(
        request,
        "detalle_prospecto.html",
        {"prospecto": p, "tiene_ia": tiene_api_key()}
    )

# TODO (Fase 2): rutas /prospectos/{id}/ai/... usando ai_client (degradación elegante).
@app.post("/prospectos/{id}/ai/sugerir-accion")
def ai_sugerir_accion(id: int):
    return HTMLResponse("Sugerencia de IA: Llamar para seguimiento.")

@app.post("/prospectos/{id}/ai/redactar-email")
def ai_redactar_email(id: int):
    return HTMLResponse("Borrador generado por IA...")

@app.get("/configuracion", response_class=HTMLResponse)
def get_configuracion(request: Request):
    return templates.TemplateResponse(
        request,
        "config_modal.html",
        {"tiene_ia": tiene_api_key()}
    )

@app.post("/configuracion", response_class=HTMLResponse)
def post_configuracion(request: Request, api_key: str = Form(...)):
    key = api_key.strip()
    if test_conexion(key):
        API_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        API_KEY_PATH.write_text(key)
        return templates.TemplateResponse(
            request,
            "config_modal.html",
            {"tiene_ia": True, "mensaje": "✅ Conexión exitosa. API key guardada correctamente."}
        )
    return templates.TemplateResponse(
        request,
        "config_modal.html",
        {"tiene_ia": tiene_api_key(), "error": "❌ La key es inválida o no hay conexión."}
    )


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
