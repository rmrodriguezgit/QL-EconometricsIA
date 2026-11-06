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
| Comparar modelos (`compare_models`) | Diagnósticos | first: FittedModel, second: FittedModel, data: Dataset; con «+»: modelo_3…modelo_6 | result: Result | C19, C21, C22, C24, C26 |
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

Registro actual: 59 tipos. `join_series` consume left/right Dataset (y serie_3…serie_8 añadidas con el botón «+» de la tarjeta) y produce data Dataset mediante unión exterior uno a uno sucesiva por `periodo`; `impute_mean` transforma columnas elegidas y registra medias y reemplazos; `normality` consume Dataset y `residual_normality` consume FittedModel, ambos producen Result con descriptivos, pruebas y gráficos. Referencias B16/B18/B19/B22/B24/B31. [Guía](NORMALIDAD.md).

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

## Banco Mundial multi-indicador y pairplot · 0.13.0

Registro actual: **80 tipos**. Pruebas sin red en `tests/test_wb_multi_pairplot.py` (cliente wbdata simulado) y ejecución real verificada contra la API del Banco Mundial el 2026-11-04.

| Tipo | Puertos | Módulo | Método | Referencias | Verificación | Límite declarado |
|---|---|---|---|---|---|---|
| `worldbank_multi` | — → Dataset | Fuentes | Equivale a `wbdata.get_dataframe({código: alias, …}, country=[…])`: una columna por indicador con su alias, una fila por año (y `pais` si hay varios países). Hasta 12 indicadores y 20 países; descarga en paralelo, un cliente aislado por indicador | B01 | Parser `CÓDIGO: alias` (líneas, comas, `;`, `=` o dict); columnas y orden; error que nombra el código fallido; consulta real USA/MEX | Una sola fuente (`source`) para todos los indicadores; años sin ningún dato se descartan; unidades según metadatos de cada indicador |
| `pairplot` | Dataset → Plot, Result | C03/C10 | Matriz tipo `seaborn.pairplot`: dispersión por par, histograma en la diagonal (apilado por grupo) y r de Pearson por par; grupo opcional (≤ 8 categorías) | B17 | r por pares = `DataFrame.corr()` de pandas (incluido n por par con faltantes); r dentro de cada grupo; suma de histogramas = n | Muestra hasta `max_points` puntos (histogramas y r usan todo); r combina grupos, con aviso y tabla por grupo |

Valores por defecto de `worldbank_multi`: país `USA` e indicadores `GC.REV.SOCL.CN: social_contri`, `FR.INR.LEND: lending_rate`, `NY.GDP.MKTP.KD.ZG: gdp_growth`, `NE.CON.TOTL.CD: fin_cons`. El inspector edita países y filas indicador → alias con el buscador del catálogo; los alias inválidos o repetidos se marcan antes de ejecutar.

## Herramientas multivariadas y apartados · 0.14.0

Registro actual: **89 tipos**. Módulo `engine/quantlabs/multivariate_tools.py`; pruebas en `tests/test_multivariate_tools.py` contra pandas, scipy, numpy y statsmodels.

