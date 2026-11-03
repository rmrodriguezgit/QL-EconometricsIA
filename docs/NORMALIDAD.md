# Normalidad, faltantes e inferencia · 0.8.0

## Empezar

Recarga la interfaz. En **Archivos y ejemplos → Ejemplos**, busca **N01 · Normalidad · interés y consumo USA** y pulsa **Abrir en canvas**. Usa la guía **Ejecutar hasta este paso** para inspeccionar cada cálculo. También puedes importar [el proyecto JSON](../examples/normalidad-interes-consumo-usa.json).

1. **Banco Mundial · interés**: USA, `FR.INR.LEND`, 1960–2020.
2. **Banco Mundial · consumo**: USA, `NE.CON.TOTL.CD`, mismo intervalo. Son [gastos de consumo final en dólares corrientes](https://data.worldbank.org/indicator/NE.CON.TOTL.CD); no una medida real deflactada.
3. **Unir series por período**: interés entra por left; consumo por right. Elige `periodo` como clave y `valor` como variable en ambas. Nombres de salida: `lending_rate` y `final_consumption`. La unión exterior conserva años disponibles y faltantes; rechaza claves duplicadas o vacías y no agrega países.
4. **Normalidad de variables · observados**: selecciona las dos columnas. Calcula cada una con sus valores observados; cuenta los faltantes por separado.
5. **Imputar con la media**: elige las dos columnas. Sustituye únicamente sus NaN por su media observada. La tabla de auditoría muestra media aplicada, observados y cantidad reemplazada. No modifica la tabla fuente.
6. **Normalidad de variables · imputados**: compara las distribuciones, varianzas y pruebas con el paso 4.
7. **Regresión OLS**: X = lending_rate, Y = final_consumption, covarianza HC3. Es un ejercicio descriptivo: no establece causalidad ni corrige tendencia, autocorrelación o endogeneidad.
8. **Normalidad de residuos**: conecta `model` de OLS a su entrada `model`. Diagnostica los residuos del ajuste conectado; no reutiliza las variables originales como si fueran errores.

Las consultas son anuales y requieren conexión. No se fuerza `freq="M"` sobre indicadores anuales. La cobertura y revisiones del proveedor pueden diferir de las cifras del libro. El flujo está verificado sin red sustituyendo las dos fuentes por CSV artificiales; no se presenta esa prueba como una descarga real de todas las observaciones.

## Qué calcula

- Media: `Σxᵢ / n`; mediana; varianza muestral: `Σ(xᵢ − media)² / (n − 1)`; desviación muestral: raíz de esa varianza.
- Histograma de frecuencias y Q–Q con cuantiles teóricos normales frente a valores ordenados. La recta es media + desviación muestral × cuantil normal; es una referencia gráfica, no un ajuste OLS.
- Shapiro–Wilk para 3≤n≤5000. Para muestras mayores se omite y advierte, sin seleccionar una submuestra para fingir que se usaron todos los datos.
- Jarque–Bera con su aproximación asintótica y advertencia de muestras pequeñas.
- H₀: distribución normal. Si p<α se rechaza H₀; no rechazar no demuestra normalidad. α es configurable y no se corrige automáticamente por múltiples contrastes.
- Las columnas constantes muestran descriptivos pero omiten pruebas no definidas. Menos de tres valores, columnas inválidas o infinitos producen errores explícitos. Una columna sin observados no puede imputarse.

Los Q–Q muestran hasta 400 cuantiles repartidos en toda la distribución; las pruebas usan toda la muestra observada. [SciPy documenta el límite del p-valor de Shapiro para n>5000](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.shapiro.html). [Statsmodels sitúa la normalidad entre los diagnósticos de residuos](https://www.statsmodels.org/stable/examples/notebooks/generated/regression_diagnostics.html).

## Correcciones al texto y límites

La media no detecta normalidad ni se divide entre grados de libertad; el divisor n−1 corresponde a la varianza muestral. OLS no exige normalidad marginal de X o Y para calcular coeficientes. La hipótesis normal de errores interviene en la inferencia exacta clásica junto con otros supuestos; los residuos observados solo aproximan errores desconocidos.

Imputar medias reduce artificialmente la dispersión y puede distorsionar correlaciones, errores estándar y pruebas de normalidad. Se ofrece para reproducir el procedimiento didáctico, sin presentarlo como tratamiento universal. Para evaluación predictiva, una media debe aprenderse solo en entrenamiento; este nodo explícitamente usa toda la entrada y no implementa una transformación entrenada independiente. En series temporales, tendencia y dependencia también limitan la interpretación de las pruebas; HC3 no corrige autocorrelación. Los diagnósticos no habilitan ni bloquean automáticamente OLS.

Diseñado e implementado: nodos, controles de columnas, auditoría y gráficos. Verificado con tests/test_normality_tools.py: fórmulas, equivalencia con SciPy, unión temporal, imputación no destructiva, casos constantes/grandes y ejecución de todas las ramas con CSV artificiales. La compilación TypeScript valida la integración del frontend. C02/C04/C05/C08/C11 conservan sus demás pendientes y referencias.
