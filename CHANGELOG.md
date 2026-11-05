# Historial de cambios

## 0.4.0 - 2026-11-01

- Reconstrucción de los 28 ejemplos como grafos conectados sin usar el nodo de receta cerrada: 131 pasos y 49 tipos de herramienta usados.
- Registro compartido de 53 tipos entre interfaz y motor, con puertos Dataset/FittedModel/Transformer/Result, salidas múltiples y control de conexiones.
- Transformaciones, entrenamiento/prueba, escalado separado, modelos, diagnósticos, comparación e interpretación como herramientas reutilizables.
- Guía por nodo con instrucciones, resultado esperado, pregunta, pendientes, navegación e inspección del resultado real.
- Ejecución hasta un nodo con su subgrafo de dependencias; trazabilidad de ejecuciones guiadas y comprobación de huellas al acumular salidas.
- Generadores con ecuación visible; parámetros aprendidos de escaladores inspeccionables; controles de calendario irregular y prevención de fuga de información.
- Inventario de herramientas y pendientes por módulo. Recetas 0.3.0 preservadas solo para compatibilidad.

## 0.3.0 - 2026-11-01

- Catálogo de 28 experimentos reproducibles, uno por módulo curricular, con objetivos, preguntas, temas, bibliografía y alcance explícito.
- Experimentos científicos ejecutables de inferencia, regresión, diagnóstico, series, cointegración, GARCH, cuantiles, robustez, PCA/factores, IV, selección, backtest, HMM, clustering, redes, Monte Carlo y SEM.
- Administrador de proyectos con JSON editable, validación, apertura en canvas, ejecución, guardado, copias, importación/exportación y papelera restaurable.
- Persistencia local con revisiones SHA-256, bloqueo entre procesos, escritura atómica y protección ante archivos dañados o rutas no autorizadas.
- Guardado de borradores separado de ejecución; aviso de cambios pendientes y prevención de superposición OLS sobre fuentes distintas.
- Auditoría funcional documentada y pestaña de comprobaciones del sistema.
- Nuevas dependencias científicas exactas y lock actualizado; módulos curriculares completos e instaladores siguen pendientes.

## 0.2.1 - 2026-11-01

- Selector desplegable de indicadores del Banco Mundial con nombres, códigos, fuente, búsqueda sin distinción de acentos y paginación.
- Catálogo completo de la API en español con caché de 24 horas, validación de todas sus páginas y copia anterior como respaldo ante fallo de red.
- Consultas de datos con fuente explícita y códigos que distinguen mayúsculas/minúsculas, compatibles con la selección del catálogo.
- Desconexión individual de enlaces desde el inspector o desde su línea seleccionada, sin eliminar módulos y con Deshacer.
- Pruebas de catálogo, paginación, integridad de caché, fallo de red y propagación de la fuente a wbdata.

## 0.2.0 - 2026-11-01

- Alpha local React/React Flow con canvas, inspector, búsqueda de nodos, conexiones, deshacer y panel de resultados.
- Motor Python JSON-RPC con validación de DAG, límites de carga, errores por nodo y aislamiento de ramas.
- Fuentes simuladas con semilla, CSV y consulta anual World Bank; descriptivos, dispersión y OLS simple clásico/HC3.
- Ventana de ecuación con modelo poblacional, recta estimada y definiciones usando los coeficientes reales.
- Guardar/abrir proyectos JSON y exportar resultados con snapshots, versiones y huellas SHA-256.
- Locks Python/npm, esquema JSON compartido y pruebas científicas con fixtures conocidos.
- Integración Tauri preparada; compilación nativa, Cargo.lock y sidecar empaquetado pendientes por falta de Rust.
- P1 sigue abierta; C01-C04/C09 parcialmente implementados.

## 0.1.0 - 2026-11-01

