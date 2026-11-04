# Herramientas descubiertas al reconstruir los módulos

Versión 0.4.0 · 2026-11-01. Los 28 ejemplos se reconstruyeron con nodos reales y puertos validados. Ninguno usa la receta cerrada experiment. Se registran 53 tipos, incluido uno de compatibilidad; 49 tipos participan en los ejemplos. CSV y Banco Mundial pueden sustituir generadores cuando sus columnas cumplen el contrato.

## Qué hizo falta y se implementó

- Puertos para Dataset, FittedModel, Transformer y Result; entradas con nombres distintos, salidas múltiples y prevención de tipos incompatibles/ciclos.
- Transformaciones explícitas: logaritmos, deflactación, per cápita, crecimiento, diferencias, rezagos, potencias y capitalización.
- Partición entrenamiento/prueba, escalador aprendido y aplicación posterior sin refit.
- Estimadores conectables, evaluación separada, diagnósticos, comparación e interpretación.
- Ejecución de un paso con su subgrafo de dependencias; salida de cada nodo visible y guía de lo que debe observarse.

## Registro de herramientas

La definición compartida es [nodeCatalog.json](../packages/contracts/nodeCatalog.json). Interfaz y motor leen el mismo contrato.

| Herramienta | Categoría | Entradas | Salidas | Uso en ejemplos |
|---|---|---|---|---|
| Datos simulados (`simulate`) | Fuentes de datos | Ninguna | data: Dataset | Disponible para sustituir fuentes |
| Archivo CSV (`csv`) | Fuentes de datos | Ninguna | data: Dataset | Disponible para sustituir fuentes |
| Banco Mundial (`worldbank`) | Fuentes de datos | Ninguna | data: Dataset | Disponible para sustituir fuentes |
| Descriptivos (`describe`) | Exploración | data: Dataset | summary: Summary, result: Result | C01, C02, C04, C09, C17 |
| Dispersión (`scatter`) | Exploración | data: Dataset | plot: Plot, result: Result | C03 |
| Regresión OLS (`ols`) | Modelos | data: Dataset | model: FittedModel, result: Result | C01, C09, C11, C19, C21, C26 |
| Receta anterior (`experiment`) | Experimentos | Ninguna | Ninguna | Compatibilidad 0.3.0 |
| Generador de escenarios (`synthetic`) | Fuentes de datos | Ninguna | data: Dataset | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19, C20, C21, C22, C23, C24, C25, C26, C27, C28 |
| Logaritmo (`log`) | Transformaciones | data: Dataset | data: Dataset | C13 |
| Deflactar (`deflate`) | Transformaciones | data: Dataset | data: Dataset | C02 |
| Por habitante (`per_capita`) | Transformaciones | data: Dataset | data: Dataset | C02 |
| Tasa de crecimiento (`growth`) | Transformaciones | data: Dataset | data: Dataset | C04 |
| Rezago (`lag`) | Transformaciones | data: Dataset | data: Dataset | C14 |
| Diferencia (`difference`) | Transformaciones | data: Dataset | data: Dataset | C14 |
| Potencias (`polynomial`) | Transformaciones | data: Dataset | data: Dataset | C22 |
| Capitalización (`compound`) | Transformaciones | data: Dataset | data: Dataset | C27 |
| Señal de momentum (`signal`) | Transformaciones | data: Dataset | data: Dataset | C23 |
| Estandarizar (`standardize`) | Transformaciones | data: Dataset | data: Dataset, transformer: Transformer | C20, C25, C26 |
| Aplicar escalador (`apply_scaler`) | Transformaciones | data: Dataset, transformer: Transformer | data: Dataset | C26 |
| Separar entrenamiento/prueba (`split`) | Transformaciones | data: Dataset | train: Dataset, test: Dataset | C12, C15, C22, C23, C26 |
| Muestrear (`sample`) | Transformaciones | data: Dataset | data: Dataset | C06, C07 |
| Histograma (`histogram`) | Exploración | data: Dataset | result: Result | C03 |
| Correlación (`correlation`) | Exploración | data: Dataset | result: Result | C04, C28 |
| Bayes y TCL (`probability`) | Exploración | data: Dataset | result: Result | C05 |
| Comparar muestras (`sampling_audit`) | Diagnósticos | population: Dataset, sample: Dataset, biased: Dataset | result: Result | C06 |
| Intervalo de la media (`mean_ci`) | Exploración | data: Dataset | result: Result | C07 |
| Prueba pareada (`paired_test`) | Diagnósticos | data: Dataset | result: Result | C08 |
| Raíz unitaria (`unit_root`) | Diagnósticos | data: Dataset | result: Result | C16 |
| Resumen de escenarios (`monte_carlo`) | Exploración | data: Dataset | result: Result | C27 |
| Evaluar estrategia (`backtest`) | Diagnósticos | data: Dataset | result: Result | C23 |
| OLS múltiple (`multiple_ols`) | Modelos | data: Dataset | model: FittedModel, result: Result | C10, C13, C22 |
| Logit / probit (`logit`) | Modelos | data: Dataset | model: FittedModel, result: Result | C12 |
| ARIMA (`arima`) | Modelos | data: Dataset | model: FittedModel, result: Result | C15 |
| GARCH (`garch`) | Modelos | data: Dataset | model: FittedModel, result: Result | C17 |
| Regresión Huber (`robust`) | Modelos | data: Dataset | model: FittedModel, result: Result | C19 |
| Variables instrumentales (`iv2sls`) | Modelos | data: Dataset | model: FittedModel, result: Result | C21 |
| Regímenes HMM (`hmm`) | Modelos | data: Dataset | model: FittedModel, result: Result | C24 |
| Mezcla gaussiana (`gmm`) | Modelos | data: Dataset | model: FittedModel, result: Result | C24 |
| Agrupar con k-means (`kmeans`) | Modelos | data: Dataset | model: FittedModel, result: Result | C25 |
| Red neuronal (`mlp`) | Modelos | data: Dataset | model: FittedModel, result: Result | C26 |
| Diagnóstico del modelo (`diagnostics`) | Diagnósticos | model: FittedModel | result: Result | C10, C11, C17 |
| Cambiar covarianza (`covariance`) | Diagnósticos | model: FittedModel | model: FittedModel, result: Result | C11 |
| Evaluar predicciones (`evaluate`) | Diagnósticos | model: FittedModel, data: Dataset | result: Result | C12, C15 |
| Comparar modelos (`compare_models`) | Diagnósticos | first: FittedModel, second: FittedModel, data: Dataset | result: Result | C19, C21, C22, C24, C26 |
| Calidad de grupos (`silhouette`) | Diagnósticos | model: FittedModel, data: Dataset | result: Result | C25 |
| Cointegración (`cointegration`) | Modelos | data: Dataset | data: Dataset, result: Result | C16 |
| Corrección de errores (`ecm`) | Modelos | data: Dataset | model: FittedModel, result: Result | C16 |
| Regresión por cuantiles (`quantile`) | Modelos | data: Dataset | result: Result | C18 |
| Componentes principales (`pca`) | Modelos | data: Dataset | result: Result | C20 |
| Análisis factorial (`factor_analysis`) | Modelos | data: Dataset | result: Result | C20 |
| Ecuaciones estructurales (`sem`) | Modelos | data: Dataset | result: Result | C28 |
| Interpretar resultados (`report`) | Salidas | result: Result | result: Result | C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19, C20, C21, C22, C23, C24, C25, C26, C27, C28 |
| Autocorrelación (`acf`) | Diagnósticos | data: Dataset | result: Result | C14 |

