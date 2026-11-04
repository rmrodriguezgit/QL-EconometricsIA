# Catálogo de recorridos con herramientas

Versión 0.4.0 · 2026-11-01. Los 28 proyectos tienen nodos conectados y 131 pasos explicativos. Ninguno usa la receta cerrada experiment. Los generadores producen datos artificiales; estimación, transformación y evaluación ocurren en las herramientas siguientes.

Abre Archivos y ejemplos → Ejemplos, selecciona el módulo y pulsa Abrir en canvas. Usa Ejecutar hasta este paso y Siguiente para inspeccionar cada salida. También puedes ejecutar el flujo completo, cambiar parámetros o sustituir una fuente por CSV.

| Módulo | Recorrido | Pasos | Herramientas | Referencias | Proyecto |
|---|---|---:|---|---|---|
| C01 | Del proceso generador a la estimación | 4 | synthetic, describe, ols, report | B01, B28 | [JSON](../examples/projects/C01.json) |
| C02 | Nominal, real y per cápita | 5 | synthetic, deflate, per_capita, describe, report | B16 | [JSON](../examples/projects/C02.json) |
| C03 | Visualizar sin ocultar observaciones | 4 | synthetic, histogram, scatter, report | B17 | [JSON](../examples/projects/C03.json) |
| C04 | Describir antes de explicar | 5 | synthetic, growth, describe, correlation, report | B18 | [JSON](../examples/projects/C04.json) |
| C05 | Bayes y el teorema del límite central | 3 | synthetic, probability, report | B19 | [JSON](../examples/projects/C05.json) |
| C06 | Muestreo aleatorio y sesgo de selección | 5 | synthetic, sample, sampling_audit, report | B20 | [JSON](../examples/projects/C06.json) |
| C07 | La incertidumbre de una media | 4 | synthetic, sample, mean_ci, report | B21 | [JSON](../examples/projects/C07.json) |
| C08 | Pruebas de hipótesis con pares | 3 | synthetic, paired_test, report | B22 | [JSON](../examples/projects/C08.json) |
| C09 | Ingreso y consumo: OLS simple | 4 | synthetic, describe, ols, report | B03, B23, B29 | [JSON](../examples/projects/C09.json) |
| C10 | Regresión múltiple y multicolinealidad | 4 | synthetic, multiple_ols, diagnostics, report | B04, B14, B30 | [JSON](../examples/projects/C10.json) |
| C11 | Diagnosticar heterocedasticidad | 5 | synthetic, ols, diagnostics, covariance, report | B24, B31 | [JSON](../examples/projects/C11.json) |
| C12 | Clasificar con logit y probit | 5 | synthetic, split, logit, evaluate, report | B06, B33 | [JSON](../examples/projects/C12.json) |
| C13 | Elasticidades de Cobb-Douglas | 4 | synthetic, log, multiple_ols, report | B15 | [JSON](../examples/projects/C13.json) |
| C14 | AR(1) frente a un paseo aleatorio | 5 | synthetic, lag, difference, acf, report | B32 | [JSON](../examples/projects/C14.json) |
| C15 | Pronosticar con una prueba temporal | 5 | synthetic, split, arima, evaluate, report | B05, B36 | [JSON](../examples/projects/C15.json) |
| C16 | Cointegración y corrección de errores | 5 | synthetic, unit_root, cointegration, ecm, report | B25 | [JSON](../examples/projects/C16.json) |
| C17 | La volatilidad cambia: GARCH(1,1) | 5 | synthetic, describe, garch, diagnostics, report | B26 | [JSON](../examples/projects/C17.json) |
| C18 | Más allá de la media: cuantiles | 3 | synthetic, quantile, report | B34 | [JSON](../examples/projects/C18.json) |
| C19 | Regresión robusta con valores atípicos | 5 | synthetic, ols, robust, compare_models, report | B35 | [JSON](../examples/projects/C19.json) |
| C20 | PCA y factores: dos reducciones distintas | 5 | synthetic, standardize, pca, factor_analysis, report | B11 | [JSON](../examples/projects/C20.json) |
| C21 | Endogeneidad y variables instrumentales | 5 | synthetic, ols, iv2sls, compare_models, report | B12 | [JSON](../examples/projects/C21.json) |
| C22 | Complejidad, AIC, BIC y prueba externa | 7 | synthetic, polynomial, split, multiple_ols, compare_models, report | B13 | [JSON](../examples/projects/C22.json) |
| C23 | Backtest temporal con costos | 5 | synthetic, signal, split, backtest, report | B27 | [JSON](../examples/projects/C23.json) |
| C24 | Regímenes ocultos y mezclas gaussianas | 5 | synthetic, hmm, gmm, compare_models, report | B07 | [JSON](../examples/projects/C24.json) |
| C25 | Grupos con k-means | 5 | synthetic, standardize, kmeans, silhouette, report | B08 | [JSON](../examples/projects/C25.json) |
| C26 | Red neuronal frente a un baseline lineal | 8 | synthetic, split, standardize, apply_scaler, mlp, ols, compare_models, report | B09 | [JSON](../examples/projects/C26.json) |
| C27 | Escenarios de inflación por Monte Carlo | 4 | synthetic, compound, monte_carlo, report | B10 | [JSON](../examples/projects/C27.json) |
| C28 | Medición latente y trayectorias SEM | 4 | synthetic, correlation, sem, report | B02 | [JSON](../examples/projects/C28.json) |