- Diseño de aplicación educativa de escritorio macOS/Windows con canvas de nodos, Tauri, React y motor científico Python.
- Inventario de 36 capítulos con huellas SHA-256 y cobertura curricular en 28 módulos.
- Contratos propuestos de IPC/DAG, trazabilidad de datos, diagnósticos científicos, lecciones, accesibilidad y distribución.
- Plan por fases, versiones observadas/propuestas y decisiones pendientes.
- Script de commits/push con alcance controlado, validación documental, pruebas y CI macOS/Windows.
- Bibliografía original y datasets privados excluidos de Git.

La aplicación y sus instaladores están pendientes de implementación. Los cambios de publicación se verifican en Git, sin registrar un SHA autorreferente en esta entrega.

## 0.5.0 · 2026-11-01

- Estudio oscuro inspirado en Quantlabs-Blueprints: biblioteca, canvas, inspector y resultados. Fuentes locales; mejor contraste de controles y tablas.
- Electron 45.2.1 con RPC stdio, procesos Python acotados y cierre completo; recargar, reiniciar y salir. Recuperación del grafo al recargar.
- Consulta de GitHub Releases con estado explícito cuando no existen versiones publicadas; distribución firmada y actualización automática siguen pendientes.
- Recta OLS amarilla brillante, mayor grosor, leyenda y cuadrícula atenuada.
- Pruebas Node de ciclo de vida y validación IPC integradas en sync.py.

## 0.5.1 · 2026-11-01

- Botón visible Nuevo proyecto en la barra principal, con protección de cambios sin guardar.
- Canvas vacío con instrucciones y acceso directo a datos simulados; ejecutar permanece deshabilitado sin nodos.

## 0.5.2 · 2026-11-01

- Corrección de caché wbdata compartida dañada: cada proceso usa una caché temporal aislada, incluso durante la importación del paquete. Conserva cachés anteriores y catálogo JSON.
- Dispersión muestra las columnas disponibles ante un error y ofrece configurar periodo/valor al conectarse con Banco Mundial.

## 0.5.3 · 2026-11-01

- Código completo, nombre y fuente del indicador con ajuste de línea; metadatos seleccionados conservados en el proyecto.
- Listas de variables para OLS y Dispersión, intercambio X/Y, contexto de la serie y vista de datos. Selección por casillas para regresores/instrumentos y columnas múltiples en modelos y transformaciones.
- Carga de columnas desde la tabla conectada; esquema numérico explícito del motor, separado por puerto. Invalida al cambiar indicador, datos o conexiones, sin reutilizar resultados anteriores.
- Selección inicial periodo/valor al conectar World Bank a OLS o Dispersión con sus parámetros originales; no sustituye elecciones personalizadas.
- Pulsar el código abre un diálogo flotante amplio con selección actual, nombre, código completo, fuente, búsqueda y lista paginada.

## 0.5.4 · 2026-11-01

- Catálogo oficial de 217 países/economías y 79 regiones/agregados del Banco Mundial, en español, integrado para consulta sin conexión.
- Selector flotante con búsqueda por nombre/ISO 2/ISO 3 y estrellas de favoritos. Favoritos persistentes por perfil local y al inicio de la lista; marcar estrella no modifica el país del proyecto.
- Script de actualización valida páginas, totalidad y unicidad antes de sustituir el catálogo. Pruebas de filtro, orden y recuperación de preferencias.

## 0.5.5 · 2026-11-01

- Histograma visible como barras, con variable, intervalos, frecuencias, observaciones válidas y faltantes; conserva tabla numérica.
- Seleccionar un nodo abre Resultados. Modelos y transformaciones adicionales muestran su salida en proyectos libres, además de los recorridos guiados.
- El número de observaciones del nodo Histograma corresponde a los valores utilizados, excluyendo faltantes.

## 0.6.0 · 2026-11-01