## Lo que falta por módulo

Los siguientes pendientes se identificaron al construir los flujos. Están también en cada guía; no se anuncian como implementados.

| Módulo | Herramientas o ampliaciones pendientes |
|---|---|
| C01 | Lección evaluable completa y contraste de distintas especificaciones |
| C02 | Datos de panel, índices alternativos y metadatos editables de unidades |
| C03 | Gráfico de barras, caja y controles interactivos de ejes |
| C04 | Media geométrica y distribución de la correlación |
| C05 | Editor general de distribuciones y probabilidades |
| C06 | Muestreo estratificado y sesgo de supervivencia |
| C07 | Cálculo de tamaño de muestra y corrección por población finita |
| C08 | Contrastes múltiples y control de falsos descubrimientos |
| C09 | Intervalos de predicción y contraste manual de hipótesis |
| C10 | Editor de restricciones t/F y selección de especificación |
| C11 | Gráficos de influencia, selección stepwise y otras correcciones |
| C12 | Variables categóricas, interacciones, Chow y efectos marginales |
| C13 | Editor de funciones de potencia y elasticidades generales |
| C14 | Estacionalidad, descomposición y rezagos agrupados por país |
| C15 | SARIMA, VAR, rolling validation e intervalos de pronóstico |
| C16 | Johansen y VECM de varias relaciones |
| C17 | EGARCH y volatilidad multivariada |
| C18 | Contraste entre coeficientes de distintos cuantiles |
| C19 | Otros estimadores robustos y diagnóstico de influencia |
| C20 | Rotación factorial y selección de número de factores |
| C21 | WLS, GLS, máxima verosimilitud y GMM de momentos general |
| C22 | Regularización, promediado de modelos y validación anidada |
| C23 | Datos históricos sin supervivencia y costos de ejecución completos |
| C24 | Selección de estados y evaluación temporal de regímenes |
| C25 | Elección de k y evaluación de estabilidad de grupos |
| C26 | Selección de arquitectura sin usar el bloque de prueba |
| C27 | Distribuciones y escenarios editables más allá de la inflación |
| C28 | Editor de diagramas SEM y diagnóstico general de identificación |