## Alcance

Cada proyecto incluye lesson: objetivo, referencias, pasos, instrucciones, resultado esperado, preguntas y herramientas pendientes. Cambiar la semilla o la tabla de origen afecta los cálculos posteriores; los modelos no generan una muestra interna.

El catálogo conserva todos los temas de cada módulo como guía curricular, pero estos recorridos no completan cada sección de los libros. Los métodos y herramientas todavía pendientes están enumerados en [HERRAMIENTAS.md](HERRAMIENTAS.md). La definición del catálogo se guarda en [catalog.json](../examples/catalog.json). Los archivos personales 0.3.0 con experiment siguen admitidos como compatibilidad; el catálogo nuevo no los utiliza.

## Recorrido aplicado R01 · Indicadores de EE. UU. (0.14.0)

Requiere conexión (Banco Mundial). 22 nodos, un paso guiado por nodo; se abre desde **29 ejemplos → R01**. La suite valida su estructura sin red y lo ejecuta sin red sustituyendo la fuente por una tabla equivalente; la ejecución real (1972–2020, 49 años) se verificó el 2026-11-04 con los 22 nodos correctos.

| Paso | Nodo(s) | Qué responde |
|---|---|---|
| a | `worldbank_multi` (USA: social_contri, lending_rate, gdp_growth, fin_cons) | Leer las 4 variables como `wbdata.get_dataframe` |
| b | `series_plot` | Graficarlas (paneles; índice base 100 opcional) |
| c | `boxplots` | Boxplot estandarizado y atípicos |
| d, e | `covariance_matrix`, `correlation` | Covarianza y correlación |
| f | `pairplot` | Matriz de dispersión |
| g | `describe_table` | `describe().transpose()` |
| h | 3 × `two_sample_test` | Hipótesis 1–3: cada variable frente al gasto de consumo final (Welch) |
| i | `eigen_correlation` | Correlación severa: valores y vectores propios, índice de condición, VIF |
| j | `standardize` → `pca` | Reducción de dimensión (escalado previo) |
| k | `split` → `multiple_ols` → `evaluate` | Predicción con MCO de statsmodels y error fuera de muestra |
| l | `residual_analysis` | Residuos del MCO |
| m | `sklearn_linear` | MCO con scikit-learn |
| n | `cross_validation` | Validación cruzada temporal |
| o | `hyperparameter_search` | Ridge con α por GridSearchCV |
| p | `residual_analysis` | Residuos del modelo optimizado |

Lectura de la ejecución real: las tres hipótesis rechazan H₀, pero comparan variables en unidades distintas (moneda local, %, US$); el recorrido lo señala como pendiente metodológico. Los residuos del MCO muestran autocorrelación (Durbin-Watson ≈ 0,61) y heterocedasticidad (Breusch-Pagan p ≈ 0,006).