- Ojo por nodo para mostrar/ocultar su salida. Resultados agrupa las salidas visibles y la regresión conserva acceso propio.
- Recomendaciones al situarse, enfocar o pulsar una salida, basadas en sus tipos de puerto. Añadir y conectar en un paso; entradas adicionales pendientes explícitas.
- Conserva cálculos de nodos/ancestros sin cambios al editar ramas independientes. Invalida dependientes al cambiar datos o especificación, marcando pendientes y manteniendo trazabilidad del cálculo original.

## 0.7.0 · 2026-11-02

- Nueva fuente Wooldridge con 115 conjuntos locales, catálogo, búsqueda, tipos y faltantes. wooldridge 0.5.0 fijado en pyproject.toml y uv.lock.
- Carga copia completa mediante wd.data(name).copy(); al elegir otro conjunto actualiza columnas y retira modelos dependientes anteriores.
- Capacidad de tablas ampliada a 50.000 filas/100 columnas; conjuntos mayores de 10.000 filas exportan solo 1.000 registros de muestra en JSON, con indicación explícita. Cálculos y huella conservan todas las filas.
- Presentación de floats Wooldridge con seis decimales sin modificar datos ni redondear cálculos.

## 0.7.1 · 2026-11-02

- Recomendaciones de salida solo con doble clic, o Enter para teclado; elimina activación por hover, foco o clic simple.
- OLS múltiple conectado a wage1 ofrece ejemplo wage ~ educ + exper + tenure con HC3. Respuesta aparece primero y no puede marcarse como regresor.
- Elegir casillas retira nombres inexistentes y repetidos; los errores identifican qué columnas faltan o están duplicadas.

## 0.7.2 - 2026-11-02

- Pestaña Regresión para OLS simple y múltiple, con selección persistente del modelo, coeficientes, intervalos y métricas.
- Ecuación múltiple junto a Proyectos: especificación, estimación numérica y explicación de variables; ecuación simple conservada.
- Resultados estructurados de OLS múltiple contrastados con statsmodels HC3.

## 0.7.3 - 2026-11-03

- Arrancadores macOS `.command` y Windows `.cmd`, con bootstrap compartido, Python 3.12 y dependencias bloqueadas. Caché de instalación invalidada por configuración, arquitectura y versión mayor de Node.
- Portada README con insignias enlazadas a versiones reales, capacidades y guía de arranque. No se publican instaladores independientes.
- Pruebas del enrutamiento Windows de comandos y de invalidación de dependencias; ejecución nativa en Windows pendiente.

## 0.7.4 - 2026-11-03

- Nodo Serie temporal, con selección de columnas de años o fechas ISO y variable numérica, título, etiquetas, línea verde y leyenda.
- Orden cronológico, interrupción por valores o años faltantes y rechazo de períodos repetidos para evitar mezclar países.
- Ejemplo conectado de Banco Mundial para interés de préstamos en Estados Unidos; no reproduce cifras a partir de una imagen.

## 0.7.5 - 2026-11-03

- Serie temporal: línea y leyenda más finas (2,5 unidades SVG); puntos reducidos para mantener la proporción visual.

## 0.7.6 - 2026-11-03

- Selector de color para Serie temporal en el inspector, persistido en el proyecto y aplicado a línea, puntos y leyenda. Validación hexadecimal en el motor; verde predeterminado compatible con proyectos existentes.

## 0.8.0 - 2026-11-03

- Nodos Unir series por período, Imputar con la media, Normalidad de variables y Normalidad de residuos.
- Media, mediana, varianza y desviación muestrales; histogramas y Q–Q normales; Shapiro–Wilk y Jarque–Bera con advertencias y decisiones explícitas.
- Ejemplo guiado complementario N01 accesible desde Archivos y ejemplos: interés y consumo USA, datos observados e imputados y residuos OLS.
- Alineación exterior uno a uno y auditoría de imputación; no se confunde normalidad de variables con el supuesto de errores ni se bloquea OLS por normalidad.

## 0.8.1 - 2026-11-03

