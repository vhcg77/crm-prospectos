# AGENTS.md — CRM de Prospección Personal

> Contrato raíz para agentes (Antigravity, Cursor, Claude Code). Cross-tool.
> Lee SIEMPRE este archivo y `.agents/rules/project-context.md` antes de actuar.

## Qué estamos construyendo

Un **CRM de prospección personal de escritorio** para un usuario final NO técnico.
La experiencia objetivo es: el usuario hace doble clic en un icono y se abre una
ventana de aplicación nativa con el CRM dentro. **No debe ver consolas, terminales,
URLs, ni instrucciones técnicas.**

Es además una **demo vendible**: el código debe quedar lo bastante limpio y
parametrizado como para reutilizarlo con otros clientes.

## Stack (no cambiar sin aprobación explícita del usuario)

- Backend: **FastAPI** (Python 3.12+)
- Base de datos: **SQLite** vía SQLAlchemy (archivo local)
- Frontend: **HTML + Tailwind (CDN) + HTMX** (sin build step de JS)
- Ventana de escritorio: **pywebview** (NO abrir navegador externo, NO mostrar consola)
- Empaquetado: **PyInstaller** con `.spec` custom en modo carpeta (NO `--onefile`)
- IA: **Claude API** vía el SDK de Anthropic, SIEMPRE detrás de `ai_client.py`

## Reglas de oro (innegociables)

1. **La experiencia del usuario final manda.** Cero fricción técnica. Si una
   solución técnica elegante empeora la experiencia del no-técnico, se descarta.
2. **Toda llamada a Claude pasa por `ai_client.py`.** Nunca llames a la API de
   Anthropic directamente desde una ruta, un template o un servicio. Una sola
   función, un solo punto de cambio. Esto permite migrar de "key local" a
   "proxy en Cloud Run" cambiando una URL.
3. **Nunca embebas la API key en el código ni en el `.exe`.** La key se lee de
   config/almacenamiento del usuario, jamás hardcodeada.
4. **El entorno de build es un venv limpio, NUNCA conda/miniforge.** PyInstaller
   falla con entornos conda.
5. **TDD por feature.** Antes de implementar una feature, escribe el test que
   falla. Los tests usan SQLite in-memory (ver `tests/conftest.py`).
6. **Separa dev de prod por entorno.** `APP_ENV=development` usa `crm_dev.db`;
   producción usa la ruta de datos del usuario. Nunca toques datos de prod en dev.
7. **Comunícate con el usuario en español.** El código, nombres de variables,
   y documentación técnica para agentes en inglés cuando aporte claridad; los
   textos visibles al usuario final SIEMPRE en español de Chile.

## Modelo de datos: Prospecto

| Campo            | Tipo      | Notas                                            |
|------------------|-----------|--------------------------------------------------|
| id               | int PK    | autoincrement                                    |
| nombre           | str       | requerido                                        |
| empresa          | str       | opcional                                         |
| telefono         | str       | opcional                                         |
| email            | str       | opcional, validar formato si está presente       |
| etapa            | str       | enum: ver etapas abajo                           |
| notas            | text      | libre                                            |
| valor_estimado   | int       | CLP, opcional, default 0                         |
| ultimo_contacto  | date      | opcional                                         |
| proxima_accion   | str       | opcional (texto + idealmente fecha)              |
| creado_en        | datetime  | auto                                             |
| actualizado_en   | datetime  | auto                                             |

## Etapas del pipeline (orden fijo)

1. Contacto Inicial
2. Propuesta Enviada
3. Negociación
4. Cerrado
5. Perdido

Definir estas etapas como una constante única (`ETAPAS`) reutilizada por modelo,
seed, Kanban y validación. Nunca las repitas hardcodeadas en varios sitios.

## Cómo trabajar

- Antes de tocar código: lee `.agents/rules/project-context.md`.
- Para añadir una feature: usa el workflow `/add-feature`.
- Para generar un release: usa el workflow `/build-release`.
- Para integrar IA: consulta la skill `ai-integration`.
- Mantén cada archivo de regla bajo 12.000 caracteres (límite de Antigravity).

---

## Principios de trabajo (Karpathy)

> Pautas de comportamiento para reducir errores comunes de LLM al programar.
> **Tradeoff:** sesgan hacia la cautela por sobre la velocidad. Para tareas
> triviales, usa criterio.

### 1. Piensa antes de programar

**No asumas. No ocultes la confusión. Expón los tradeoffs.**

Antes de implementar:
- Declara tus supuestos explícitamente. Si hay incertidumbre, pregunta.
- Si existen varias interpretaciones, preséntalas — no elijas en silencio.
- Si hay un enfoque más simple, dilo. Empuja en contra cuando corresponda.
- Si algo no está claro, detente. Nombra qué te confunde. Pregunta.

### 2. Simplicidad primero

**El mínimo código que resuelve el problema. Nada especulativo.**

- Sin features más allá de lo pedido.
- Sin abstracciones para código de un solo uso.
- Sin "flexibilidad" o "configurabilidad" no solicitada.
- Sin manejo de errores para escenarios imposibles.
- Si escribes 200 líneas y podrían ser 50, reescríbelo.

Pregúntate: "¿Un ingeniero senior diría que esto está sobre-complicado?" Si sí,
simplifica.

### 3. Cambios quirúrgicos

**Toca solo lo necesario. Limpia solo tu propio desorden.**

Al editar código existente:
- No "mejores" código, comentarios o formato adyacentes.
- No refactorices lo que no está roto.
- Respeta el estilo existente, aunque tú lo harías distinto.
- Si ves código muerto no relacionado, menciónalo — no lo borres.

Cuando tus cambios dejen huérfanos:
- Elimina imports/variables/funciones que TUS cambios dejaron sin uso.
- No elimines código muerto preexistente salvo que te lo pidan.

La prueba: cada línea cambiada debe trazar directo al pedido del usuario.

### 4. Ejecución guiada por objetivos

**Define criterios de éxito. Itera hasta verificar.**

Transforma tareas en objetivos verificables:
- "Agregar validación" → "Escribe tests para inputs inválidos, luego hazlos pasar"
- "Arreglar el bug" → "Escribe un test que lo reproduzca, luego hazlo pasar"
- "Refactorizar X" → "Asegura que los tests pasen antes y después"

Para tareas multi-paso, declara un plan breve:
```
1. [Paso] → verificar: [chequeo]
2. [Paso] → verificar: [chequeo]
3. [Paso] → verificar: [chequeo]
```

Criterios fuertes te dejan iterar de forma independiente. Criterios débiles
("haz que funcione") requieren aclaración constante.

### Excepción consciente a estos principios (NO simplificar)

El principio #2 prohíbe configurabilidad especulativa. Hay **una** desviación
deliberada, ya decidida con el usuario, que NO debe "simplificarse":

- **`ai_client.py` aísla toda llamada a Claude detrás de una función única**, para
  poder migrar de "key local" (Fase 2) a "proxy en Cloud Run" (Fase 3) cambiando
  una URL. Esto NO es flexibilidad especulativa: es una costura comercial pedida
  explícitamente (la app es una demo vendible). No elimines esta indirección
  argumentando simplicidad.

Cualquier OTRA flexibilidad no pedida sí cae bajo el principio #2 y debe evitarse.