| Tipo | Puertos | Método | Verificación | Límite declarado |
|---|---|---|---|---|
| `series_plot` | Dataset → Plot, Result | Varias series contra `periodo`: paneles con escala propia, índice base 100 o eje común | Índice = 100 en el primer año observado | Una sola entidad (rechaza tablas con varios países) |
| `boxplots` | Dataset → Plot, Result | Boxplot de Tukey por variable, en z o escala original | Mediana z = cuantil de pandas | Atípicos según 1.5·RIC |
| `describe_table` | Dataset → Summary, Result | `describe()` o `describe().transpose()` | Igual a pandas (rtol 1e-12) | — |
| `two_sample_test` | Dataset → Result | H₀/Hₐ redactadas; Welch, Student, pareada o Mann-Whitney; alternativa bilateral o unilateral | p-valores iguales a scipy | Supone independencia; aviso si las magnitudes difieren > 10³ |
| `eigen_correlation` | Dataset → Result | Valores y vectores propios de la correlación (disposición del listado), índice de condición, VIF, det(R) | Valores propios = `np.linalg.eig`; colinealidad casi perfecta → severa | Umbrales guía (30/10) |
| `sklearn_linear` | Dataset → FittedModel, Result | LinearRegression con StandardScaler opcional; coeficientes estandarizados y originales | Coeficientes originales = statsmodels OLS | Sin inferencia (por diseño de scikit-learn) |
| `cross_validation` | FittedModel + Dataset → Result | Reajusta la especificación en k pliegues (TimeSeriesSplit o KFold); R², RMSE, MAE | Número de pliegues y R² en datos simulados | Aviso si KFold barajado con datos anuales |
| `hyperparameter_search` | Dataset → FittedModel, Result | GridSearchCV de α (Ridge, Lasso, ElasticNet) con escalado; curva de validación | α > 0 y residuos de media 0 | Aviso si α óptimo en el borde |
| `residual_analysis` | FittedModel → Result | Residuos vs predichos, histograma y Q–Q, Jarque-Bera, Shapiro, Breusch-Pagan, Durbin-Watson | Media ≈ 0; rechaza logit | Sobre la muestra de ajuste |

**Apartados de la biblioteca.** Cada herramienta de análisis declara `scope` en el catálogo (`univariada`, `multivariada` o `ambas`). La biblioteca ofrece **Todas · Univariadas · Multivariadas**; las fuentes de datos aparecen siempre. Transformaciones y experimentos solo en *Todas*.

## Formato de ejes (0.18.0)

Parámetros de presentación `y_axis` y `x_axis` con tres opciones:

| Opción | Efecto |
|---|---|
| `auto` (por defecto) | Usa ×10ⁿ solo si el mayor valor absoluto visible es ≥ 10⁴ o < 10⁻²; si no, números completos. |
| `cientifica` | Siempre ×10ⁿ, con n = orden de magnitud del mayor valor absoluto (sin factor si n = 0). Las marcas muestran la mantisa (`1.57`) y el factor aparece en el nombre del eje (`fin_cons (US$) (×10¹³)`). |
| `normal` | Números completos (`15,866,800,000,000`). |

| Nodo | Eje Y | Eje X |
|---|---|---|
| Serie temporal (`time_plot`), Boxplot (`boxplot`), Varias series (`series_plot`), Boxplots (`boxplots`) | ✓ | — (tiempo o categorías) |
| Dispersión (`scatter`) | ✓ | ✓ |
| Histograma (`histogram`) | ✓ frecuencia | ✓ valores |
| Normalidad y normalidad de residuos | ✓ Q–Q | ✓ histograma |
| Análisis de residuos (`residual_analysis`) | ✓ residuos | ✓ predichos |
| Pairplot (`pairplot`) | ✓ etiquetas de fila | ✓ etiquetas de columna |

En las vistas con varios paneles (varias series, pairplot) cada variable calcula su propio exponente. Son parámetros solo de presentación: el motor los ignora y cambiarlos conserva los resultados calculados. Implementación: `apps/desktop/src/axisFormat.ts`; pruebas en `apps/desktop/electron/axisFormat.test.ts`.

## Gráfico de ajuste OLS con residuos (0.20.0)

El nodo **Regresión OLS** (`ols`) añade a su resultado `fit_plot` (componente `OlsFitPlot`), visible en su tarjeta de salida y en la pestaña **Regresión**. Ya no hace falta conectar un nodo de Dispersión para ver la recta.

