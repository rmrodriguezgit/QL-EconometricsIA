# Desarrollo de la alpha 0.4.0

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

El usuario puede añadir fuentes y nodos, conectarlos, editar parámetros y ejecutar. OLS y dispersión permiten escribir los nombres de las columnas. La sección Conexiones del inspector permite desconectar cada enlace. Al seleccionar una línea aparece un botón Desconectar en el canvas; también se conserva la eliminación con el teclado. Deshacer recupera el enlace. Desconectar no elimina nodos.

Los resultados se invalidan al modificar parámetros o conexiones; mover nodos no cambia el cálculo. Los resultados mostrados de cada tipo corresponden al primer nodo exitoso de ese tipo; el inspector permite revisar todos los demás. No se permite conectar salidas OLS con otros nodos todavía.

## Contrato de ejecución real

Protocolo 1.0.0, esquema de proyecto 1.0.0 y versión de nodo 1.0.0. Métodos: engine.health, nodes.list, project.validate, run.start, worldbank.indicators, examples.list/read, projects.list/read/save/delete/restore y system.audit. JSON-RPC 2.0 delimitado por salto de línea, con id obligatorio; no se implementan notificaciones. El motor no evalúa expresiones de usuario. Rechaza versiones, referencias y puertos inválidos y entradas sin conectar antes de ejecutar.

Ejecución secuencial, sin progreso incremental, caché del DAG ni cancelación interactiva. Un nodo fallido marca sus descendientes skipped y conserva ramas independientes. El transporte mata la ejecución después de 60 segundos. Cada llamada inicia un proceso: la optimización a sidecar persistente queda pendiente.

Límites actuales: 100 nodos, 400 conexiones, fuentes de hasta 10.000 filas y 50 columnas, CSV de 2 MB, proyecto cargado de 3 MB, solicitud de 4 MB y respuesta de 12 MB. Estos límites sustituyen provisionalmente los objetivos superiores de la arquitectura. Se conservan faltantes; los descriptivos excluyen por columna y OLS/dispersión por pares completos, siempre con recuento visible.

## Banco Mundial

wbdata 1.1.0 usa el argumento `date`, comprobado contra su firma instalada. Se permite un país ISO 3 y un indicador anual por nodo; la fuente se registra y envía explícitamente a wbdata (2 por defecto para proyectos previos); la columna numérica se llama `valor` y el año `periodo`. Orden cronológico ascendente. La consulta registra país, código, período y fecha, además del hash del snapshot. Las unidades aún necesitan consulta al catálogo externo; no se inventan ni se consideran verificadas en la interfaz.

La caché de wbdata se guarda en `.cache/wbdata/` en desarrollo, excluida de Git. Se usa una sesión con timeout de conexión/lectura de 5/12 segundos; el transporte impone 60 segundos totales. La biblioteca gestiona paginación y reintentos de conexión. No hay prueba de red obligatoria en CI. Se realizó una consulta real de MEX/NY.GDP.PCAP.KD para 2020-2023; no se versionan esos datos.

## Resultados y persistencia

El proyecto guardado o exportado incluye grafo, posiciones, parámetros, versión y CSV embebido cuando exista. El administrador guarda una envoltura con UUID, título, fechas, revisión SHA-256 y documento del proyecto en .quantlabs/projects/files; delete lo mueve a trash y restore lo recupera. Los resultados se recalculan al abrir. El archivo exportado de resultados contiene snapshots de todas las fuentes, coeficientes, inferencia, residuos y manifiesto. Las tablas fuente se serializan a JSON con 15 decimales; el hash identifica esa representación. Parquet de precisión nativa queda pendiente.

La huella de grafo representa nodos/parámetros y conexiones; excluye posiciones y título. Cada manifiesto registra versión, dependencias, semilla, plataforma, commit, fechas UTC y fuentes. No incluye todavía identidad del BLAS ni un almacenamiento consultable de ejecuciones. No hay autoguardado; hay advertencia de cambios pendientes. Los proyectos 1.0.0 anteriores siguen admitidos con parámetros por defecto. No hay migración desde otros esquemas; versiones desconocidas se rechazan.

