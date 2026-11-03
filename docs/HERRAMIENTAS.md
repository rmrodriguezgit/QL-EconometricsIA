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