- **Panel superior**: puntos, recta OLS, banda IC 95 % de la media condicional (con la covarianza elegida: con HC3 la banda se ensancha si hay heterocedasticidad) y cada residuo e = y − ŷ como segmento vertical hasta la recta, verde si e > 0 y rosa si e < 0.
- **Panel inferior**: residuos frente a x (o frente a ŷ con el botón *Residuos vs ŷ*), línea en 0 y líneas ±2σ̂. Al margen, histograma de los residuos con la curva normal N(0, σ̂²).
- **Atípicos**: los puntos con residuo estandarizado interno |r| = |e| / (σ̂·√(1−hᵢᵢ)) > 2 tienen borde naranja; el contador aparece en la cabecera junto a la ecuación ŷ = b₀ + b₁·x, R², σ̂ y n.
- Al pasar el ratón por un punto se resalta en ambos paneles y se muestran x, y, ŷ, e y r.
- Botones *Residuos* y *Banda IC 95 %* para ocultar capas. El formato de ejes (×10ⁿ) del nodo se respeta.
- Límite: más de 2.000 observaciones → muestra fija (semilla 0) que conserva los 20 residuos más extremos; la nota del gráfico lo indica.

Pruebas: `tests/test_ols_fit_plot.py` (residuos, residuos estandarizados y banda frente a statsmodels; banda HC3 más ancha con heterocedasticidad; muestreo con extremos) y `apps/desktop/electron/olsFitGeometry.test.ts` (marcas de eje e histograma). Verificado en la interfaz con el ejemplo ingreso–consumo (120 observaciones, 6 con |r| > 2).

## OLS múltiple: plano 3D y variable añadida (0.19.0)

El nodo **OLS múltiple** (`multiple_ols`) añade dos vistas a su resultado, sin parámetros nuevos:

**Plano de regresión 3D** (`result.plane3d`, componente `RegressionPlane3D`)
- Puntos en el espacio (x₁, x₂, y), el plano ajustado ŷ = β₀ + β₁x₁ + β₂x₂ y una línea vertical de cada punto al plano (su residuo). Verde = sobre el plano, rosa = debajo.
- Se gira arrastrando o con las flechas del teclado; botones *Vista inicial*, *De frente a x₁/x₂*, *Desde arriba*, *Girar*, *Residuos* y zoom. Proyección ortográfica en SVG propio, sin librerías nuevas.
- Con más de dos regresores eliges los dos ejes; los demás se fijan en su media y la respuesta se muestra ajustada, y* = y − Σ βⱼ(xⱼ − x̄ⱼ), de modo que la distancia vertical al plano sigue siendo el residuo exacto del modelo completo.
- Límite: la perspectiva 3D puede engañar y, con más de dos regresores, es un corte del modelo. Se muestran hasta 1.500 puntos (muestra fija con semilla 0).

**Gráficos de variable añadida** (`result.partial_regression`, componente `AddedVariablePlots`)
- Un panel por regresor: residuos de y frente a residuos de xⱼ, ambos tras regresar sobre los demás regresores con constante. La pendiente es exactamente βⱼ (teorema de Frisch–Waugh–Lovell); cada panel muestra β, EE, p y la correlación parcial, y los puntos alejados de la recta son los que más influyen en ese coeficiente.

Pruebas: `tests/test_regression_views.py` (pendientes parciales = coeficientes de statsmodels con regresores correlacionados, filas del plano = valores ajustados, límite de puntos) y `apps/desktop/electron/regressionGeometry.test.ts` (residuo exacto al plano para cualquier par de ejes). Referencia: B13 (Wooldridge, partialling out).

## Yahoo Finance con índice de comparación (0.22.0)

Registro actual: **91 tipos**. Módulo `engine/quantlabs/yfinance_source.py`; catálogo de tickers sugeridos `packages/contracts/yfinanceCatalog.json`; pruebas sin red en `tests/test_yfinance_source.py`.

