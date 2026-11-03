# Matriz de cobertura curricular

Versión: 0.4.0 · 2026-11-01. **No hay módulos completos. Los 28 módulos tienen ahora un recorrido introductorio con nodos reutilizables y pasos explicados; los subtemas no ejercitados siguen pendientes. Los nodos estándar adicionales mantienen su alcance parcial.** P1-P6 corresponden al roadmap. Los nombres de nodo son contratos propuestos.

| Módulo | Temas que deben conservarse | Nodos / herramientas | Referencias | Fase | Evidencia mínima de aceptación |
|---|---|---|---|---|---|
| C01 | Econometría, teoría, DGP, especificación, estimación y contraste | Lesson, ModelSpecification | B01, B28 | P1 | Estudiante distingue datos, supuestos e inferencia |
| C02 | Medición, categorías, corte transversal, tiempo, panel, índices, deflactación y per cápita | DataSchema, Deflate, PerCapita | B16 | P1 | Unidades y claves verificadas; ejemplo nominal/real |
| C03 | Barras, histogramas, dispersión, series, ejes y sesgos visuales | Histogram, Scatter, TimePlot | B17 | P1 | Gráficos y tablas concordantes con unidades visibles |
| C04 | Media, mediana, varianza, desviación, caja, crecimiento, media geométrica y correlación | Describe, BoxPlot, Growth, Correlation | B18 | P1 | Resultado conocido y dominio de crecimiento validado |
| C05 | Probabilidad, condicional, independencia, Bayes, esperanza, normal, estandarización y TCL | Distribution, Bayes, CLTSimulation | B19 | P2 | Simulación con semilla y explicación de probabilidades |
| C06 | Población, muestra aleatoria, selección, supervivencia, observación, experimento y confusión | Sample, BiasLesson | B20 | P2 | Ejemplo de sesgo y muestreo reproducible |
| C07 | Sesgo/varianza de estimadores, distribución muestral, intervalos t, nivel, tamaño y corrección finita | MeanEstimate, ConfidenceInterval | B21 | P2 | Intervalos correctos sobre muestra conocida |
| C08 | H0/H1, p-valores, significancia, pares, efecto práctico y minería de datos | HypothesisTest, PairedTest | B22 | P2 | Interpretación correcta y registro de contrastes múltiples |
| C09 | OLS simple, residuos, supuestos, R², intervalos de coeficientes y predicción, consumo | OLS, RegressionTable, PredictionInterval | B03, B23, B29 | P2 | Coincidencia con statsmodels y muestra documentada |
| C10 | OLS múltiple, matriz de diseño, t/F, covarianza, correlación, controles, multicolinealidad | DesignMatrix, OLS, VIF, JointTest | B04, B14, B30 | P2 | Detectar rango deficiente y reproducir t/F |
| C11 | Selección de variables, stepwise, especificación, heterocedasticidad, autocorrelación, influencia y atípicos | BP, White, HC, HAC, DW, BG, LjungBox, CookDistance, QQPlot | B24, B31 | P2 | No confundir inferencia robusta con estimación robusta |
| C12 | Dummies, interacciones, cambio estructural, Chow, probabilidad lineal, logit y probit | Encode, Interaction, Chow, Logit, Probit | B06, B33 | P3 | Evitar dummy trap, mostrar efectos marginales y clasificación |
| C13 | Formas lineales, polinomios, potencia, logaritmos, elasticidad, Cobb-Douglas, crecimiento y causalidad | Polynomial, Log, Elasticity | B15 | P3 | Transformaciones válidas y coeficientes interpretados |
| C14 | Tendencia, ciclo, estacionalidad, ecuaciones en diferencias, random walk, ruido y rezagos | Decompose, Lag, Diff, SimulateAR | B32 | P3 | Rezagos no cruzan países y respetan años ausentes |
| C15 | AR/MA/ARMA/ARIMA/SARIMA, ACF/PACF, estacionariedad, ADF/KPSS, suavizado aditivo, forecast y VAR | ARIMA, AdditiveForecast, VAR, RollingSplit | B05, B36 | P3 | Evaluación temporal, intervalos y residuos sin fuga de información |
| C16 | Regresión espuria, integración, Engle-Granger, Johansen, rango y corrección de errores | UnitRoot, Cointegration, ECM, VECM | B25 | P4 | Orden de integración y términos deterministas explícitos |
| C17 | Homocedasticidad, ARCH/GARCH, asimetría, EGARCH, volatilidad y ARCH multivariado | ARCHLM, GARCH, EGARCH, MultivariateVolatility | B26 | P4 | Convergencia, restricciones y residuos estandarizados; motor multivariado validado aparte |
| C18 | Cuantiles, asimetría, colas, diferencias entre coeficientes y regresión temporal/transversal | QuantileRegression, QuantileComparison | B34 | P4 | Cobertura de varios cuantiles y contraste válido |
| C19 | Robustez a atípicos, estimadores robustos e influencia | RobustRegression, Influence | B35 | P4 | Contaminación sintética y distinción respecto de HC/HAC |
| C20 | Factores, cargas, puntuaciones, modelos factoriales y componentes principales | FactorAnalysis, PCA | B11 | P5 | Estandarización, varianza explicada y diferencia PCA/factores |
| C21 | Propiedades, OLS/WLS/GLS, máxima verosimilitud, IV/2SLS, momentos y GMM | WLS, GLS, MLE, IV2SLS, GMM | B12 | P4 | Identificación, instrumentos y condiciones de momentos documentadas |
| C22 | Complejidad, penalización, sobreajuste, validación, AIC/BIC/R² ajustado, model averaging y riesgo | ModelCompare, Regularization, CrossValidation, ModelAverage | B13 | P4 | Misma muestra al comparar y separación de ajuste/evaluación |
| C23 | Estrategias, justificación ex ante, muestra sin supervivencia, sobreajuste, costos y backtest | Strategy, Backtest, CostModel | B27 | P6 | Separación temporal, costos y disponibilidad histórica |
| C24 | Regímenes ocultos, Markov, transiciones y mezclas gaussianas | GaussianHMM, GaussianMixture | B07 | P5 | Distinguir dependencia temporal de mezcla independiente |
| C25 | K-means, distancias, escalado, centroides, elección de k e INB por continente | Scale, KMeans, ClusterPlot | B08 | P5 | Semilla, evaluación y escalado dentro del entrenamiento cuando aplique |
| C26 | Redes neuronales, activación, pesos, capas, entrenamiento y generalización | MLP, LearningCurve | B09 | P5 | Baseline, particiones y convergencia documentadas |
| C27 | Monte Carlo, inflación, escenarios, incertidumbre y distribuciones | MonteCarlo, Scenario, FanChart | B10 | P5 | Semilla, supuestos y error Monte Carlo visibles |
| C28 | SEM, covarianza, correlación, variables latentes, trayectorias e identificación causal | SEM, PathDiagram, FitIndices | B02 | P6 | Identificación y supuestos; ajuste no se interpreta como prueba causal |

