# Quantlabs · Econometrics IA

**Describe tu análisis. El segundo cerebro construye el blueprint. Tú compruebas cada resultado.**

[![Versión](https://img.shields.io/badge/versión-0.24.0-6cc9ac)](VERSION)
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

**Versión 0.27.2 · 2026-11-06 · Alpha local con escritorio Electron, estudio oscuro y segundo cerebro (Ollama/Qwen + reglas). Instaladores independientes y actualización automática pendientes.**

## Segundo cerebro IA

Pulsa **Cerebro IA** en la barra del lienzo y escribe lo que quieres analizar, por ejemplo: *«Analiza la inflación de México 2000-2023 del Banco Mundial con gráfico temporal, raíz unitaria y ARIMA»*.

1. **Recupera** herramientas, recorridos y blueprints valorados con BM25 local.
2. **Planifica** con Qwen vía Ollama en `127.0.0.1` o, si no está disponible, con un planificador determinista en español.
3. **Compila** el plan con la mecánica de los recorridos: solo nodos del catálogo, parámetros declarados, puertos tipados y validador DAG del motor.
4. **Verifica** ejecutando el flujo cuando los datos son locales y repara columnas con las vistas previas reales.
5. **Registra** lo que falta como ficha de herramienta pendiente, sin simularlo ni generar código.

En cada salida de **Resultados**, **Explicar este resultado** pide al agente la interpretación bajo demanda: resumen, qué dicen las cifras, cautelas y siguiente paso. La redacta Qwen local a partir de las métricas (no de las filas) junto con una lectura por reglas que siempre puedes consultar; las cifras que el modelo no toma del resultado se marcan como no verificadas. Sin Ollama se muestra la lectura por reglas.

El nodo **Portafolio de Markowitz** entrega los pesos de cuatro portafolios (pesos iguales, mínima varianza, máximo Sharpe y máximo Sortino), sus métricas de rendimiento, volatilidad y riesgo (desviación a la baja, VaR, CVaR, caída máxima y contribución de cada activo al riesgo) estimadas y fuera de muestra, y los gráficos de frontera eficiente, Sharpe, Sortino, mínima varianza y composición de pesos.

**Agrupar con k-means** muestra el mapa de grupos (con PCA si hay más de dos variables), la silueta por observación, la elección de k (codo y silueta) y el perfil de los centroides, con silueta media, Calinski-Harabasz y Davies-Bouldin.

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

- **Biblioteca por áreas e integración de Quantlabs-Blueprints (0.24.0)**: la biblioteca de la izquierda abre con un submenú de 10 áreas (Datos, Preparar datos, Explorar y graficar, Estadística e inferencia, Regresión y econometría, Series de tiempo, Machine learning, Deep learning y RL, Finanzas cuantitativas, Diagnóstico y resultados); al elegir una aparecen sus herramientas por grupos, y la búsqueda cubre todas. Cada herramienta aparece una sola vez: 8 duplicadas se reemplazaron por la más completa (siguen funcionando en proyectos guardados, con botón «Cambiar a …»). Nuevas desde Blueprints: calidad de datos, cambiar frecuencia, seleccionar columnas, indicadores cuantitativos (RSI, MACD, Bollinger…), métricas de riesgo (Sharpe, Sortino, VaR/CVaR, beta), portafolio de Markowitz y modelos de machine learning (bosque, boosting, SVR, KNN…). Ejemplos Q01, Q02 y ML01. [Detalles](docs/HERRAMIENTAS.md#biblioteca-por-áreas-y-herramientas-de-quantlabs-blueprints-0240)
- **Deep learning capa por capa y aprendizaje por refuerzo (0.23.0)**: nuevo grupo *Deep learning y RL* en la biblioteca. Construye una red multicapa como en Quantlabs-Blueprints: **Capa de entrada** (variables) → una o más **Capas intermedias** (densa con neuronas y activación ReLU, Leaky ReLU, ELU, tanh, sigmoide, Swish o lineal; o dropout) → **Capa de salida** (regresión o clasificación binaria) → **Entrenar red multicapa** (Adam, RMSprop o SGD, L2, mini-lotes y parada temprana), cuyo modelo acepta *Evaluar*. El **Agente de refuerzo** aprende con Q-learning o SARSA a estar corto, en efectivo o largo con costos por cambio de posición y se evalúa fuera de muestra frente a comprar y mantener. Ejemplos DL01, DL02, RL01 y RL02, sin conexión. [Detalles](docs/HERRAMIENTAS.md#deep-learning-capa-por-capa-y-aprendizaje-por-refuerzo-0230)
- **Yahoo Finance con índice de comparación (0.22.0)**: nodo *Yahoo Finance · activos e índice* en Fuentes de datos. Escribe uno o más tickers («TICKER: alias»: `AAPL`, `WALMEX.MX`, `BTC-USD`, `MXN=X`…) y elige el índice para comparar (S&P 500, Nasdaq, Dow Jones, IPC de la BMV, Ibovespa, Euro Stoxx 50, Nikkei… o ninguno), el intervalo y si quieres precios, rendimientos, rendimientos logarítmicos o base 100. La salida incluye una tabla con rendimiento, volatilidad, caída máxima y beta, correlación y R² frente al índice. Ejemplos Y01 (Apple y Microsoft frente al S&P 500) e Y02 (emisoras mexicanas frente al IPC). Uso educativo, no asesoría financiera. [Detalles](docs/HERRAMIENTAS.md#yahoo-finance-con-índice-de-comparación-0220)
- **FRED como fuente de datos (0.21.0–0.21.1)**: nodo *FRED · Reserva Federal de St. Louis* en Fuentes de datos. Elige series en un catálogo de 226 identificadores verificados, con buscador y filtro por tema (tasas, precios, actividad, empleo, dinero, vivienda, mercados, tipos de cambio, comercio, finanzas públicas, ciclo, estados de EE. UU. e internacional con México), o escribe cualquier ID como «ID: alias» (p. ej. `DGS3MO: tbill_3m`), fechas y frecuencia; se descargan del CSV público de FRED sin clave de API y se alinean por fecha. Incluye cinco ejemplos F01–F05 (recesiones con la curva de rendimientos, Phillips, Okun, cointegración de tasas y regla de Taylor). [Detalles](docs/HERRAMIENTAS.md#fred-como-fuente-de-datos-0210) · [Ejemplos](docs/EJEMPLOS.md#recorridos-aplicados-con-fred-f01f05-0210)
- **Gráfico de ajuste OLS con residuos (0.20.0)**: el OLS simple dibuja la recta con su banda IC 95 %, cada residuo como segmento vertical (verde arriba, rosa abajo), los atípicos con |r| > 2 resaltados y un panel de residuos frente a x o ŷ con líneas ±2σ̂ e histograma con la normal N(0, σ̂²). Aparece en la tarjeta del nodo y en la pestaña Regresión sin necesitar un nodo de Dispersión. [Detalles](docs/HERRAMIENTAS.md#gráfico-de-ajuste-ols-con-residuos-0200)
- **OLS múltiple en 3D (0.19.0)**: el resultado del OLS múltiple incluye un plano de regresión 3D que se gira con el ratón o las flechas (residuos como líneas verticales; con más de dos regresores eliges los ejes y los demás se fijan en su media) y gráficos de variable añadida, uno por regresor, cuya pendiente es exactamente el coeficiente (Frisch–Waugh–Lovell). [Detalles](docs/HERRAMIENTAS.md#ols-múltiple-plano-3d-y-variable-añadida-0190).
- **Ejes en notación científica (0.18.0)**: los gráficos (serie temporal, dispersión, boxplot, histograma, normalidad, varias series, boxplots, residuos y pairplot) tienen «Formato del eje Y» (y «del eje X» cuando es numérico): *Automático*, *Notación científica ×10ⁿ* o *Números completos*. Las marcas muestran la mantisa y el nombre del eje el factor, p. ej. `fin_cons (×10¹³)`. Cambiarlo no obliga a recalcular. [Detalles](docs/HERRAMIENTAS.md#formato-de-ejes-0180).
- **Cifras grandes en notación científica (0.27.2)**: en tablas, descriptivos, covarianzas, reportes, coeficientes y etiquetas, los valores de mil millones o más se escriben `2.546 × 10¹³` (p. ej. PIB o consumo del Banco Mundial en US$). Solo cambia la presentación; las exportaciones conservan el valor completo.
- **Motor rápido y en paralelo (0.17.0)**: el escritorio mantiene un grupo de procesos Python ya cargados (multiproceso; hasta 4, configurable con `QL_ENGINE_WORKERS`) y cada ejecución corre en hilos los nodos independientes del grafo (`QL_ENGINE_THREADS`). Una ejecución típica pasa de ~1 s a ~0,03 s; las descargas del Banco Mundial y las ramas pesadas se solapan. [Detalles](docs/ELECTRON.md#rendimiento-multiproceso-e-hilos-0170).
- **Segundo cerebro IA**: enunciado → blueprint conectado, verificado por ejecución y con guía paso a paso; Qwen local con respaldo determinista, memoria valorable y cola de herramientas faltantes. Cuando un nodo falla, **Reparar con Cerebro IA** corrige el flujo del canvas (nombres de salida, columnas, rangos, opciones y conexiones), muestra cada cambio y te deja aplicarlo, sin crear un blueprint nuevo. [Guía](docs/CEREBRO.md).
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
| [Catálogo de ejemplos](docs/EJEMPLOS.md) | Los 28 experimentos, los recorridos aplicados (R01, N01, F01–F05, Y01–Y02) y sus archivos JSON |
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
