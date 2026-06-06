# Plan de Iteración — CRM de Prospección (Iteración 2)

> **Cómo usar este documento con Antigravity**
> Este es el plan maestro. Cada feature de abajo es **atómico**: copia el bloque completo (desde el título hasta su "Hecho cuando") y pásalo al agente como un único `/add-feature`. No mezcles features en una sola corrida; el agente trabaja mejor con alcance acotado y verificable.
>
> **Orden recomendado:** F1 → F2 → F3 → F4 → F5 → F6 → F7 → F8 → F9 → F10. Las dependencias están anotadas.
>
> **Reglas que el agente NO debe violar** (recordárselas si hace falta):
> - No tocar la costura del proxy en `ai_client.py`. Toda IA pasa por ese módulo. Migrar a Cloud Run = cambiar una URL, nada más.
> - No embeber API keys. Fase 2 usa key local del usuario.
> - `ETAPAS` es la única fuente de verdad de las 5 etapas. Nada de strings sueltos.
> - Build siempre desde venv limpio, nunca conda/miniforge.
> - No usar `--onefile` en PyInstaller.

---

## Estado actual (baseline)

Ya funciona: vista de lista, vista Kanban (5 columnas estáticas), modal "Nuevo Prospecto", esqueleto FastAPI + HTMX + Tailwind + SQLite, `ai_client.py` con la costura del proxy, tests verdes (5), `crm.spec`.

Falta: persistir cambios de etapa, drag&drop real, logs de actividad, validación, formato de moneda, búsqueda, métricas, export, y las features de IA.

---

## Convención común para todos los features

- **Stack:** FastAPI + HTMX + Tailwind + SQLite (sin frameworks JS pesados).
- **Estilo de respuesta HTMX:** los endpoints que modifican datos devuelven el fragmento HTML afectado (la tarjeta, la fila, la columna), no JSON, salvo que se indique.
- **Cada feature incluye su test** en `tests/` y debe dejar los tests existentes en verde.
- **Cada cambio de datos** que sea relevante para el negocio debe escribir un registro en el log de actividad (ver F3).
- **i18n:** todo el texto visible en español de Chile.

---

# FASE 1 — Cerrar el CRUD

---

## F1 · CRUD completo de prospectos

**Objetivo:** que el modal "Nuevo Prospecto" y "Editar" persistan de verdad, y que "Borrar" funcione con confirmación.

**Alcance:**
- `POST /prospectos` — crear desde el modal. Devuelve la fila/tarjeta nueva insertada vía HTMX (`hx-swap`).
- `GET /prospectos/{id}/editar` — devuelve el modal precargado con los datos.
- `PUT /prospectos/{id}` (o `POST` con `_method`) — actualizar. Devuelve la fila actualizada.
- `DELETE /prospectos/{id}` — borrar con confirmación (`hx-confirm="¿Borrar a {nombre}?"`). Devuelve vacío y remueve la fila del DOM.
- Reutilizar el mismo template de modal para crear y editar (un solo parcial).

**Restricciones:**
- Usar los 10 campos confirmados del modelo. No inventar campos.
- La etapa por defecto al crear es la primera de `ETAPAS`.

**Hecho cuando:** puedo crear, editar y borrar un prospecto desde la UI sin recargar la página entera, y los cambios sobreviven a reiniciar el servidor. Test cubre los 4 verbos.

---

## F2 · Drag & drop persistente en el Kanban

**Depende de:** F1.
**Objetivo:** mover una tarjeta entre columnas actualiza la etapa en la base y queda registrado.

**Alcance:**
- Integrar **SortableJS** (vía CDN o `static/`) en las 5 columnas del Kanban.
- Al soltar una tarjeta, disparar `hx-post` a `POST /prospectos/{id}/etapa` con la nueva etapa.
- El endpoint valida que la etapa pertenezca a `ETAPAS`, actualiza, y escribe un log "Cambio de etapa: {anterior} → {nueva}".
- Devolver la tarjeta re-renderizada (para reflejar cualquier cambio visual) o `204` si el optimismo del front es suficiente.
- Manejar el caso de error (etapa inválida, id inexistente): revertir visualmente.

