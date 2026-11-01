# Quantlabs-Econometrics

Laboratorio educativo de econometría con programación visual mediante nodos y motor analítico Python. Objetivo de escritorio: macOS y Windows. [Repositorio](https://github.com/rmrodriguezgit/Quantlabs-Econometrics).

**Versión 0.2.1 · 2026-11-01 · Alpha funcional en modo de desarrollo local. Integración Tauri preparada, sin compilar todavía.**

## Arrancar

Requisitos de desarrollo: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js 22 y npm. Desde la raíz:

```sh
uv sync --frozen
npm ci --prefix apps/desktop
python3 scripts/dev.py
```

Abre [el laboratorio local](http://127.0.0.1:1420) y pulsa **Ejecutar flujo**. En Windows usa `python` en lugar de `python3`. El servidor queda ligado a loopback; Ctrl+C lo detiene. `npm run preview` solo muestra el build estático y no ejecuta el motor: para trabajar usa el comando de desarrollo.

## Ya funciona

- Canvas editable con conexiones, seis tipos de nodo, eliminación, zoom y deshacer. Desconecta enlaces desde el inspector o seleccionando su línea y pulsando **Desconectar**.
- Datos sintéticos con semilla, CSV local y consulta anual de un indicador/país del Banco Mundial. Lista desplegable con búsqueda en el catálogo completo de indicadores y selección automática de su fuente.
- Descriptivos, dispersión y regresión OLS simple con covarianza clásica o HC3.
- Ventana **Ecuación** con fórmula poblacional y recta ajustada con los coeficientes calculados.
- Tabla de coeficientes, errores estándar, p-valores, R² y muestra efectiva.
- Guardar y abrir proyectos JSON; exportar resultados, snapshots de datos y manifiesto con versiones y huellas.
- Validación de grafo y tipos; errores por nodo y omisión de ramas dependientes.

El ejemplo [ingreso-consumo.json](examples/ingreso-consumo.json) se incluye al abrir. Los cálculos se ejecutan en Python; no hay resultados simulados por la interfaz. El nodo de datos sintéticos sí genera una muestra artificial identificada como tal.

## Límites de esta alpha

P1 sigue abierta. Faltan instaladores nativos, Excel, más indicadores simultáneos, unidades editables, limpieza/transformaciones, almacenamiento Parquet/SQLite, caché del DAG, cancelación y lecciones completas. OLS es una primera implementación de P2; no completa su módulo curricular. Hay 36 capítulos inventariados y 28 módulos planificados. La cobertura bibliográfica es una guía de implementación, no una lista de funciones disponibles.

Los proyectos guardados incluyen el contenido de CSV importados. Los resultados exportados incluyen datos de la ejecución; se guardan solo al solicitarlos. No existe autoguardado ni recuperación después de cerrar la pestaña: descarga el proyecto antes de salir. Los PDF, ZIP, datasets y cachés no se publican en Git.

## Verificar y publicar cambios

```sh
uv run python scripts/check_docs.py
uv run python -m unittest discover -s tests -v
npm run build --prefix apps/desktop
uv run python scripts/sync.py --message "feat: describir la unidad terminada"
```

El último comando valida documentación, pruebas y frontend, incorpora rutas permitidas, crea commit si hay cambios y hace push a `origin main`. Repetirlo después de un push fallido no duplica commits. [AGENTS.md](AGENTS.md) conserva esta instrucción para futuras sesiones; no hay tarea en segundo plano.

## Documentación

| Archivo | Contenido |
|---|---|
| [Desarrollo](docs/DESARROLLO.md) | Ejecución, protocolo, pruebas y límites actuales |
| [Arquitectura](docs/ARQUITECTURA.md) | Diseño de capas, IPC, DAG, datos y distribución |
| [Bibliografía](docs/BIBLIOGRAFIA.md) | Inventario verificable de 36 capítulos |
| [Cobertura](docs/COBERTURA.md) | Temas, referencias y avance por módulo |
| [Plan](docs/ROADMAP.md) | Entregables por versión y estado de fases |
| [Versiones](docs/VERSIONES.md) | Versiones observadas, adoptadas y pendientes |
| [Versionado](docs/VERSIONADO.md) | Commits, push y recuperación |
| [Cambios](CHANGELOG.md) | Historial de entregas |