## Cómo seguir un ejemplo

1. Abre Archivos y ejemplos, elige el módulo y pulsa Abrir en canvas.
2. Lee el paso y Qué debes observar. Revisa el escenario y los parámetros en el inspector.
3. Pulsa Ejecutar hasta este paso. El motor recalcula solo sus ancestros y el nodo elegido, no los nodos posteriores.
4. Comprueba la tabla, parámetros, prueba o gráfico de Salida.
5. Pulsa Siguiente. Usa Ver flujo completo para entender sus ramas.
6. Cambia un parámetro o sustituye el origen por CSV y verifica cómo se propaga el cambio. La edición invalida los resultados anteriores.
7. Guarda tu variante y responde la pregunta del reporte.

Los pasos no emplean una caché persistente: recalculan dependencias. La interfaz conserva resultados previos de otros pasos solo si el grafo y las huellas de datos comunes coinciden; el manifiesto registra los IDs de las ejecuciones guiadas acumuladas. Un módulo explicado no equivale a una auditoría completa de todos sus capítulos.

## Fuente adicional 0.7.0

Wooldridge → salida data:Dataset, 115 conjuntos clásicos seleccionables. Añade una herramienta al registro (54 en total); los 28 recorridos anteriores mantienen su cobertura y pendientes. [Guía](WOOLDRIDGE.md).

## Serie temporal · 0.7.4

`time_plot`: Dataset → Result. Selección de tiempo y valor, formato year/date, título y ejes; disponible desde CSV, Banco Mundial y Wooldridge. Referencias B17 y B32; cubre parte de C03/C14. Registro actual: 55 tipos. [Guía](SERIE_TEMPORAL.md).

## Normalidad y faltantes · 0.8.0

Registro actual: 59 tipos. `join_series` consume left/right Dataset y produce data Dataset mediante unión exterior uno a uno; `impute_mean` transforma columnas elegidas y registra medias y reemplazos; `normality` consume Dataset y `residual_normality` consume FittedModel, ambos producen Result con descriptivos, pruebas y gráficos. Referencias B16/B18/B19/B22/B24/B31. [Guía](NORMALIDAD.md).

## Boxplot · 0.8.1

`boxplot`: Dataset → Result. Categoría Exploración; variable numérica, cuartiles, mediana, RIC, bigotes y atípicos. Color y etiquetas editables. Registro: 60 tipos. Referencias B17/B18. [Guía](BOXPLOT.md).

## Asociación de variables · 0.8.4

Registro actual: 61 tipos. Correlación devuelve matrices de Pearson y covarianza; Covarianza de variables (`covariance_matrix`) devuelve matriz muestral. Ambos Dataset → Result, Exploración, B18. Cambiar covarianza sigue siendo un diagnóstico de FittedModel, distinto de estas matrices. [Guía](CORRELACION_COVARIANZA.md).

## Herramientas desde el segundo cerebro · 0.10.0

Registro actual: **73 tipos**. Doce nodos nuevos implementados a partir de las fichas de herramientas faltantes del [segundo cerebro](CEREBRO.md). Todos consumen artefactos conectados, rechazan expresiones y devuelven `Result` con métricas, tablas, series y límites explícitos. Pruebas numéricas en `tests/test_gap_tools.py` contra fórmulas cerradas, statsmodels, scipy o datos con efecto conocido.