**Restricciones:**
- Sin librerías de Kanban completas (ej. no usar un framework que reemplace HTMX). Solo SortableJS para el arrastre.
- El orden dentro de la columna no necesita persistirse en esta iteración (solo la etapa).

**Hecho cuando:** arrastro "María Gómez León" de Negociación a Cerrado, recargo la página, y sigue en Cerrado. Se generó un log del cambio.

---

## F3 · Log de actividades

**Depende de:** F1.
**Objetivo:** historial cronológico por prospecto (creación, cambios de etapa, ediciones, notas manuales).

**Alcance:**
- Tabla `actividad`: `id`, `prospecto_id` (FK), `tipo` (enum: creado, etapa, editado, nota, ia), `descripcion`, `creado_en` (timestamp).
- Helper `registrar_actividad(prospecto_id, tipo, descripcion)` invocable desde cualquier endpoint.
- Que F1 y F2 lo usen (creación, edición, cambio de etapa).
- Endpoint `GET /prospectos/{id}/logs` que devuelve el historial — ya hay un botón "Logs" en la lista, conectarlo.
- Permitir agregar una **nota manual** desde la vista de detalle (tipo `nota`).

**Restricciones:**
- `creado_en` en UTC en la base, formatear a hora de Chile en la vista.
- No borrar logs al borrar un prospecto si quieres auditoría; o `ON DELETE CASCADE` si prefieres limpieza. **Decisión recomendada: CASCADE** para esta demo personal.

**Hecho cuando:** el botón "Logs" abre el historial real de un prospecto, en orden cronológico inverso, con fechas legibles en español.

---

# QUICK WINS DE UX

---

## F4 · Formato de moneda chileno consistente

**Objetivo:** que todo monto se muestre como `$3.500.000` (punto como separador de miles, sin decimales) en lista, Kanban, detalle y totales.

**Alcance:**
- Filtro/función de formateo único (ej. `format_clp(valor)`) usado en todos los templates. Una sola implementación.
- Guardar siempre el valor como entero en la base; formatear solo en la capa de presentación.
- El input de "Valor Estimado" en el modal acepta números y los normaliza (quitar puntos/espacios antes de guardar).

**Hecho cuando:** no existe ningún monto en la UI sin formatear, y guardar "3500000" o "3.500.000" produce el mismo resultado.

---

## F5 · Validación de formulario

**Depende de:** F1.
**Objetivo:** evitar datos basura desde el modal.

**Alcance:**
- Nombre: obligatorio, no vacío.
- Email: si viene, formato válido.
- Teléfono: si viene, solo dígitos/espacios/+/-/().
- Valor estimado: numérico ≥ 0.
- Etapa: debe estar en `ETAPAS`.
- Validación tanto en servidor (autoritativa) como hints HTML5 en el front.
- Mostrar errores inline en el modal sin perder lo ya escrito (HTMX devuelve el modal con errores).

**Hecho cuando:** intentar guardar sin nombre, o con email malformado, muestra el error en el modal y no crea el registro.

---

## F6 · Búsqueda y filtro en la lista

**Depende de:** F1.
**Objetivo:** encontrar prospectos rápido cuando hay muchos.

**Alcance:**
- Input de búsqueda con `hx-get` (debounce ~300ms) que filtra la tabla por **nombre o empresa** mientras se escribe.
- Filtro por etapa (dropdown o chips) que se combina con la búsqueda.
- Devolver solo el `<tbody>` re-renderizado.

**Hecho cuando:** escribir "rojas" deja en la lista solo los prospectos cuyo nombre o empresa contiene "rojas", sin recargar.

---

## F7 · Métricas por columna en el Kanban

**Depende de:** F2, F4.
**Objetivo:** ver plata, no solo conteo.

**Alcance:**
- En cada encabezado de columna: conteo + suma de valor estimado formateada. Ej: `Negociación · 4 · $2.000.000`.
- Recalcular al mover tarjetas (parte del swap de F2 o un `hx-trigger` que refresque encabezados).

**Hecho cuando:** cada columna muestra su total en CLP y se actualiza al arrastrar una tarjeta entre columnas.

---

## F8 · Indicador de prospectos estancados

