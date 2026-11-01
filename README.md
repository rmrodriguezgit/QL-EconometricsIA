# Quantlabs-Econometrics

Aplicación educativa de econometría para macOS y Windows, con programación visual mediante nodos y motor analítico Python. Repositorio: https://github.com/rmrodriguezgit/Quantlabs-Econometrics.

**Versión 0.1.0 · 2026-11-01 · Estado: arquitectura y planificación; aplicación aún no implementada.**

El diseño usa los 36 capítulos locales de tres obras como base curricular. Cada capítulo tiene identificador, huella SHA-256 y relación con módulos y fases. Tener cobertura planificada no equivale a tener una funcionalidad implementada.

## Documentación

| Archivo | Contenido |
|---|---|
| [Arquitectura](docs/ARQUITECTURA.md) | Capas, IPC, DAG, nodos, datos, seguridad, interfaz y distribución |
| [Bibliografía](docs/BIBLIOGRAFIA.md) | Inventario verificable de 36 capítulos, libros y limitaciones |
| [Cobertura](docs/COBERTURA.md) | Temas, nodos, referencias, fases y aceptación |
| [Plan](docs/ROADMAP.md) | Entregables y criterios por versión |
| [Versiones](docs/VERSIONES.md) | Versiones propuestas, observadas y pendientes de fijar |
| [Versionado](docs/VERSIONADO.md) | Commits, push, sincronización automática y recuperación |
| [Cambios](CHANGELOG.md) | Historial de entregas |

## Verificación y sincronización

Solo se necesita Python 3.11+ y Git para las herramientas documentales; no se instalan dependencias de la aplicación en esta entrega.

```sh
python3 scripts/check_docs.py
python3 -m unittest discover -s tests -v
python3 scripts/sync.py --message "docs: actualizar arquitectura y cobertura"
```

El último comando verifica documentación, incorpora únicamente rutas del proyecto permitidas, crea un commit si hay cambios y hace push a `origin main`. En Windows puede utilizarse `python` en lugar de `python3`. Un push fallido conserva el commit local. No se fuerza ni se sobrescribe historia remota.

## Política de trabajo

Cada unidad de trabajo terminada debe actualizar su documentación y versiones, ejecutar verificaciones y concluir con commit y push. [AGENTS.md](AGENTS.md) conserva esta instrucción para futuras sesiones. El script ejecuta ese cierre automáticamente al invocarlo; no hay vigilancia en segundo plano ni tareas programadas instaladas.

Los PDF y el ZIP permanecen en la carpeta local de bibliografía y están excluidos de Git. Los datos descargados, resultados privados y credenciales tampoco se publican. Los manifiestos de ejecución conservarán hashes y procedencia sin requerir subir los datos.
