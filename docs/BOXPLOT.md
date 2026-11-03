# Boxplot · 0.8.1

1. Añade **Boxplot** desde **Exploración** y conecta una fuente o tabla a `data`.
2. Selecciona la **Variable**: `valor` desde Banco Mundial directo, `lending_rate` en N01 o `tasa_préstamo` si así se llama en tu CSV.
3. Edita **Título del gráfico**, **Etiqueta del eje vertical** y **Color del gráfico**. Para el listado 2-5: «Tasa de interés de los préstamos en EE. UU. (%)», «Valores» y verde `#008000`.
4. Ejecuta el flujo y abre Resultados. El ojo controla su visibilidad. Guarda para conservar los parámetros.

El ejemplo **N01 · Normalidad · interés y consumo USA** incluye el boxplot antes de imputar faltantes.

La caja abarca Q1–Q3, con mediana central y RIC = Q3−Q1. Los bigotes terminan en valores observados dentro de Q1−1,5×RIC y Q3+1,5×RIC; si no hay observaciones más allá de un cuartil, terminan en ese cuartil. Se usa interpolación lineal de cuartiles y la convención predeterminada de [Matplotlib](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.boxplot.html). Los puntos exteriores se marcan como atípicos sin eliminarlos; no son necesariamente errores. Una caja no prueba normalidad.

Los faltantes se excluyen y cuentan; no se imputan. Columnas vacías, no numéricas o con infinitos producen errores. Se admiten valores negativos, constantes y muestras de un solo observado. La tabla informa cuartiles, bigotes y número de atípicos. La exportación conserva todos los atípicos; si hay más de 500, el gráfico reduce sus puntos visuales y lo indica.

Implementados cálculo, selección de variable, color y SVG. Verificación mediante tests/test_box_plot.py y compilación TypeScript; no se presenta como prueba manual en todos los sistemas operativos. C03/C04 tienen alcance parcial; referencias B17/B18.
