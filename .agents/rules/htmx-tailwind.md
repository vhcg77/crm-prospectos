---
description: Convenciones de frontend con HTML, HTMX y Tailwind para el CRM. Aplicar al escribir o editar templates, fragmentos HTML, o interacciones de UI.
activation: model_decision
---

# Frontend — HTMX + Tailwind

## Filosofía

- Sin build step de JS. Tailwind por CDN, HTMX por CDN. Cero npm, cero bundlers.
- El servidor manda HTML. HTMX intercambia fragmentos. JS mínimo y solo si es
  imprescindible (p. ej. drag & drop del Kanban).
- La UI es para un usuario NO técnico: grande, clara, en español, con confirmaciones
  amables y mensajes de error comprensibles (nunca stack traces ni códigos).

## Pantallas (3 principales)

1. **Lista** de prospectos: tabla/cards con buscador, filtro por etapa, botón "+ Nuevo".
2. **Kanban**: 5 columnas = las 5 etapas. Tarjetas arrastrables entre columnas;
   soltar una tarjeta hace `hx-post` para cambiar la etapa.
3. **Detalle** de prospecto: ficha editable + log de actividades + (Fase 2) panel de IA
   con "Sugerir siguiente paso" y "Redactar email".

## Patrones HTMX

- Crear/editar vía `hx-post`/`hx-put` devolviendo el fragmento actualizado.
- Cambio de etapa por drag&drop: `hx-post="/prospectos/{id}/etapa"` con la nueva etapa.
- Usar `hx-target` e `hx-swap` explícitos. Indicadores de carga con `hx-indicator`.
- Para el panel de IA (Fase 2): `hx-post` a `/prospectos/{id}/ai/...`, con spinner,
  y manejo visible de "la IA no está disponible" si `ai_client` falla.

## Estilo visual

- Paleta sobria y profesional (es demo vendible). Buen contraste, botones grandes.
- Etiquetas de etapa con color consistente (definir un color por etapa, reutilizar).
- Responsive razonable, pero el objetivo es escritorio (ventana pywebview).
- Estados vacíos amables: "Aún no tienes prospectos. Agrega el primero 👇".

## Reglas de oro

- NUNCA mostrar al usuario URLs internas, puertos, ni mensajes técnicos.
- Confirmar acciones destructivas (eliminar prospecto) con un diálogo claro.
- Todo texto en español de Chile.
