# Catálogo de experimentos

Versión 0.3.0 · 2026-11-01. Hay 28 proyectos ejecutables, uno por módulo curricular. Todos usan datos artificiales y semilla explícita: no requieren conexión ni descargan datos. Son introducciones prácticas; los subtemas de cada módulo permanecen visibles para ampliar su cobertura.

En la aplicación: **Archivos y ejemplos → Ejemplos**. Busca por tema, módulo o referencia, selecciona un ejemplo y pulsa Ejecutar. Puedes revisar/editar su JSON, cambiar n/semilla y guardarlo en Mis proyectos sin modificar el original.

| Módulo | Experimento | Referencias | Proyecto |
|---|---|---|---|
| C01 | Del proceso generador a la estimación | B01, B28 | [JSON](../examples/projects/C01.json) |
| C02 | Nominal, real y per cápita | B16 | [JSON](../examples/projects/C02.json) |
| C03 | Visualizar sin ocultar observaciones | B17 | [JSON](../examples/projects/C03.json) |
| C04 | Describir antes de explicar | B18 | [JSON](../examples/projects/C04.json) |
| C05 | Bayes y el teorema del límite central | B19 | [JSON](../examples/projects/C05.json) |
| C06 | Muestreo aleatorio y sesgo de selección | B20 | [JSON](../examples/projects/C06.json) |
| C07 | La incertidumbre de una media | B21 | [JSON](../examples/projects/C07.json) |
| C08 | Pruebas de hipótesis con pares | B22 | [JSON](../examples/projects/C08.json) |
| C09 | Ingreso y consumo: OLS simple | B03, B23, B29 | [JSON](../examples/projects/C09.json) |
| C10 | Regresión múltiple y multicolinealidad | B04, B14, B30 | [JSON](../examples/projects/C10.json) |
| C11 | Diagnosticar heterocedasticidad | B24, B31 | [JSON](../examples/projects/C11.json) |
| C12 | Clasificar con logit y probit | B06, B33 | [JSON](../examples/projects/C12.json) |
| C13 | Elasticidades de Cobb-Douglas | B15 | [JSON](../examples/projects/C13.json) |
| C14 | AR(1) frente a un paseo aleatorio | B32 | [JSON](../examples/projects/C14.json) |
| C15 | Pronosticar con una prueba temporal | B05, B36 | [JSON](../examples/projects/C15.json) |
| C16 | Cointegración y corrección de errores | B25 | [JSON](../examples/projects/C16.json) |
| C17 | La volatilidad cambia: GARCH(1,1) | B26 | [JSON](../examples/projects/C17.json) |
| C18 | Más allá de la media: cuantiles | B34 | [JSON](../examples/projects/C18.json) |
| C19 | Regresión robusta con valores atípicos | B35 | [JSON](../examples/projects/C19.json) |
| C20 | PCA y factores: dos reducciones distintas | B11 | [JSON](../examples/projects/C20.json) |
| C21 | Endogeneidad y variables instrumentales | B12 | [JSON](../examples/projects/C21.json) |
| C22 | Complejidad, AIC, BIC y prueba externa | B13 | [JSON](../examples/projects/C22.json) |
| C23 | Backtest temporal con costos | B27 | [JSON](../examples/projects/C23.json) |
| C24 | Regímenes ocultos y mezclas gaussianas | B07 | [JSON](../examples/projects/C24.json) |
| C25 | Grupos con k-means | B08 | [JSON](../examples/projects/C25.json) |
| C26 | Red neuronal frente a un baseline lineal | B09 | [JSON](../examples/projects/C26.json) |
| C27 | Escenarios de inflación por Monte Carlo | B10 | [JSON](../examples/projects/C27.json) |
| C28 | Medición latente y trayectorias SEM | B02 | [JSON](../examples/projects/C28.json) |

## Contrato pedagógico

Cada ficha incluye objetivo, todos los temas de su módulo como guía, pregunta de interpretación, bibliografía y límite de alcance. El nodo experiment solo admite IDs C01-C28 y ejecuta código previamente registrado: el JSON no puede ejecutar Python o expresiones arbitrarias.

Parámetros: `topic` (C01-C28), `seed` (entero de 0 a 2³²−1), `n` (entero de 100 a 1.200). Algunos experimentos usan además un número fijo de réplicas indicado en su interpretación (por ejemplo 5.000 trayectorias Monte Carlo); n es el tamaño base y no se presenta como número de réplicas.

Los resultados incluyen métricas, tablas, series cuando corresponde, interpretación, semilla, advertencias y límites. Los manifiestos registran versiones reales de todas las dependencias adoptadas. El catálogo autoritativo legible por herramientas es [examples/catalog.json](../examples/catalog.json).