- Nodo Boxplot con variable, título, eje vertical y color editables; cuartiles lineales, mediana, bigotes de Tukey y atípicos, con resumen y faltantes contados.
- Incluido en N01 antes de imputar. No elimina atípicos ni prueba normalidad.

## 0.8.2 - 2026-11-03

- Boxplot: reemplazo opcional por la media original con condiciones >, >=, <, <=, == o != y umbral editable. Desactivado por defecto.
- Auditoría de condición, media y recuento; fuente intacta y salida data para continuar el flujo con la tabla resultante.
- N01 compara cajas originales y tratadas con >14,5. Pruebas de fronteras inclusivas, equivalencia NumPy y propagación de datos.

## 0.8.3 - 2026-11-03

- Corregida la vista inferior de recorridos guiados: Resultados respeta el ojo de todos los nodos y muestra ambas cajas de N01.
- Seleccionar un paso abre su salida en Resultados. Navegación directa entre tarjetas visibles, con títulos para distinguir Boxplot original y tratado.

## 0.8.4 - 2026-11-03

- Correlación visible por defecto con matrices de Pearson y covarianza muestral; muestra común, faltantes y constantes explícitos.
- Nodo Covarianza de variables independiente del ajuste de covarianza del modelo OLS.
- Ambas herramientas incluidas en N01 antes de imputar; mínimo dos observaciones completas y dos variables.

## 0.9.0 - 2026-11-04

- Nuevo repositorio QL-EconometricsIA con el historial completo de Quantlabs-Econometrics; sincronización y consulta de versiones apuntan al nuevo remoto.
- Segundo cerebro (`engine/quantlabs/brain`): recuperación BM25 local sobre catálogo, 28 recorridos, bibliografía y memoria; planificación con Qwen vía Ollama local y respaldo determinista en español.
- Compilador de blueprints con la mecánica existente: parámetros cerrados, puertos tipados, fuente automática, validador DAG, guía de un paso por nodo y verificación por ejecución con reparación de columnas.
- Fichas de herramientas faltantes deduplicadas con contador, puertos sugeridos y estado; memoria de blueprints con valoraciones que alimentan la recuperación.
- Métodos JSON-RPC `brain.*`, CLI `python -m quantlabs.brain` y panel **Cerebro IA** en el estudio; `brain.plan` dispone de 180 s.
- 17 pruebas nuevas del cerebro y una de transporte Electron.

## 0.10.0 - 2026-11-04

- Doce herramientas nuevas a partir de las fichas del segundo cerebro: tamaño de muestra, contrastes múltiples, intervalos de predicción, Chow, dicotómicas e interacción, descomposición estacional, SARIMA, VAR, Johansen, WLS/FGLS, regresión regularizada y selección de k. Registro: 73 tipos.
- Escenario sintético `seasonal` y modelo `wls` compatible con evaluación y comparación.
- El cerebro conecta los consumidores de modelos solo con productores compatibles y traslada matices del enunciado (proporción, Bonferroni, ridge, probit, HAC…) a parámetros.
- Etiquetas en español de los nuevos parámetros en el inspector; inventario de pendientes anotado sin borrar subtemas abiertos.
- 16 pruebas numéricas nuevas y 2 del cerebro (118 en total).

## 0.10.1 - 2026-11-04

- El cerebro informa cuando un diagnóstico se conecta a un modelo distinto del más reciente por compatibilidad; el panel lo muestra como aviso.
- El indicador del motor muestra «Consultando…» hasta recibir el estado real de Ollama.
- Auditoría del sistema incluye el estado del segundo cerebro y las fichas pendientes.
- Documentación: arquitectura del cerebro, instrucciones para agentes sobre cómo implementar fichas y novedades en README.
- Verificado en navegador: Qwen `qwen3.5:4b` construyó un blueprint de 6 nodos en 48 s, verificado 6/6 y abierto y ejecutado en el canvas.

## 0.11.0 - 2026-11-04

