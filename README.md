# Quantlabs · Econometrics IA

**Describe tu análisis. El segundo cerebro construye el blueprint. Tú compruebas cada resultado.**

[![Versión](https://img.shields.io/badge/versión-0.15.0-6cc9ac)](VERSION)
[![Cerebro IA](https://img.shields.io/badge/cerebro-Qwen%20local%20%2B%20RAG-c49af8)](docs/CEREBRO.md)
[![Escritorio](https://img.shields.io/badge/escritorio-macOS%20%7C%20Windows-79b4ef)](docs/ARRANQUE.md)
[![Electron](https://img.shields.io/badge/Electron-45.2.1-79b4ef)](apps/desktop/package.json)
[![React](https://img.shields.io/badge/React-19.3.1-61dafb)](apps/desktop/package.json)
[![TypeScript](https://img.shields.io/badge/TypeScript-7.0.2-3178c6)](apps/desktop/package.json)
[![Python](https://img.shields.io/badge/Python-3.12-ffd343)](pyproject.toml)
[![Herramientas](https://img.shields.io/badge/nodos-89-c49af8)](docs/HERRAMIENTAS.md)
[![Recorridos](https://img.shields.io/badge/recorridos-28-c49af8)](docs/EJEMPLOS.md)
[![Wooldridge](https://img.shields.io/badge/Wooldridge-115%20datasets-6cc9ac)](docs/WOOLDRIDGE.md)

Laboratorio educativo de econometría con programación visual mediante nodos, motor analítico Python y un **segundo cerebro de IA local** que convierte enunciados en flujos conectados y verificados. Objetivo de escritorio: macOS y Windows. [Repositorio](https://github.com/rmrodriguezgit/QL-EconometricsIA) · derivado de [Quantlabs-Econometrics](https://github.com/rmrodriguezgit/Quantlabs-Econometrics) con su historial completo.

**Versión 0.15.0 · 2026-11-05 · Alpha local con escritorio Electron, estudio oscuro y segundo cerebro (Ollama/Qwen + reglas). Instaladores independientes y actualización automática pendientes.**

## Segundo cerebro IA

Pulsa **Cerebro IA** en la barra del lienzo y escribe lo que quieres analizar, por ejemplo: *«Analiza la inflación de México 2000-2023 del Banco Mundial con gráfico temporal, raíz unitaria y ARIMA»*.

1. **Recupera** herramientas, recorridos y blueprints valorados con BM25 local.
2. **Planifica** con Qwen vía Ollama en `127.0.0.1` o, si no está disponible, con un planificador determinista en español.
3. **Compila** el plan con la mecánica de los recorridos: solo nodos del catálogo, parámetros declarados, puertos tipados y validador DAG del motor.
4. **Verifica** ejecutando el flujo cuando los datos son locales y repara columnas con las vistas previas reales.
5. **Registra** lo que falta como ficha de herramienta pendiente, sin simularlo ni generar código.

```sh
ollama pull qwen3.5:4b                         # opcional: sin modelo se usan reglas
uv run python -m quantlabs.brain plan "Regresión múltiple con diagnóstico de heterocedasticidad" -o blueprint.json
```

Guía completa, métodos RPC, variables de entorno y límites: [CEREBRO.md](docs/CEREBRO.md).

## Abrir en el escritorio

| macOS | Windows |
|---|---|
| Doble clic en **[Arrancar-Quantlabs.command](Arrancar-Quantlabs.command)** | Doble clic en **[Arrancar-Quantlabs.cmd](Arrancar-Quantlabs.cmd)** |

**Preparación inicial:** instala [Node.js 22 o posterior](https://nodejs.org/) (incluye npm) y [uv](https://docs.astral.sh/uv/getting-started/installation/). Descarga o clona este repositorio completo y conserva el arrancador en su raíz. Si descargas un ZIP, extráelo antes de abrirlo. En macOS, clonar con Git conserva el permiso ejecutable; si una descarga lo pierde, ejecuta una vez `chmod +x Arrancar-Quantlabs.command` desde la carpeta del proyecto.

El arrancador prepara Python 3.12 con `uv sync --frozen --python 3.12`, instala las dependencias del escritorio cuando faltan o cambia su configuración, construye la interfaz actual y abre Electron. El primer arranque necesita conexión y puede tardar varios minutos. Los siguientes reutilizan dependencias; no descargan cambios del repositorio. Para actualizar el código, usa `git pull` y vuelve a abrir el arrancador.

La terminal muestra el progreso y conserva el error si el arranque falla. Usa **Salir por completo** para cerrar ventanas y procesos del motor. Los proyectos se guardan localmente; pulsa **Guardar** antes de salir. Estos son arrancadores del código fuente: **los instaladores independientes siguen pendientes**. [Detalles y estado de verificación](docs/ARRANQUE.md).

### Desarrollo en Electron con recarga

```sh
npm run desktop:dev --prefix apps/desktop
```

o doble clic en **[Arrancar-Quantlabs-Dev.command](Arrancar-Quantlabs-Dev.command)** (macOS). La interfaz se recarga en caliente al editar, el motor Python toma los cambios en el siguiente cálculo y Electron se reinicia solo si cambian sus archivos principales. Al salir (Cmd/Ctrl+Q, cerrar la ventana, Ctrl+C o cerrar la terminal) no queda ningún proceso en memoria. [Detalles](docs/ELECTRON.md#modo-desarrollo-con-recarga-0111).

### Desarrollo en navegador

```sh
uv sync --frozen --python 3.12
npm ci --prefix apps/desktop
uv run python scripts/dev.py
```

Abre [el laboratorio local](http://127.0.0.1:1420) y pulsa **Ejecutar flujo**. Ctrl+C detiene el servidor ligado a loopback. `npm run preview` solo muestra el build estático; no ejecuta el motor.

## Ya funciona

- **Segundo cerebro IA**: enunciado → blueprint conectado, verificado por ejecución y con guía paso a paso; Qwen local con respaldo determinista, memoria valorable y cola de herramientas faltantes. [Guía](docs/CEREBRO.md).
- **Archivos y ejemplos**: 28 recorridos construidos con herramientas conectadas, uno por módulo, con objetivos y referencias a los 36 capítulos. Cada nodo tiene un paso explicativo.
- **Guía paso a paso**: instrucciones, resultado esperado, ejecución de dependencias, inspección de salidas, Anterior/Siguiente y vista del flujo completo.
- **Herramientas reutilizables**: 89 tipos registrados (incluida compatibilidad anterior; 17 nuevos en 0.10–0.11 desde las fichas del cerebro; Banco Mundial multi-indicador y pairplot en 0.13.0; nueve multivariadas en 0.14.0); 49 tipos se utilizan en los 28 recorridos, con 131 pasos explicados, más el recorrido aplicado R01 (22 pasos, datos reales de EE. UU.). La biblioteca se filtra en **Univariadas** y **Multivariadas**. **Unir series por período** y **Comparar modelos** tienen un botón **+** en la tarjeta para añadir entradas (hasta 8 series o 6 modelos) y **−** para quitar la última.
- **Mis proyectos**: guardar, abrir, editar JSON, validar, ejecutar, duplicar y exportar. Borrar mueve a una papelera restaurable.
- **Auditoría** dentro del administrador: comprueba catálogo, referencias, almacenamiento e integridad y muestra los pendientes.

- Canvas editable con conexiones, puertos tipados para tablas, modelos, transformadores y resultados, eliminación, zoom y deshacer. Desconecta enlaces desde el inspector o seleccionando su línea y pulsando **Desconectar**.
- Datos sintéticos con semilla, CSV local y consulta anual de un indicador/país del Banco Mundial. Lista desplegable con búsqueda en el catálogo completo de indicadores y selección automática de su fuente.
- Descriptivos, dispersión y regresión OLS simple con covarianza clásica o HC3.
- Ventana **Ecuación** con fórmula poblacional y recta ajustada con los coeficientes calculados.
- Tabla de coeficientes, errores estándar, p-valores, R² y muestra efectiva.
- Guardar y abrir borradores/proyectos JSON; exportar resultados, snapshots de datos y manifiesto con versiones y huellas.
- Validación de grafo y tipos; errores por nodo y omisión de ramas dependientes.

El ejemplo [ingreso-consumo.json](examples/ingreso-consumo.json) se incluye al abrir. Los cálculos se ejecutan en Python; no hay resultados simulados por la interfaz. El nodo de datos sintéticos sí genera una muestra artificial identificada como tal.

## Límites de esta alpha

Las fases curriculares siguen abiertas. Hay un experimento introductorio ejecutable para cada uno de los 28 módulos; esto no completa todos sus subtemas. Los ejemplos ya no utilizan una receta autónoma: los generadores, transformaciones, estimadores, diagnósticos y reportes son nodos separados. Los estimadores o subtemas aún no disponibles se enumeran en cada guía y en HERRAMIENTAS.md. Faltan instaladores nativos, Excel, panel, GARCH multivariado, GMM general, almacenamiento Parquet/SQLite, caché del DAG, cancelación y lecciones completas. Consulta la auditoría para distinguir lo corregido de lo pendiente.

Los proyectos guardados incluyen el contenido de CSV importados. Los resultados exportados incluyen datos de la ejecución; se guardan solo al solicitarlos. El botón Guardar incorpora el proyecto a **Mis proyectos**, en `.quantlabs/projects/` local (excluida de Git). No existe autoguardado: guarda antes de salir. El editor JSON avisa al descartar cambios y el canvas avisa al cerrar con cambios pendientes. Los proyectos guardados pueden reabrirse; la papelera permite recuperar los borrados. Los PDF, ZIP, datasets y cachés no se publican en Git.

## Seguir un recorrido

Abre **Archivos y ejemplos → Ejemplos**, elige un módulo y pulsa **Abrir en canvas**. Lee el paso, pulsa **Ejecutar hasta este paso**, inspecciona su salida y continúa con **Siguiente**. Los pasos recalculan únicamente sus dependencias; no ejecutan nodos posteriores. Puedes cambiar parámetros, desconectar herramientas y guardar tu propia variante.

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
| [Segundo cerebro](docs/CEREBRO.md) | Enunciado → blueprint: RAG, Ollama/Qwen, compilador, verificación y fichas faltantes |
| [Herramientas y pendientes](docs/HERRAMIENTAS.md) | Registro de puertos, uso por módulo y carencias identificadas |
| [Catálogo de ejemplos](docs/EJEMPLOS.md) | Los 28 experimentos y sus archivos JSON |
| [Auditoría](docs/AUDITORIA.md) | Hallazgos, correcciones y pendientes verificables |
| [Desarrollo](docs/DESARROLLO.md) | Ejecución, protocolo, pruebas y límites actuales |
| [Arquitectura](docs/ARQUITECTURA.md) | Diseño de capas, IPC, DAG, datos y distribución |
| [Bibliografía](docs/BIBLIOGRAFIA.md) | Inventario verificable de 36 capítulos |
| [Cobertura](docs/COBERTURA.md) | Temas, referencias y avance por módulo |
| [Plan](docs/ROADMAP.md) | Entregables por versión y estado de fases |
| [Versiones](docs/VERSIONES.md) | Versiones observadas, adoptadas y pendientes |
| [Versionado](docs/VERSIONADO.md) | Commits, push y recuperación |
| [Cambios](CHANGELOG.md) | Historial de entregas |

## Revisar a pantalla completa (0.12.0)

El botón **Ampliar** de la barra del lienzo extiende el espacio de trabajo a toda la ventana para revisar el grafo; el botón **Ampliar** de la cabecera de resultados hace lo mismo con Resultados, Regresión, Descriptivos y Trazabilidad. **Volver al layout** o `Esc` restauran la disposición normal. [Detalles](docs/ELECTRON.md#espacio-de-trabajo-a-pantalla-completa-0120).

## Escritorio Electron (0.5.0)

Ejecutar `npm run desktop --prefix apps/desktop` después de `uv sync` y `npm ci --prefix apps/desktop`. Incluye recargar, reiniciar, salir por completo y consultar GitHub Releases; el motor Python no queda residente. Interfaz inspirada en Quantlabs-Blueprints y recta OLS amarilla brillante. Instrucciones y límites: [ELECTRON.md](docs/ELECTRON.md).

Para empezar de cero, usa **Nuevo proyecto** en la barra del canvas. El flujo vacío explica los primeros pasos y ofrece añadir datos simulados; si hay cambios sin guardar, pide confirmación antes de sustituirlos.

Banco Mundial → Dispersión: configurar `x=periodo` e `y=valor`, o pulsar **Usar periodo y valor** en el inspector. La caché interna de wbdata se aísla por proceso para evitar corrupción entre consultas.

En OLS y Dispersión se eligen variables en listas con las columnas numéricas de la tabla conectada. Los modelos múltiples y transformaciones comparten selectores y casillas. **Cargar columnas de la fuente** ejecuta solo la tabla y sus dependencias; cambiar indicador retira los resultados anteriores y exige volver a calcular. Los códigos del catálogo se muestran completos.

**Países favoritos (0.5.4):** en Banco Mundial pulsa País o economía para abrir el catálogo con búsqueda. Marca ★ para guardar favoritos en este equipo y mostrarlos al principio en todos los proyectos. El catálogo incluye 217 países/economías y 79 agregados opcionales; se puede consultar sin conexión.

**Histograma:** conectar una fuente a data, elegir Variable (por ejemplo valor), ajustar Intervalos y ejecutar. Seleccionar el nodo abre Resultados con barras, frecuencias y faltantes. Los resultados de otros modelos y transformaciones también se presentan al seleccionar su nodo.

**Resultados y continuación del flujo (0.6.0):** el ojo de cada nodo muestra u oculta su salida en Resultados. Regresión tiene una pestaña propia; añadir un nodo conserva cálculos cuyas entradas y especificación no cambian. Al situarse o pulsar sobre una salida aparecen herramientas compatibles; elegir una la añade conectada y señala las otras entradas que faltan.

**Fuente Wooldridge (0.7.0):** añade Wooldridge, busca y elige uno de los 115 conjuntos (wage1, card, etc.). La elección carga los datos y actualiza las variables de las herramientas conectadas. Elegir otro conjunto invalida los modelos dependientes; revisa sus selectores antes de ejecutar. [Guía y límites](docs/WOOLDRIDGE.md).

Las recomendaciones se abren con **doble clic** en una salida (o Enter al enfocarla), sin activarse al pasar el puntero. Para OLS múltiple con wage1, pulsa **Usar ejemplo wage1**: respuesta wage y explicativas educ, exper, tenure. [Proyecto listo](examples/wooldridge-wage1-multiple-ols.json).

La pestaña Regresión permite elegir OLS simple o múltiple. El botón Ecuación junto a Proyectos muestra la especificación y los coeficientes estimados del modelo elegido.

## Gráfico de serie temporal

Añade **Serie temporal** en Exploración, conecta Banco Mundial, CSV o Wooldridge, elige tiempo y variable, y ejecuta. Permite título y etiquetas de ejes, con color configurable y leyenda. [Guía y ejemplo de tasas de interés](docs/SERIE_TEMPORAL.md).

## Normalidad y datos faltantes

En **Archivos y ejemplos → Ejemplos**, busca **N01 · Normalidad · interés y consumo USA**. Incluye dos fuentes anuales Banco Mundial, unión por año, descriptivos, histogramas, Q–Q, Shapiro–Wilk, Jarque–Bera, imputación explícita por media, OLS y diagnóstico de residuos. Es un ejemplo complementario a los 28 módulos. [Guía y límites](docs/NORMALIDAD.md).

**Boxplot** en Exploración: selecciona variable, título, etiqueta vertical y color. Incluido en N01 antes de imputar. [Guía](docs/BOXPLOT.md).

Boxplot incluye **Reemplazo condicional**: elige `>`, `>=`, `<`, `<=`, `==` o `!=` y un umbral para sustituir por la media original. Muestra el recuento y ofrece la tabla resultante por `data`, conservando la fuente.

En Resultados, los recorridos guiados también muestran todas las salidas con el ojo activado. Usa los accesos del panel para saltar directamente a cada Boxplot, sin recorrer los demás gráficos.

**Correlación** y **Covarianza de variables**, en Exploración, permiten seleccionar columnas y mostrar matrices en Resultados. [Guía](docs/CORRELACION_COVARIANZA.md).
