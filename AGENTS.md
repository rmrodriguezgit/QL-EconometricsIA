# Instrucciones del proyecto

Leer `/Users/rubenrodriguez/.codex/RTK.md` cuando exista. Su ausencia en otros equipos no bloquea el proyecto.

- Trabajar en español y mantener README.md y docs/ actualizados.
- Antes de añadir o cerrar funcionalidades, revisar docs/COBERTURA.md y sus referencias bibliográficas; no eliminar temas pendientes para aparentar cobertura.
- Distinguir siempre diseñado, implementado y verificado. No declarar operativa la aplicación mientras no exista.
- Registrar cambios en CHANGELOG.md, versión en VERSION y decisiones/dependencias en docs/VERSIONES.md. No inventar versiones instaladas o pruebas exitosas.
- Al terminar una unidad de trabajo, ejecutar `uv run python scripts/check_docs.py` y las pruebas pertinentes; usar `uv run python scripts/sync.py --message "tipo: descripción"` para crear commit y hacer push. El usuario ha autorizado commits y push automáticos.
- No usar force push, reset destructivo ni agregar los PDF, ZIP, datos privados o secretos. No cambiar el remoto a otro repositorio.
- Si falla autenticación o conexión, conservar el commit y comunicar el bloqueo; no declarar completado el push.