## Extensiones explícitas

Panel FE/RE, errores agrupados, Hausman, panel dinámico, diferencias en diferencias y pruebas causales adicionales son ampliaciones propuestas. La presencia de datos de panel en B16 no acredita cobertura detallada de sus estimadores. Registrar referencias adicionales antes de declarar estas lecciones completas.

## Protocolo para cerrar un tema

Revisar las secciones completas del capítulo; desglosar cualquier subtema omitido; documentar ecuación y supuestos; implementar nodo y lección original; añadir un ejemplo reproducible y una prueba científica; registrar errores y limitaciones; actualizar estado por fila, versiones y changelog. La verificación automática garantiza que todos los capítulos tengan una fila asociada, no que todo su contenido esté implementado.

## Avance implementado en 0.2.0

| Módulo | Implementado y probado | Pendiente para cerrar |
|---|---|---|
| C01 | Canvas, experimento guiado de ingreso/consumo e inspector con supuestos | Lección completa, evaluación y revisión de secciones |
| C02 | CSV, simulación y consulta World Bank con procedencia, faltantes y selector del catálogo completo por fuente | Deflactación, per cápita, panel, Excel y edición de unidades |
| C03 | Dispersión con ejes y recta OLS cuando coincide la muestra | Barras, histograma, series y ejercicios de sesgos visuales |
| C04 | Media, mediana, desviación muestral, extremos y recuentos | Caja, crecimiento, media geométrica y correlación |
| C09 | OLS simple, IC 95 %, p-valores, R², residuos, covarianza clásica/HC3 | Lecciones, supuestos ampliados, intervalos de predicción y revisión completa del capítulo |

La base de cada implementación se vincula a las referencias de su fila. La revisión fina de capítulos y ejercicios sigue pendiente; no se declara completada por haber implementado el nodo.

## Experimentos disponibles en 0.3.0

Cada ID C01-C28 tiene una ficha y un JSON ejecutable en [EJEMPLOS.md](EJEMPLOS.md). Las fichas conservan todos los temas de la matriz como guía de ampliación y referencias B01-B36. Se probaron los 28 proyectos, pero su ejecución correcta no equivale a completar cada sección de la bibliografía. Los límites concretos se muestran en los reportes y en [AUDITORIA.md](AUDITORIA.md).

## Reconstrucción con herramientas propias (0.4.0)

Los 28 ejemplos se ejecutaron con herramientas del registro compartido; no utilizan experiment ni llaman sus recetas anteriores. Cada nodo tiene un paso, salida esperada y pregunta. El inventario [HERRAMIENTAS.md](HERRAMIENTAS.md) vincula herramientas a módulos y enumera lo que falta. La definición legible por máquina se conserva en examples/tool-gaps.json.

Se implementaron particiones, escaladores aprendidos/aplicados por separado, puertos para modelos y resultados, transformaciones y diagnósticos requeridos por esos recorridos. Continúa pendiente la cobertura exhaustiva de subtemas; los pendientes no se sustituyen por una receta cerrada.

### Evidencia adicional · 0.7.4

C03 y C14: nodo reutilizable Serie temporal (`time_plot`) con orden cronológico y faltantes explícitos; referencias B17 y B32. No completa descomposición, estacionalidad ni los demás pendientes. Pruebas: tests/test_time_plot.py.