## Validación

Pruebas científicas con fixtures de coeficientes y errores estándar calculables a mano, faltantes, rango deficiente, reproducibilidad, aislamiento de fallos, CSV y protocolo stdio. El comprobador documental valida referencias y vínculos. TypeScript y Vite producen el build. CI instala locks y ejecuta estas verificaciones en macOS y Windows; no compila Tauri todavía.

## Escritorio nativo pendiente

Instalar Rust y los prerrequisitos oficiales de [Tauri](https://v2.tauri.app/start/prerequisites/). Con el servidor local detenido, `npm run tauri --prefix apps/desktop -- dev` usará Python de .venv mediante un comando Rust acotado. La configuración se ha preparado, pero requiere verificar compilación, iconos, permisos, descargas y archivos antes de declararla operativa.

La configuración de release añade `binaries/quantlabs-engine` mediante tauri.release.conf.json; no hay binario empaquetado. El entry point `scripts/engine_entry.py` queda preparado para PyInstaller, cuya adopción y lock todavía están pendientes. Faltan Cargo.lock, pruebas nativas por target, empaquetado científico, firma y notarización. No hay instaladores disponibles.

Fuentes técnicas consultadas: [React Flow](https://reactflow.dev/learn), [Tauri: comandos](https://v2.tauri.app/develop/calling-rust/), [statsmodels OLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html) y [wbdata](https://wbdata.readthedocs.io/en/stable/), 2026-11-01.

## Catálogo de indicadores (0.2.1)

El campo Código de indicador abre un desplegable con búsqueda por nombre, código o fuente. La búsqueda ignora mayúsculas y acentos; los resultados se muestran en páginas de 100 entradas. Se puede navegar con teclado y seleccionar indicadores conservando su fuente. La API devuelve 29.544 filas en la consulta inicial; al deduplicar por fuente/código se obtuvieron 29.533 entradas. No se limita a una selección manual de indicadores populares.

El motor descarga todas las páginas de https://api.worldbank.org/v2/es/indicator, valida que el número total coincida y guarda `indicators-es-v1.json` junto a la caché de wbdata. Vigencia: 24 horas. La escritura es atómica; un fallo parcial nunca sustituye un catálogo válido. Si falla la actualización, se usa la copia anterior y se indica en pantalla. La primera carga necesita conexión. Los metadatos y la caché no se incorporan al repositorio.

`worldbank.indicators` recibe query, page y refresh (opcional), y devuelve items, total, catalog_total, page, pages, retrieved_at y stale. Los códigos y las fuentes distintos se preservan incluso cuando comparten nombre. Seleccionar una entrada actualiza indicador y fuente en una sola operación reversible. La aparición en catálogo no garantiza observaciones para el país/período, ni compatibilidad con la frecuencia anual de esta alpha.

Referencia oficial: [consultas de indicadores](https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries), consultada el 2026-11-01.

## Administrador local y recetas 0.3.0

**Archivos y ejemplos** abre una ventana de administración con catálogo, archivos propios, papelera, editor JSON y auditoría. El botón Guardar del canvas guarda en el administrador; la descarga JSON permanece como Exportar JSON dentro del editor. La selección del archivo activo conserva su revisión para impedir sobrescribir ediciones de otra sesión. Guardar copia crea un UUID nuevo, sin modificar el original. Editar title en JSON permite renombrar al guardar.

Las operaciones no aceptan rutas arbitrarias: solo UUID canónicos, dentro del espacio local. Los archivos dañados aparecen como no legibles y se conservan. La escritura usa temporal, fsync y os.replace, y un bloqueo entre procesos serializa mutaciones. Las revisiones obsoletas producen FILE_CONFLICT. Borrar es recuperable y no expone una operación de purga permanente. El directorio queda excluido de Git. Un JSON externo inválido puede cargarse en el editor para corregirlo, pero no se aplica al canvas ni se guarda en la biblioteca hasta superar la validación.

`project.validate` acepta draft=true para guardar y aplicar estructuras incompletas, incluido un canvas vacío. La ejecución conserva sus requisitos estrictos. El esquema JSON describe documentos de edición; tener un documento válido no garantiza que todos sus puertos estén conectados.

Los 28 ejemplos usan un nodo experiment con topic C01-C28, n y seed. Se ejecuta una función registrada, nunca eval/exec de texto de usuario. El reporte muestra métricas, tablas, series, advertencias, interpretación y alcance. El catálogo se puede buscar por título, temas, ID y referencia bibliográfica. Las recetas avanzadas no exponen aún todas sus opciones como nodos del canvas.

`system.audit` valida los 28 documentos, cuenta referencias, prueba escritura con un archivo temporal y comprueba archivos guardados/papelera. Informa pendientes de currículo, ejecución y empaquetado. No ejecuta los 28 modelos al abrir la auditoría ni afirma una certificación de seguridad.

## Herramientas y ejecución guiada 0.4.0

El registro compartido [nodeCatalog.json](../packages/contracts/nodeCatalog.json) contiene 53 tipos, puertos, parámetros por defecto, categorías, referencias y opciones. 49 se usan en los ejemplos; simulate, csv y worldbank también pueden actuar como fuentes alternativas y experiment permanece para compatibilidad. Se incluyen 131 pasos explicativos en los 28 proyectos.

Los puertos no se reducen a data: split devuelve train/test, standardize devuelve data/transformer, los estimadores devuelven model/result y report recibe result. Los objetos ajustados son artefactos privados del proceso; la respuesta JSON contiene sus resultados numéricos, no objetos Python serializados. Cada tabla de salida tiene vista previa y huella registrada.

`run.start` acepta target_node opcional. Sin él ejecuta todo el DAG válido. Con él valida la estructura completa y ejecuta únicamente el nodo y sus ancestros; las entradas faltantes de ramas ajenas no bloquean ese paso. No omite ciclos o estructuras inválidas. El manifiesto incluye target_node y execution_order.

La guía selecciona y enfoca cada nodo, muestra Qué debes observar y permite ejecutar hasta él. El resultado visible corresponde al nodo seleccionado. Los pasos recalculan dependencias. Al acumular resultados, el frontend comprueba igualdad de grafo y huellas compartidas y registra guided_runs; si cambia un dato común, no conserva resultados incompatibles. Editar el proyecto invalida el estado de cálculo.

Los estimadores consumen siempre las tablas conectadas. No regeneran datos según un ID de tema. Los generadores sí simulan escenarios registrados y muestran su ecuación y supuestos. La red neuronal recibe datos ya escalados por otra herramienta; el escalador de prueba no vuelve a ajustarse. El evaluador recibe un modelo y la tabla de prueba y no hace fit.

Las herramientas temporales revisan período numérico regular cuando existe la columna periodo; no comprimen faltantes internos al estimar series. Frecuencias, fechas y paneles generales requieren herramientas adicionales, que se explicitan en los pendientes. No se imputan ni eliminan períodos para hacer pasar una estimación.

La interfaz impide ciclos, tipos incompatibles y conexiones duplicadas al dibujar. El backend vuelve a comprobarlos. Los errores numéricos esperables se presentan como ESTIMATION_ERROR. Los formatos de nodo/proyecto anteriores siguen admitidos.

## Electron y estudio 0.5.0

La ruta recomendada de escritorio usa `npm run desktop --prefix apps/desktop`; para HMR arrancar Vite y `npm run desktop:dev --prefix apps/desktop`. El build estático se comunica con Python por IPC nativo. Ejecutar `npm run test:desktop --prefix apps/desktop` para ciclo de vida y validación del puente. [Guía Electron](ELECTRON.md).

## Consulta World Bank y Dispersión (0.5.2)

Las salidas son periodo y valor: usar esos ejes o el botón del inspector. Una caché shelve compartida produjo SystemError al importar wbdata; wb_client.client aísla importación y cliente en una carpeta temporal exclusiva del proceso. El catálogo de indicadores conserva su almacenamiento JSON y los archivos anteriores no se borran. Los datos se vuelven a descargar por proceso; los resultados exportados conservan su procedencia.

## Variables de entrada (0.5.3)

El motor publica numeric_columns por salida Dataset, incluso cuando hay faltantes. OLS y Dispersión presentan selectores X/Y; regresores, instrumentos y conjuntos de columnas usan casillas. El resto de campos de columnas usa listas. Cargar columnas ejecuta la fuente inmediata y sus dependencias, incluso si el modelo todavía no está configurado.

Las vistas previas se identifican por fuente/puerto y firma de todos sus ancestros y parámetros; no dependen de la selección X/Y ni de la posición visual. Cambiar indicador, país, años, transformaciones o enlace invalida el esquema previo. Todo cambio de parámetros retira los resultados calculados. Un indicador World Bank conserva las columnas periodo/valor, pero representa otra serie: hay que volver a ejecutar. OLS con periodo/valor es una tendencia temporal, no una regresión entre dos indicadores. Unir indicadores en una tabla sigue pendiente.

La elección de indicador persiste nombre/unidad/fuente como metadatos; código y texto pueden ocupar varias líneas y no usan puntos suspensivos. Los proyectos previos siguen funcionando aunque aún no tengan esos nombres guardados.

El código del indicador es un botón que abre un diálogo modal nativo en la capa superior. Conserva la selección actual, nombres largos y fuente durante la búsqueda; Escape o Cerrar devuelven al inspector, y elegir una opción actualiza el proyecto.

## Catálogo de países y favoritos (0.5.4)

CountryPicker usa packages/contracts/worldbankCountries.json: 296 entradas oficiales, 217 países/economías y 79 regiones/agregados. La búsqueda local ignora acentos y distingue código ISO 3, ISO 2, nombre y región; por defecto se ocultan agregados. Activar la casilla permite verlos.

Las estrellas se guardan en localStorage bajo quantlabs-worldbank-favorite-countries-v1. Se comparten entre proyectos del mismo perfil/origen y se conservan al recargar o reiniciar Electron. Navegador y Electron tienen almacenes separados. No se sincronizan con Git ni entre equipos. Marcar/desmarcar favorito no cambia parámetros, datos ni resultados; elegir otro país sí invalida resultados y requiere recalcular. Las búsquedas filtran también favoritos; los que coinciden se muestran primero.

Preferencias corruptas o códigos desconocidos se descartan. Si falla el almacenamiento se informa y no se promete persistencia. El catálogo funciona sin red; descargar observaciones sigue requiriendo conexión y disponibilidad para país/indicador/período.

Actualizar metadatos con `.venv/bin/python scripts/update_countries.py`; valida páginas, cantidad y códigos antes de reemplazar atómicamente el archivo. Fuente: [API oficial de países en español](https://api.worldbank.org/v2/es/country?format=json&per_page=400). La revisión/hora se registra en el propio catálogo.

## Histograma y salidas por nodo (0.5.5)

La entrada data debe contener la columna numérica seleccionada. El motor excluye faltantes y calcula los intervalos con numpy.histogram (último intervalo incluye límite derecho). Devuelve los mismos límites/frecuencias para barras y tabla; no recalcula bins en el frontend. Seleccionar Histograma abre Resultados en un proyecto libre o guiado. Modelos y transformaciones adicionales usan NodeOutput al seleccionarlos.