| Tipo | Puertos | Método | Verificación | Límite declarado |
|---|---|---|---|---|
| `yfinance` | — → Dataset | `yfinance.download` de los cierres ajustados de los activos y del índice elegido; alinea las fechas comunes; entrega precios, rendimientos simples o logarítmicos (%) o base 100; tabla de comparación (rendimiento total y anualizado, volatilidad anualizada, caída máxima, beta, correlación y R² frente al índice) | Rendimientos, logaritmos, base 100, beta, correlación y volatilidad comparados con numpy/pandas sin red; ejemplos Y01–Y02 ejecutados con datos reales el 2026-11-05 (la beta de MCO coincide con la de la tabla) | Máx. 10 activos; índice de la lista o ninguno; intervalo diario sin calendario regular (para rezagos o raíz unitaria, semanal o mensual); sin rendimientos en exceso sobre la tasa libre de riesgo; uso educativo |

Parámetros: `tickers` («TICKER: alias» por línea; sin alias se usa el de la lista sugerida o el ticker en minúsculas con «_»), `index` (p. ej. `^GSPC`, `^MXX`, `ninguno`), `start_date` y `end_date` (AAAA-MM-DD o año; vacía = hoy), `interval` (`diario`, `semanal`, `mensual`) y `values` (`precios`, `rendimientos`, `log`, `base100`). La columna del índice usa su alias (`sp500`, `ipc_mexico`, `nasdaq`…).

## FRED como fuente de datos (0.21.0)

Registro actual: **90 tipos**. Módulo `engine/quantlabs/fred_source.py`; catálogo curado `packages/contracts/fredCatalog.json`; pruebas sin red en `tests/test_fred_source.py`.

| Tipo | Puertos | Método | Verificación | Límite declarado |
|---|---|---|---|---|
| `fred` | — → Dataset | Descarga cada serie de `fredgraph.csv?id=ID&cosd=INICIO&coed=FIN` (sin clave), la nombra con su alias y une por fecha; convierte a semanal (viernes), mensual, trimestral o anual con media, último valor o suma | 33 IDs del catálogo comprobados contra FRED; parseo de `observation_date` y del antiguo `DATE` con «.» como faltante; remuestreo comparado con pandas; ejemplos F01–F05 ejecutados con datos reales el 2026-11-05 | Máx. 12 series y 60.000 filas; las unidades se toman del catálogo curado (otros IDs: consultar la ficha); sin revisiones históricas (ALFRED) ni API oficial |

Catálogo (0.21.1): 226 identificadores verificados el 2026-11-05 en 13 temas, con título en español e inglés, unidades, frecuencia, ajuste estacional y última observación. En el inspector, cada serie tiene un selector con buscador y filtro por tema; el campo de texto sigue admitiendo cualquier ID. Los IDs fuera del catálogo se descargan igual, pero sus unidades no se conocen hasta consultar la ficha.

Parámetros: `series` («ID: alias» por línea; sin alias se usa el del catálogo o el ID en minúsculas), `start_date` y `end_date` (AAAA-MM-DD o año; vacía = hoy), `frequency` (`original`, `semanal`, `mensual`, `trimestral`, `anual`) y `aggregation` (`media`, `ultimo`, `suma`). Con `original` y series de distinta frecuencia las filas de una quedan vacías en las fechas de la otra; la procedencia lo advierte.

Cambios en herramientas existentes: `time_order` acepta `periodo` con fechas ISO regulares, así que `lag`, `growth`, `difference`, `unit_root`, `cointegration`, `ecm`, `arima` y `backtest` funcionan con datos mensuales o trimestrales de FRED. Los datos diarios con huecos de fin de semana siguen rechazándose como calendario irregular, con la sugerencia de convertir la frecuencia; desde 0.27.1 la señal de momentum y el backtest aceptan días hábiles con feriados sueltos (calendario bursátil). `growth` respeta `periods` (antes se ignoraba y siempre usaba 1). `series_plot` dibuja fechas ISO como año decimal y muestra en la tabla la primera y última fecha.

## Deep learning capa por capa y aprendizaje por refuerzo (0.23.0)

Registro actual: **96 tipos**. Módulo `engine/quantlabs/deep_tools.py`; pruebas en `tests/test_deep_tools.py`.

