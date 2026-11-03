# Boxplot · 0.8.1

1. Añade **Boxplot** desde **Exploración** y conecta una fuente o tabla a `data`.
2. Selecciona la **Variable**: `valor` desde Banco Mundial directo, `lending_rate` en N01 o `tasa_préstamo` si así se llama en tu CSV.
3. Edita **Título del gráfico**, **Etiqueta del eje vertical** y **Color del gráfico**. Para el listado 2-5: «Tasa de interés de los préstamos en EE. UU. (%)», «Valores» y verde `#008000`.
4. Ejecuta el flujo y abre Resultados. El ojo controla su visibilidad. Guarda para conservar los parámetros.

El ejemplo **N01 · Normalidad · interés y consumo USA** incluye el boxplot antes de imputar faltantes.

La caja abarca Q1–Q3, con mediana central y RIC = Q3−Q1. Los bigotes terminan en valores observados dentro de Q1−1,5×RIC y Q3+1,5×RIC; si no hay observaciones más allá de un cuartil, terminan en ese cuartil. Se usa interpolación lineal de cuartiles y la convención predeterminada de [Matplotlib](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.boxplot.html). Los puntos exteriores se marcan como atípicos sin eliminarlos; no son necesariamente errores. Una caja no prueba normalidad.

Los faltantes se excluyen y cuentan; no se rellenan con el reemplazo condicional. Columnas vacías, no numéricas o con infinitos producen errores. Se admiten valores negativos, constantes y muestras de un solo observado. La tabla informa cuartiles, bigotes y número de atípicos. La exportación conserva todos los atípicos; si hay más de 500, el gráfico reduce sus puntos visuales y lo indica.

Implementados cálculo, selección de variable, color y SVG. Verificación mediante tests/test_box_plot.py y compilación TypeScript; no se presenta como prueba manual en todos los sistemas operativos. C03/C04 tienen alcance parcial; referencias B17/B18.

## Reemplazo condicional · 0.8.2

En el inspector de Boxplot abre **Reemplazo condicional**. Selecciona **> · mayor que** y umbral **14.5** para reproducir `np.where(serie > 14.5, serie.mean(), serie)`. También puedes elegir **≥ · mayor o igual que**, **<**, **≤**, **=** o **≠**. Por defecto queda en **Sin reemplazo**, incluso en proyectos anteriores.

La media se calcula una sola vez con los valores originales observados, incluidos los que se reemplazarán. Los valores iguales al umbral solo entran en >=, <= o ==, según corresponda. Los faltantes permanecen vacíos, también con !=. No se recalcula la media después de cada sustitución. Ejecuta el flujo: se dibuja la caja tratada y se muestran operador, umbral, media y cantidad reemplazada.

La fuente original permanece intacta. La nueva salida **data · Dataset** de Boxplot permite conectar descriptivos, normalidad, OLS u otra visualización a la tabla resultante. La salida **result** conserva el gráfico y su auditoría. Guardar el proyecto conserva la condición; exportar resultados incluye los datos de salida según los límites habituales de exportación.

N01 incluye dos cajas en ramas paralelas: original y reemplazo >14,5. El reemplazo no normaliza ni corrige automáticamente los datos; puede alterar distribución y resultados inferenciales. Las pruebas verifican seis operadores, frontera 14,5, equivalencia con np.where, fuente intacta y uso de data por un nodo posterior.

## Encontrar las cajas en Resultados · 0.8.3

La pestaña **Resultados** muestra todos los nodos con ojo activo, también en N01. En la navegación de salidas pulsa Boxplot y su título para ir a la caja original o tratada. Seleccionar los pasos 5 o 6 abre Resultados y activa la salida correspondiente. Regresión muestra su tabla y ecuación, no las cajas.
