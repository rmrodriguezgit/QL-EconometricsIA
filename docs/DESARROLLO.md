# Desarrollo de la alpha 0.2.0

Fecha: 2026-11-01. Primer corte funcional de P1 con un adelanto OLS de P2. No equivale al cierre de ninguna fase curricular.

## Inicio local y estructura

`uv sync --frozen` crea .venv con Python 3.12 y las dependencias de uv.lock. `npm ci --prefix apps/desktop` instala exactamente package-lock.json. `python3 scripts/dev.py` inicia Vite en 127.0.0.1:1420. El navegador usa un puente de desarrollo que lanza Python por stdin/stdout para cada solicitud. Este puente solo está activo en desarrollo, comprueba origen/content-type y no se incluye en el build estático.

- `apps/desktop/src/`: interfaz React Flow, inspector, resultados y archivos JSON.
- `apps/desktop/vite.config.ts`: transporte local de desarrollo con timeout y límite de carga.
- `engine/quantlabs/`: registro de nodos, validación, ejecución y JSON-RPC.
- `packages/contracts/project.schema.json`: esquema público del documento.
- `examples/ingreso-consumo.json`: experimento reproducible.
- `apps/desktop/src-tauri/`: integración nativa preparada; no compilada por ausencia de Rust en el host.

## Flujo inicial

Ingreso uniforme entre 20 y 150; consumo = 12 + 0.72 × ingreso + ruido normal de desviación 9. Semilla 42, 120 observaciones. Las columnas tienen unidades monetarias simuladas. Descriptivos y OLS usan la misma muestra. Con las versiones bloqueadas, la pendiente estimada es aproximadamente 0.719027 y R² aproximadamente 0.888. Estos valores son una referencia de smoke test, no el objetivo que el motor fuerza.

El botón **Ecuación** abre una ventana accesible con modelo poblacional, recta ajustada y definición de símbolos. Con varios nodos OLS usa el seleccionado; en otro caso, el primero del proyecto. Se cierra con Escape, botón de cierre o clic en el fondo. Antes de ejecutar muestra la forma simbólica.

El usuario puede añadir fuentes y nodos, conectarlos, editar parámetros y ejecutar. OLS y dispersión permiten escribir los nombres de las columnas. Los resultados se invalidan al modificar parámetros o conexiones; mover nodos no cambia el cálculo. Los resultados mostrados de cada tipo corresponden al primer nodo exitoso de ese tipo; el inspector permite revisar todos los demás. No se permite conectar salidas OLS con otros nodos todavía.

## Contrato de ejecución real

Protocolo 1.0.0, esquema de proyecto 1.0.0 y versión de nodo 1.0.0. Métodos: engine.health, nodes.list, project.validate y run.start. JSON-RPC 2.0 delimitado por salto de línea, con id obligatorio; no se implementan notificaciones. El motor no evalúa expresiones de usuario. Rechaza versiones, referencias y puertos inválidos y entradas sin conectar antes de ejecutar.

Ejecución secuencial, sin progreso incremental, caché del DAG ni cancelación interactiva. Un nodo fallido marca sus descendientes skipped y conserva ramas independientes. El transporte mata la ejecución después de 60 segundos. Cada llamada inicia un proceso: la optimización a sidecar persistente queda pendiente.

Límites actuales: 100 nodos, 400 conexiones, fuentes de hasta 10.000 filas y 50 columnas, CSV de 2 MB, proyecto cargado de 3 MB, solicitud de 4 MB y respuesta de 12 MB. Estos límites sustituyen provisionalmente los objetivos superiores de la arquitectura. Se conservan faltantes; los descriptivos excluyen por columna y OLS/dispersión por pares completos, siempre con recuento visible.

## Banco Mundial

wbdata 1.1.0 usa el argumento `date`, comprobado contra su firma instalada. Se permite un país ISO 3 y un indicador anual por nodo; la columna numérica se llama `valor` y el año `periodo`. Orden cronológico ascendente. La consulta registra país, código, período y fecha, además del hash del snapshot. Las unidades aún necesitan consulta al catálogo externo; no se inventan ni se consideran verificadas en la interfaz.

La caché de wbdata se guarda en `.cache/wbdata/` en desarrollo, excluida de Git. Se usa una sesión con timeout de conexión/lectura de 5/12 segundos; el transporte impone 60 segundos totales. La biblioteca gestiona paginación y reintentos de conexión. No hay prueba de red obligatoria en CI. Se realizó una consulta real de MEX/NY.GDP.PCAP.KD para 2020-2023; no se versionan esos datos.

## Resultados y persistencia

El proyecto descargado incluye grafo, posiciones, parámetros, versión y CSV embebido cuando exista. Los resultados se recalculan al abrir. El archivo exportado de resultados contiene snapshots de todas las fuentes, coeficientes, inferencia, residuos y manifiesto. Las tablas fuente se serializan a JSON con 15 decimales; el hash identifica esa representación. Parquet de precisión nativa queda pendiente.

La huella de grafo representa nodos/parámetros y conexiones; excluye posiciones y título. Cada manifiesto registra versión, dependencias, semilla, plataforma, commit, fechas UTC y fuentes. No incluye todavía identidad del BLAS ni un almacenamiento consultable de ejecuciones. No hay autoguardado ni migración desde esquemas anteriores; versiones desconocidas se rechazan.

## Validación

Pruebas científicas con fixtures de coeficientes y errores estándar calculables a mano, faltantes, rango deficiente, reproducibilidad, aislamiento de fallos, CSV y protocolo stdio. El comprobador documental valida referencias y vínculos. TypeScript y Vite producen el build. CI instala locks y ejecuta estas verificaciones en macOS y Windows; no compila Tauri todavía.

## Escritorio nativo pendiente

Instalar Rust y los prerrequisitos oficiales de [Tauri](https://v2.tauri.app/start/prerequisites/). Con el servidor local detenido, `npm run tauri --prefix apps/desktop -- dev` usará Python de .venv mediante un comando Rust acotado. La configuración se ha preparado, pero requiere verificar compilación, iconos, permisos, descargas y archivos antes de declararla operativa.

La configuración de release añade `binaries/quantlabs-engine` mediante tauri.release.conf.json; no hay binario empaquetado. El entry point `scripts/engine_entry.py` queda preparado para PyInstaller, cuya adopción y lock todavía están pendientes. Faltan Cargo.lock, pruebas nativas por target, empaquetado científico, firma y notarización. No hay instaladores disponibles.

Fuentes técnicas consultadas: [React Flow](https://reactflow.dev/learn), [Tauri: comandos](https://v2.tauri.app/develop/calling-rust/), [statsmodels OLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) y [wbdata](https://wbdata.readthedocs.io/en/stable/), 2026-11-01.
