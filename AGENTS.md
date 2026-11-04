# Instrucciones del proyecto

Leer `/Users/rubenrodriguez/.codex/RTK.md` cuando exista. Su ausencia en otros equipos no bloquea el proyecto.

- Trabajar en español y mantener README.md y docs/ actualizados.
- Antes de añadir o cerrar funcionalidades, revisar docs/COBERTURA.md y sus referencias bibliográficas; no eliminar temas pendientes para aparentar cobertura.
- Distinguir siempre diseñado, implementado y verificado. No declarar operativa la aplicación mientras no exista.
- Registrar cambios en CHANGELOG.md, versión en VERSION y decisiones/dependencias en docs/VERSIONES.md. No inventar versiones instaladas o pruebas exitosas.
- Al terminar una unidad de trabajo, ejecutar `uv run python scripts/check_docs.py` y las pruebas pertinentes; usar `uv run python scripts/sync.py --message "tipo: descripción"` para crear commit y hacer push. El usuario ha autorizado commits y push automáticos.
- No usar force push, reset destructivo ni agregar los PDF, ZIP, datos privados o secretos. No cambiar el remoto a otro repositorio.
- Si falla autenticación o conexión, conservar el commit y comunicar el bloqueo; no declarar completado el push.

## Segundo cerebro

- El cerebro (`engine/quantlabs/brain`) solo compone nodos registrados en `packages/contracts/nodeCatalog.json`. No añadir ejecución de código generado ni nodos dinámicos.
- Para implementar una ficha de herramienta faltante: revisar `uv run python -m quantlabs.brain gaps --markdown`, implementar el cálculo en `engine/quantlabs/` (p. ej. `gap_tools.py`), registrar la ficha en el catálogo y en `project.schema.json`, añadir la intención en `brain/intents.py` y su consumidor en `MODEL_ACCEPTS` si produce o consume `FittedModel`, probar contra una referencia numérica y documentar en `docs/HERRAMIENTAS.md` y `docs/CEREBRO.md`.
- Las pruebas del cerebro aíslan memoria con `QL_BRAIN_DIR` y apuntan Ollama a un puerto cerrado; no deben depender de un modelo instalado.
