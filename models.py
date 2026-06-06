"""Modelo de datos del CRM. La constante ETAPAS se define aquí y se importa
desde cualquier otro módulo (seed, rutas, Kanban, validación). Nunca duplicar.
"""
from sqlalchemy import Column, Date, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base

# Etapas del pipeline, en orden fijo. Fuente única de verdad.
ETAPAS = [
    "Contacto Inicial",
    "Propuesta Enviada",
    "Negociación",
    "Cerrado",
    "Perdido",
]

# Color sugerido por etapa (reutilizar en UI para consistencia).
COLOR_ETAPA = {
    "Contacto Inicial": "slate",
    "Propuesta Enviada": "blue",
    "Negociación": "amber",
    "Cerrado": "emerald",
    "Perdido": "rose",
}

class Actividad(Base):
    __tablename__ = "actividades"

    id = Column(Integer, primary_key=True, index=True)
    prospecto_id = Column(Integer, ForeignKey("prospectos.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String, nullable=False)  # ej: Llamada, Email, Nota, Cambio de Etapa
    descripcion = Column(Text, nullable=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    prospecto = relationship("Prospecto", back_populates="actividades")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prospecto_id": self.prospecto_id,
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }

class Prospecto(Base):
    __tablename__ = "prospectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    empresa = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    etapa = Column(String, nullable=False, default=ETAPAS[0])
    notas = Column(Text, nullable=True)
    valor_estimado = Column(Integer, nullable=False, default=0)  # CLP
    ultimo_contacto = Column(Date, nullable=True)
    proxima_accion = Column(String, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    actividades = relationship("Actividad", back_populates="prospecto", cascade="all, delete-orphan", order_by="desc(Actividad.creado_en)")

    def to_dict(self) -> dict:
        """Representación liviana para pasar a la IA o serializar."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "empresa": self.empresa,
            "telefono": self.telefono,
            "email": self.email,
            "etapa": self.etapa,
            "notas": self.notas,
            "valor_estimado": self.valor_estimado,
            "ultimo_contacto": (
                self.ultimo_contacto.isoformat() if self.ultimo_contacto else None
            ),
            "proxima_accion": self.proxima_accion,
        }