- Cinco fichas pendientes del cerebro implementadas: datos de panel (efectos fijos, aleatorios y Hausman), EGARCH/GJR-GARCH, selección stepwise, efectos marginales y bootstrap. Registro: 78 tipos.
- Escenario sintético `panel` y selector de columna `entity` en el inspector.
- El cerebro conecta los nuevos modelos (EGARCH y stepwise con Diagnóstico; efectos marginales con logit y regresiones lineales), traslada matices (GJR, distribución t, backward, BIC, BCa) y registra `mgarch` como nuevo hueco.
- 9 pruebas nuevas (127 en total), incluida la tasa de rechazo de Hausman bajo H₀.

## 0.11.1 - 2026-11-04

- Escritorio: `npm run desktop:dev` arranca un supervisor único (`scripts/desktop-dev.cjs`) con Vite en proceso y Electron sobre él; HMR para la interfaz, reinicio automático de Electron al editar `main.cjs`/`runtime.cjs`/`preload.cjs`, y cierre completo (Electron, Vite y Python) al salir, con Ctrl+C, al cerrar la terminal o si el supervisor muere. Nuevo `Arrancar-Quantlabs-Dev.command` y `launch.cjs --dev`.
- Electron: atiende SIGINT/SIGTERM/SIGHUP con salida ordenada, «Recargar sin caché» (Cmd/Ctrl+Shift+R) y reinicio delegado al supervisor en desarrollo.
- Cerebro: «errores agrupados/cluster» ya no activa k-means (cambiaba el escenario y rompía el panel); prueba de regresión.
- Interfaz: la etiqueta de cada tarjeta del lienzo sale de su categoría (Estimación, Diagnóstico, Transformación…) en lugar de «Exploración» genérica; opciones en español para panel, EGARCH, stepwise, efectos marginales y bootstrap; valores p diminutos en notación científica.
- Verificado en la interfaz (navegador): panel y EGARCH abiertos y ejecutados desde el Cerebro IA. Stepwise, efectos marginales y bootstrap verificados por ejecución del blueprint, no a mano.

## 0.12.0 - 2026-11-04

- Lienzo: modo de revisión a pantalla completa. Botón **Ampliar** en la barra del lienzo; barra flotante con proyecto, nodos/conexiones, **Encuadrar**, **Ejecutar** y **Volver al layout**; `Esc` regresa (cede antes a los diálogos abiertos). El grafo se reencuadra al entrar y al salir.
- Verificado en la interfaz (navegador, 1440×900): el lienzo ocupa toda la ventana, ejecuta el flujo desde la barra ampliada y vuelve al layout con el botón y con `Esc`. No probado aún a mano dentro de la ventana Electron.

## 0.12.1 - 2026-11-04

- Resultados: botón **Ampliar** junto a *Exportar* que lleva Resultados, Regresión, Descriptivos y Trazabilidad a toda la ventana, con pestañas fijas al desplazarse; **Volver al layout** o `Esc` regresan. Solo una vista ampliada a la vez (lienzo o resultados).
- Verificado en el navegador (1440×900): ocupa la ventana, el contenido desplaza con la cabecera fija, el cambio de pestaña conserva la ampliación y `Esc` vuelve al layout.

## 0.13.0 - 2026-11-04

- Nueva fuente **Banco Mundial · varios indicadores** (`worldbank_multi`): equivalente a `wbdata.get_dataframe({código: alias, …}, country=[…])`, con columnas por alias, `pais` si hay varios países, descarga en paralelo y error que nombra el indicador que falla. Por defecto, USA con `social_contri`, `lending_rate`, `gdp_growth` y `fin_cons`. Editor en el inspector (países, indicador con buscador y alias validado).
- Nuevo nodo **Pairplot**: matriz de dispersión con histogramas en la diagonal, r de Pearson por par, color opcional por grupo, tabla de filas completas por par y de correlación dentro de cada grupo, con aviso cuando las unidades pueden diferir entre grupos.
- Cerebro: dos o más indicadores → `worldbank_multi`; las frases de indicadores ya no activan herramientas ni se cuentan dos veces; intención `pairplot` con «por país».
- Verificado: pruebas sin red (cliente simulado) y comparación con pandas; consulta real USA/MEX y pairplot abierto y ejecutado desde el Cerebro IA en la interfaz.

