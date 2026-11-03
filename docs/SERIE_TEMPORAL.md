# Serie temporal · 0.7.4

El gráfico de referencia muestra una variable a lo largo del tiempo. La herramienta **Serie temporal** se encuentra en **Exploración** y recibe una tabla Dataset. Dispersión y los gráficos internos de experimentos no sustituían esta herramienta reutilizable.

1. Añade una fuente: Banco Mundial, CSV o Wooldridge.
2. Añade Serie temporal y conecta `data` de la fuente con su entrada `data`. También aparece entre las recomendaciones al hacer doble clic en la salida de la fuente.
3. En el inspector elige **Años o fechas (eje X)** y **Variable numérica (eje Y)**. Si no aparecen columnas, pulsa **Cargar columnas de la fuente**.
4. Selecciona **Años enteros** o **Fechas ISO AAAA-MM-DD**. Para Banco Mundial: `periodo`, `valor`, años enteros.
5. Edita título, etiqueta horizontal y etiqueta vertical. Por ejemplo: «Estados Unidos · tasa de interés (%)», «Año» y «Tasa de interés (%)».
6. Pulsa **Ejecutar flujo** y abre **Resultados**. El ojo del nodo controla su visibilidad. Los puntos de series de hasta 500 observaciones muestran fecha y valor al pasar el cursor.

La línea es verde brillante y tiene leyenda; respeta valores negativos. Ordena las fechas antes de dibujar. Los valores sin dato cortan la línea; en modo anual los años ausentes también la interrumpen. No agrega fechas repetidas ni mezcla países; filtra o separa esos datos previamente. En modo fecha ISO une observaciones disponibles, sin suponer frecuencia diaria; si falta una fecha sin fila explícita no puede inferir su frecuencia. No interpola ni predice valores. Filas sin fecha se excluyen y se cuentan aparte.

## Ejemplo de interés en Estados Unidos

Abre [serie-temporal-interes-usa.json](../examples/serie-temporal-interes-usa.json) desde **Abrir proyecto**. Consulta Banco Mundial, país USA, indicador `FR.INR.LEND`, 1960–2020, y dibuja `valor` frente a `periodo`. Requiere conexión y la cobertura disponible del proveedor.

El [Banco Mundial identifica FR.INR.LEND](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/FR.INR.LEND) como tasa de interés de préstamos, anual y expresada en porcentaje. La captura no permite identificar con certeza la serie y sus transformaciones; este ejemplo ilustra el tipo de gráfico y no garantiza reproducir sus cifras. No se inventan ni digitalizan observaciones de la imagen.

## Estado

Implementados nodo, controles de selección y representación SVG. Verificados orden, fechas ISO, años ausentes, valores nulos, negativos, infinitos, períodos repetidos e integración CSV en tests/test_time_plot.py. TypeScript y frontend se comprueban con la compilación. El ejemplo remoto no es una prueba de disponibilidad de todos sus años. Referencias curriculares: B17 y B32; C03/C14 siguen con alcance parcial.

## Color y trazo · 0.7.6

En el inspector selecciona **Color de la línea** y elige un color. Ejecuta el flujo para aplicarlo a la línea, los puntos y la leyenda; guarda el proyecto para conservarlo. El verde es el valor predeterminado. El trazo usa 2,5 unidades SVG. En JSON el parámetro es `color`, por ejemplo `#ffb454`; el motor rechaza formatos inválidos.