| Tipo | Puertos | Método | Verificación | Límite declarado |
|---|---|---|---|---|
| `nn_input` | — → Network, Result | Capa de entrada: variables (columnas) y estandarización con media y DE del bloque de ajuste | Arquitectura y conteo de parámetros | Hasta 100 variables numéricas |
| `nn_layer` | Network → Network, Result | Capa intermedia densa (1–512 neuronas; ReLU, Leaky ReLU, ELU, tanh, sigmoide, Swish o lineal) o dropout (0–0,9) | Cadena inválida rechazada; no modifica la red de origen | Hasta 12 capas; sin convolución, recurrencia ni normalización por lotes |
| `nn_output` | Network → Network, Result | Capa de salida: respuesta y tarea (regresión lineal + MSE; clasificación sigmoide + entropía cruzada) | Respuesta distinta de las entradas | Solo una salida; clasificación binaria |
| `nn_train` | Network + Dataset → FittedModel, Result | Retropropagación con Adam, RMSprop o SGD con momento, L2, dropout invertido, mini-lotes y parada temprana en la fracción final | Gradientes = diferencias finitas; R² > 0,9 en sen(x); mismas métricas con la misma semilla | Sin GPU; tamaño de la red limitado por el tiempo de CPU |
| `rl_agent` | Dataset → Result, Dataset | Q-learning o SARSA tabular: estado = cuantiles de las variables de estado; acciones corto/efectivo/largo; recompensa = posición × rendimiento siguiente − costo | Con rendimientos alternos aprende «corto tras alza»; costos altos reducen los cambios | Tabular (≤ 5000 estados); un activo; sin DQN |

Resultados de los ejemplos (ejecución del 2026-11-05, semilla 42): en DL01 la red 32-dropout-16 logra un RMSE de prueba de 0,106 frente a 0,374 de MCO (ruido verdadero 0,1; 93 épocas, mejor 63, 609 parámetros). En DL02, con un proceso logístico, red y logit empatan (RMSE de prueba 0,444 y 0,445). En RL01 el agente aprende corto en el tercil bajo y largo en el alto; en RL02, con ruido puro y 5 pb por cambio, se queda en efectivo en todos los estados.

## Biblioteca por áreas y herramientas de Quantlabs-Blueprints (0.24.0)

Registro: **103 tipos** (94 ofrecidos en la biblioteca, 8 reemplazados y 1 heredado). La organización vive en `packages/contracts/toolAreas.json`; una prueba exige que cada herramienta ofrecida esté en un solo grupo. Reemplazos y su migración en `packages/contracts/toolMigrations.json`.

| Tipo | Área | Qué hace |
|---|---|---|
| `data_quality` | Preparar datos | Duplicados de periodo, infinitos, faltantes (informar, eliminar, arrastrar) y atípicos contados |
| `resample` | Preparar datos | Frecuencia semanal, mensual, trimestral o anual (último, media, suma, primero), excluye período incompleto |
| `select_columns` | Preparar datos | Elegir, ordenar y renombrar columnas |
| `quant_features` | Finanzas cuantitativas | Rendimientos, volatilidad y Sharpe móviles, caída, SMA, EMA, RSI(14), MACD(12,26,9), Bollinger; acepta precios o rendimientos (índice base 100), p. ej. directo desde Yahoo Finance |
| `risk_metrics` | Finanzas cuantitativas | Sharpe, Sortino, caída máxima, Calmar, VaR/CVaR históricos, beta, alfa, ratio de información |
| `portfolio` | Finanzas cuantitativas | Markowitz: pesos iguales, mínima varianza, máximo Sharpe y máximo Sortino; rendimiento, volatilidad, desviación a la baja, VaR, CVaR, caída máxima y contribución al riesgo; gráficos de frontera eficiente, Sharpe, Sortino, mínima varianza y pesos; prueba fuera de muestra |
| `ml_compare` | Machine learning | Compara 7 modelos de scikit-learn por validación temporal; el elegido es evaluable |