## 0.14.0 - 2026-11-04

- Nueve herramientas multivariadas: gráfico de varias series, boxplot de varias variables, describe + transpose, prueba de hipótesis entre dos variables (Welch, Student, pareada, Mann-Whitney), correlación severa por valores propios (índice de condición, VIF), regresión lineal con scikit-learn, validación cruzada, optimización de hiperparámetros (GridSearchCV) y análisis de residuos para modelos de statsmodels y scikit-learn.
- Biblioteca con apartados **Todas · Univariadas · Multivariadas** según el campo `scope` del catálogo.
- Recorrido aplicado **R01** (a–p) con los cuatro indicadores de EE. UU.: 22 nodos guiados, desde la lectura hasta los residuos del modelo optimizado.
- Cerebro: intenciones para las nuevas herramientas y conexión de modelos de scikit-learn.
- Pruebas: 145 en total; las nuevas comparan con pandas, scipy, numpy y statsmodels. La prueba de Banco Mundial limpia el cliente en caché para no depender del orden.
- Verificado en la interfaz: R01 abierto desde Ejemplos y ejecutado con datos reales (22/22 nodos), y apartados de la biblioteca.

## 0.15.0 - 2026-11-05

- Entradas variables: **Unir series por período** muestra un botón **+** en la tarjeta para añadir series (serie_3…serie_8) y **−** para quitar la última junto con su conexión. Cada serie nueva tiene clave, valor y nombre propios en el inspector; la unión exterior se aplica en orden y rechaza nombres repetidos.
- **Comparar modelos** admite el mismo mecanismo (modelo_3…modelo_6); AIC/BIC solo se muestran como comparables si todos los modelos comparten muestra y tipo lineal.
- Catálogo: campo `variadic` y parámetro `extra_inputs`; el motor valida el límite, exige conectar cada entrada declarada y rechaza puertos no declarados. Revisados los demás nodos con varias entradas: tienen papeles distintos por puerto y se mantienen fijos.
- Pruebas: `tests/test_variadic_inputs.py` (unión de 4 series frente a pandas, límites, nombres repetidos, compatibilidad con 2 entradas y RMSE de 3 modelos frente a mínimos cuadrados de numpy).
- Verificado en la interfaz: botones + y − en ambos nodos, conectores creados y conexión arrastrada a serie_3. No verificado en la interfaz: una ejecución completa con tres fuentes reales (cubierta por las pruebas del motor).

## 0.16.0 - 2026-11-05

- **Reparar con Cerebro IA**: botón en el aviso de error, en el error del nodo y en el panel del cerebro. Repara el flujo actual sin crear un blueprint: nombres de salida inválidos o repetidos (p. ej. «Los nombres de salida deben ser distintos de periodo…»), columnas inexistentes, valores fuera de rango, opciones no válidas, conexiones incompatibles o duplicadas, entradas «+» vacías y entradas sin conectar.
- Diálogo con tabla de cambios (nodo, campo, antes, después, motivo), lista **Necesita tu decisión** y botones **Aplicar cambios** / **Aplicar y ejecutar**; Deshacer revierte.
- Nuevo método RPC `brain.repair` (180 s de límite, permitido en Electron y en el puente de desarrollo).
- Pruebas: `tests/test_brain_repair.py` (8 casos); 160 pruebas Python en total.
- Verificado en la interfaz: reparación de un nodo Unir series sin conectar (cambios aplicados al canvas) y caso parcial que pide decisión al usuario. El caso de nombres inválidos está verificado por pruebas del motor, no a mano en la interfaz.