| Tipo | Puertos | Módulo | Método | Referencias | Límite declarado |
|---|---|---|---|---|---|
| `sample_size` | — → Result | C07 | n para media (σ) o proporción; corrección por población finita | B20, B21 | Solo muestreo aleatorio simple |
| `multiple_testing` | Dataset → Result | C08 | t por columna; ajuste FDR-BH, Holm o Bonferroni | B22 | H₀ común μ₀ para todas las columnas |
| `prediction_interval` | Dataset → Dataset, Result | C09 | IC de E[y\|x] frente a IP de y nueva; columnas `prediccion`, `pi_inferior`, `pi_superior` | B21, B23, B24 | OLS simple con errores homocedásticos |
| `chow` | Dataset → Result | C12 | F de Chow con quiebre en fracción conocida (ordena por `periodo`) | B31, B33 | Quiebre fijado a priori, varianzas iguales |
| `dummies` | Dataset → Dataset, Result | C12 | `d_<salida>` = 1(columna > umbral) e interacción con x | B33 | Un umbral; no codifica categorías múltiples |
| `seasonal_decompose` | Dataset → Dataset, Result | C14 | Medias móviles aditivas o multiplicativas; fuerza estacional | B32 | Pierde extremos de la tendencia |
| `sarima` | Dataset → Result | C15 | SARIMAX(p,d,q)×(P,D,Q)s, pronóstico e intervalos | B36, B05, B32 | Sin validación rodante |
| `var` | Dataset → Result | C15 | VAR con rezago por AIC, Granger por pares, estabilidad y pronóstico | B32, B25 | Requiere series estacionarias |
| `johansen` | Dataset → Result | C16 | Traza y máximo autovalor al 5 %, rango y vectores | B25 | VECM pendiente; críticos asintóticos |
| `wls` | Dataset → FittedModel, Result | C21 | WLS con 1/x² o FGLS con log(ε̂²); OLS de referencia | B24, B31 | GLS con covarianza general pendiente |
| `regularized` | Dataset → Result | C22 | Lasso, Ridge, Elastic Net estandarizados con CV | B13, B15 | CV no anidada (R² optimista) |
| `cluster_selection` | Dataset → Result | C25 | Inercia y silueta para k = 2…máx. | B08, B07 | No evalúa estabilidad de grupos |

El generador sintético añade el escenario `seasonal` (`periodo`, `ventas` con tendencia y ciclo de 12). `wls` produce un `FittedModel` compatible con **Evaluar** y **Comparar modelos**; los diagnósticos OLS lo rechazan de forma explícita y el cerebro no los conecta.

## Fichas pendientes completadas · 0.11.0

Registro actual: **78 tipos**. Cinco fichas que el cerebro mantenía pendientes pasan a nodos reales. Pruebas en `tests/test_panel_tools.py`.

| Tipo | Puertos | Módulo | Método | Referencias | Verificación | Límite declarado |
|---|---|---|---|---|---|---|
| `panel` | Dataset → Result | C02 | MCO agrupado, efectos fijos (within), efectos aleatorios (Swamy–Arora) y Hausman; EE por conglomerado o clásicos | B16, B30, B31 | FE = LSDV con dummies (coeficiente y EE); tamaño de Hausman ≤ 15 % en 40 réplicas bajo H₀ | Sin efectos temporales; Hausman con covarianzas clásicas |
| `egarch` | Dataset → FittedModel, Result | C17 | EGARCH o GJR-GARCH(p,o,q), media constante, errores normales o t | B26, B27 | Ajuste y conexión con Diagnóstico (ARCH-LM, Ljung–Box) | Univariado; DCC/BEKK pendiente |
| `stepwise` | Dataset → FittedModel, Result | C11 | Forward/backward por AIC o BIC; OLS final con recorrido | B13, B31 | Recupera los regresores verdaderos; primer paso = mínimo AIC | Inferencia post-selección optimista |
| `marginal_effects` | FittedModel → Result | C12 | `get_margeff` promedio o en la media para logit/probit; coeficientes en modelos lineales | B06, B33 | AME logit = media(p(1−p))·β | Sin efectos con interacciones combinadas |
| `bootstrap` | Dataset → Result | C09 | Remuestreo de media, mediana, DE o RIC; IC percentil, básico o BCa | B20, B21 | EE bootstrap ≈ σ/√n; reproducible con semilla | Supone independencia (sin bloques) |

El generador sintético añade el escenario `panel` (`entidad`, `periodo`, `x`, `y`) con efecto individual correlacionado con x. El inspector ofrece `entity` como selector de columna. Queda abierta, entre otras, la ficha `mgarch` (volatilidad multivariada).
