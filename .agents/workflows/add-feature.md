# Workflow: add-feature

Flujo para añadir una feature al CRM siguiendo TDD y Gitflow. Invocar con `/add-feature`.

## Pasos

1. **Entender la feature.** Pregunta al usuario qué feature quiere si no está claro.
   Resume en una frase qué hará y qué pantalla/ruta toca.

2. **Crear rama.** `git checkout -b feature/<nombre-corto>` desde `develop`.

3. **Escribir el test que falla primero (TDD).**
   - Añade el/los test(s) en `tests/` usando el fixture `client` (SQLite in-memory).
   - Ejecuta `pytest tests/ -v` y confirma que el nuevo test FALLA por la razón correcta.

4. **Implementar lo mínimo para pasar el test.**
   - Backend: respeta `.agents/rules/python-fastapi.md`. Rutas finas, lógica en servicios.
   - Frontend: respeta `.agents/rules/htmx-tailwind.md`. Fragmentos HTML para HTMX.
   - Si toca IA: consulta la skill `ai-integration` y pasa por `ai_client.py`.

5. **Verde y refactor.**
   - `pytest tests/ -v` hasta que pase todo.
   - Refactoriza con los tests en verde. No dupliques `ETAPAS`.

6. **Prueba manual en dev.**
   - Arranca en modo desarrollo y verifica la feature en la ventana/navegador de dev.
   - Confirma que los mensajes visibles están en español y son comprensibles.

7. **Commit y PR.**
   - Commits pequeños y descriptivos. PR de `feature/<nombre>` hacia `develop`.

## Recordatorios

- La IA es aditiva: nunca debe poder romper el CRM.
- Cero fricción técnica para el usuario final.
- No fijes el puerto en 8000; usa puerto libre.