## 0.17.0 - 2026-11-05

- **Multiproceso**: el escritorio y el puente de desarrollo usan un grupo de procesos Python persistentes (2 precargados al abrir, hasta `QL_ENGINE_WORKERS`, por defecto núcleos − 1 con máximo 4) en lugar de arrancar Python en cada solicitud. Ejecutar C22 desde la interfaz pasa de ~1,06 s a ~0,033 s; varias solicitudes corren en paralelo.
- **Multihilo**: los nodos independientes del grafo se calculan a la vez (`QL_ENGINE_THREADS`), con resultados, orden y huellas idénticos a la ejecución secuencial. Avisos capturados por hilo (`parallel.capture_warnings`) en lugar de `warnings.catch_warnings`, que no es seguro entre hilos.
- **Procesos dentro de un nodo**: GridSearchCV usa varios procesos solo con trabajo grande (`QL_ENGINE_PROCESSES`).
- Canal JSON-RPC protegido: lo que impriman las librerías va a stderr. Nuevo método interno `engine.warmup`. En desarrollo, cambiar el motor reemplaza los procesos sin reiniciar la app.
- Pruebas: `tests/test_parallel.py` (los 28 ejemplos idénticos con y sin hilos, solapamiento real de nodos, avisos por hilo, canal limpio) y pruebas del grupo de procesos en `runtime.test.cjs` (reutilización, paralelo, recuperación tras un proceso muerto, recarga). 165 pruebas Python y 32 de escritorio.
- Un proceso que se está cerrando (recarga, reciclaje u ocio) ya no recibe trabajo ni cuenta como precargado; `warm` repone los mínimos de inmediato. Verificado en Electron: 2 procesos al abrir y reemplazo al editar el motor.
- Mediciones y límites en docs/ELECTRON.md: con muestras de clase el GIL anula la ganancia de los hilos; la mejora principal es no volver a arrancar Python.

## 0.18.0 - 2026-11-05

- **Ejes en notación científica ×10ⁿ**: «Formato del eje Y» (y «del eje X» cuando es numérico) en serie temporal, dispersión, boxplot, histograma, normalidad, normalidad de residuos, varias series, boxplots, análisis de residuos y pairplot. Opciones: Automático, Notación científica ×10ⁿ y Números completos. Mantisas en las marcas y factor en el nombre del eje; el pairplot añade marcas en el eje Y de cada fila.
- El modo Automático sustituye la notación compacta anterior (p. ej. «18 B») por ×10ⁿ cuando los valores son ≥ 10⁴ o < 10⁻².
- Cambiar el formato no invalida resultados: los parámetros de presentación se excluyen de la firma de cada nodo.
- Pruebas: `electron/axisFormat.test.ts` (exponentes, modos, marcas distinguibles y conservación de resultados).
- Verificado en la interfaz con valores de billones (fin_cons ≈ 10¹³): serie temporal y dispersión en ×10ⁿ, boxplot en números completos, varias series y pairplot en Automático, y cambio de formato desde el inspector sin recalcular.

## 0.19.0 - 2026-11-05

- **Plano de regresión 3D** en el resultado del OLS múltiple: puntos, plano ajustado y residuos como líneas verticales; giro con ratón o teclado, vistas predefinidas, giro automático y zoom. Con más de dos regresores se eligen los ejes y la respuesta se ajusta por los demás (y*), de modo que la distancia al plano es el residuo exacto.
- **Gráficos de variable añadida** (regresión parcial), uno por regresor, con pendiente igual al coeficiente (Frisch–Waugh–Lovell), EE, p y r parcial.
- Pruebas: `tests/test_regression_views.py` frente a statsmodels y `electron/regressionGeometry.test.ts`.
- Verificado en la interfaz: modelo con 2 regresores (plano, giro por arrastre, residuos, paneles con pendientes iguales a la tabla de coeficientes) y con 3 regresores (selector de ejes y nota del corte).
