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

## Deep learning y RL: DL01, DL02, RL01, RL02 (0.23.0)

Sin conexión (datos sintéticos, semilla 42); la suite los ejecuta completos.

| Ejemplo | Flujo | Resultado (2026-11-05) |
|---|---|---|
| DL01 · Red multicapa frente a MCO | `synthetic` (sen x) → `split` → `nn_input` → `nn_layer` densa 32 ReLU → dropout 10 % → densa 16 tanh → `nn_output` → `nn_train` → `evaluate`; `multiple_ols` → `evaluate` | RMSE de prueba 0,106 (red) frente a 0,374 (MCO) |
| DL02 · Clasificación frente a logit | `synthetic` (logístico) → red 8-4 ReLU con salida sigmoide; `logit` | RMSE de prueba 0,444 (red) y 0,445 (logit); exactitud del logit 0,705: la red no aporta si el modelo verdadero es logit |
| RL01 · Agente con regímenes | `synthetic` (regímenes) → Q-learning, SARSA y Q-learning con 200 pb | Los tres aprenden corto en el tercil bajo y largo en el alto; con 200 pb la política no cambia pero el rendimiento neto cae |
| RL02 · Agente sobre ruido | `synthetic` (rendimientos i.i.d.) → Q-learning | Se queda en efectivo en todos los estados; comprar y mantener gana 27 % en la prueba |

La serie de regímenes de RL01 es exagerada a propósito (±2 % por período): sus rendimientos no son realistas y sirven solo para ver qué aprende el agente cuando sí hay señal.

## Recorridos aplicados con Yahoo Finance Y01–Y02 (0.22.0)

Requieren conexión; uso educativo, no asesoría financiera. Cada uno descarga los rendimientos mensuales 2015–2024 (nodo `datos`), los grafica en paneles, calcula la correlación y estima el modelo de mercado activo = α + β·índice + ε con errores HC3 para cada activo, con diagnósticos y residuos del primero. La suite los ejecuta sin red con precios inyectados (`tests/test_yfinance_source.py`). Resultados de la ejecución real del 2026-11-05 (119 meses comunes, ninguna fecha descartada; Yahoo ajusta precios históricos al pagarse dividendos, así que pueden variar):

| Ejemplo | Activos vs índice | β (IC 95 % HC3) | α mensual (p) | R² |
|---|---|---|---|---|
| Y01 | AAPL vs S&P 500 | 1,23 (1,04–1,43) | 0,99 % (0,064) | 0,47 |
| Y01 | MSFT vs S&P 500 | 0,97 (0,79–1,16) | 1,32 % (0,001) | 0,49 |
| Y02 | WALMEX.MX vs IPC | 0,69 (0,42–0,96) | 0,81 % (0,057) | 0,32 |
| Y02 | AMXB.MX vs IPC | 0,76 (0,56–0,95) | 0,21 % (0,66) | 0,30 |
| Y02 | GFNORTEO.MX vs IPC | 1,37 (1,00–1,73) | 0,89 % (0,092) | 0,56 |

La beta de cada MCO coincide con la de la tabla de comparación del nodo de datos (misma muestra). Diagnósticos del primer modelo: Y01 sin evidencia de heterocedasticidad ni autocorrelación (Breusch-Pagan p = 0,36; Breusch-Godfrey p = 0,78); Y02 White p = 0,029. Calidad de datos observada: Yahoo Finance repite el precio de AMXB.MX en 6 meses (rendimiento exactamente 0 en 2015-02, 2020-04, 2023-04, 2023-05, 2023-06 y 2023-08); la herramienta no lo corrige y Y02 lo declara como pendiente. Pendientes declarados en cada guía: rendimientos en exceso sobre la tasa libre de riesgo y betas móviles.

## Recorridos aplicados con FRED F01–F05 (0.21.0)

Requieren conexión. Se descargan con el nodo `fred` y se abren desde **Ejemplos → F01…F05**. La suite los ejecuta sin red inyectando series sintéticas (`tests/test_fred_source.py`). Resultados de la ejecución real del 2026-11-05 (no son valores esperados fijos: FRED revisa sus series):

| Ejemplo | Datos (FRED) | Herramientas | Resultado real |
|---|---|---|---|
| F01 · Curva de rendimientos → recesión | T10Y3M, USREC; mensual 1982–2024 | `lag` 12 → `logit`; `split` temporal → `logit` → `evaluate` | 504 meses; β(spread₋₁₂) = −1,02 (p < 0,001). Entrenamiento: −1,62; prueba (129 meses): exactitud 0,87 con umbral 0,5 |
| F02 · Curva de Phillips | UNRATE, CPIAUCSL; anual 1960–2019 | `growth` → `difference` → 2 × `ols` HC3, `diagnostics` | Original: pendiente +0,26 (p = 0,25), R² = 0,02. Aceleracionista: −0,44 (p = 0,011), R² = 0,18; NAIRU implícita −β₀/β₁ ≈ 6,0 % |
| F03 · Ley de Okun | GDPC1, UNRATE; trimestral 1948–2019 | `growth` → `difference` → `ols` HC3, `diagnostics`, `residual_analysis` | 287 trimestres; β₁ = −0,28 (p < 0,001), R² = 0,46; crecimiento que estabiliza el desempleo ≈ 0,79 % trimestral. Breusch-Godfrey p < 0,001 |
| F04 · Estructura temporal | DGS3MO, DGS10; mensual 1982–2024 | `unit_root` en niveles y diferencias, `cointegration`, `ecm`, `diagnostics` | ADF niveles: p = 0,26 (3 meses) y 0,038 (10 años); diferencias p < 0,001. Engle-Granger p = 0,043, pendiente 0,90. ECM: α = −0,023 (p = 0,006) |
| F05 · Regla de Taylor | FEDFUNDS, PCEPI, UNRATE; trimestral 1987–2007 | `growth` (4 períodos) → `multiple_ols` HC3, `diagnostics`, `residual_analysis` | 80 trimestres; β_inflación = 1,41, β_desempleo = −0,98 (ambos p < 0,001), R² = 0,48; Durbin-Watson 0,13 |

Lecturas que cada guía pide justificar: en F01 la recesión de 2020 no la anticipa la curva; en F04 el ADF de la tasa a 10 años rechaza al 5 % por su tendencia (el contraste no incluye tendencia) y α implica una vida media de unos 30 meses; en F05 los residuos muy persistentes sugieren suavizamiento de tasas, que el recorrido deja como pendiente.

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