**Depende de:** F3.
**Objetivo:** detectar oportunidades sin movimiento.

**Alcance:**
- Calcular "última actividad" a partir del log (max `creado_en` por prospecto).
- Resaltar en la tarjeta/fila los prospectos sin actividad en >14 días (borde o badge ámbar). Umbral como constante configurable.
- No aplica a etapas terminales (Cerrado, Perdido) — esas no se consideran estancadas.

**Hecho cuando:** un prospecto en Negociación sin tocar hace 15 días aparece marcado; uno tocado ayer, no.

---

# COSTURA DE IA (Fase 2)

> Todo lo de abajo pasa **exclusivamente** por `ai_client.py`. El agente NO debe llamar a la API de Anthropic desde los endpoints directamente. La función pública de `ai_client.py` recibe un prompt/contexto y devuelve texto; de dónde sale (key local hoy, proxy mañana) es problema interno del módulo.

---

## F9 · Gestión de API key local + estado de IA

**Objetivo:** dejar lista la infraestructura para que las features de IA funcionen con la key local del usuario, sin embeberla.

**Alcance:**
- Pantalla/sección de "Configuración" donde el usuario pega su API key.
- Persistir la key de forma local y razonablemente segura (ej. archivo en directorio de config del usuario, NO en el repo, NO en la base de prospectos). El agente debe respetar `config.py`.
- `ai_client.py` lee la key desde esa fuente. Si no hay key, las features de IA se muestran deshabilitadas con un mensaje claro ("Configura tu API key para usar IA").
- Endpoint de "test de conexión" que hace una llamada mínima y reporta si la key funciona.

**Restricciones:**
- NO embeber la key. NO commitearla. NO romper la costura del proxy: el día de mañana, en vez de leer key local, `ai_client.py` apuntará a Cloud Run y este código de UI no cambia.

**Hecho cuando:** sin key, los botones de IA están deshabilitados con mensaje; con una key válida pegada en Configuración, el test de conexión responde OK.

---

## F10 · Features de IA visibles

**Depende de:** F9, F3.
**Objetivo:** las tres acciones de IA que venden la demo.

**Alcance (cada una es un botón que llama a `ai_client.py`):**
1. **Sugerir siguiente paso** — desde la vista de detalle, manda etapa + notas + historial y devuelve una recomendación accionable. Se guarda como log tipo `ia`.
2. **Redactar email de seguimiento** — genera un borrador según el contexto del prospecto, con tono ajustable (formal / cercano). Mostrar en un modal copiable.
3. **Resumen del pipeline** — botón global que manda el estado agregado (totales por etapa, estancados) y devuelve un párrafo tipo "Tienes $X en negociación, 3 prospectos sin tocar hace 2 semanas, foco sugerido: …".

**Restricciones:**
- Toda llamada vía `ai_client.py`. Los endpoints solo arman el contexto y renderizan la respuesta.
- Manejar el caso "sin key" (deshabilitado, ver F9) y el caso de error de la API (mensaje amable, no stacktrace).
- Streaming opcional; si complica, respuesta completa está bien para la demo.

**Hecho cuando:** desde un prospecto puedo pedir "siguiente paso" y "redactar email", y desde el dashboard pido "resumen del pipeline", todo funcionando con la key local y registrando lo relevante en el log.

---

# Cierre de la iteración (no son `/add-feature`, son checklist manual)

- [ ] Correr `just test` (o equivalente): todos los tests verdes.
- [ ] Build con `/build-release` desde venv limpio (modo carpeta, no onefile).
- [ ] Verificar que el ejecutable abre la ventana pywebview sin consola.
- [ ] Reemplazar `static/icon.ico` con el icono propio.
- [ ] Probar el flujo completo como lo haría el familiar no técnico: doble clic → crear prospecto → arrastrar en Kanban → pedir sugerencia de IA.

---

## Notas de priorización

Si el tiempo aprieta, el **núcleo vendible mínimo** es F1 + F2 + F3 + F4 (CRUD real, Kanban que persiste, logs, moneda decente). F5–F8 son pulido que se nota mucho con poco esfuerzo. F9–F10 son el diferenciador ("tiene IA"), pero dependen de que el núcleo esté sólido — no los adelantes.
