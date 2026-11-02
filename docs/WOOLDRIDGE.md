# Datos Wooldridge

Versión 0.7.0 · 2026-11-02.

## Usar en un proyecto

1. Añadir **Wooldridge** desde Fuentes de datos. Carga wage1 y muestra su tabla.
2. Buscar/elegir otro conjunto en el inspector, por ejemplo card. La elección carga una copia automáticamente; también existe Cargar datos y actualizar variables.
3. Conectar data a OLS, Dispersión, Histograma u otra herramienta.
4. Elegir columnas en las listas/casillas. Los conjuntos originales están en inglés: wage1 tiene wage/educ/exper/tenure; card incluye wage/educ/nearc4, entre otras.
5. Ejecutar el flujo para recalcular modelos. Cambiar conjunto retira resultados dependientes y señala selecciones que no existen en el nuevo esquema. No inventa correspondencias entre nombres.

Los selectores de las herramientas conectadas usan el esquema de la salida y, para esta fuente local, los metadatos del conjunto seleccionado. Cargar columnas de la fuente también funciona para CSV, Banco Mundial, simulaciones y transformaciones. Las columnas de texto se conservan en la tabla; las herramientas numéricas ofrecen solo columnas numéricas. Transformar/recodificar categorías sigue requiriendo una herramienta apropiada, no se hace implícitamente.

## Carga y procedencia

Se implementa load_wooldridge(name) → wd.data(name).copy(). Solo admite nombres del catálogo instalado; rechaza rutas y expresiones. Paquete fijado: wooldridge 0.5.0, con 115 conjuntos. Los datos se leen del paquete instalado, sin copiar sus observaciones a Git ni necesitar red durante la consulta.

Fuente y versión quedan en el manifiesto junto a la huella de los datos. El catálogo packages/contracts/wooldridgeCatalog.json incluye dimensiones, columnas, tipos y faltantes; se regenera con scripts/update_wooldridge_catalog.py. No contiene filas de observaciones. La documentación original de variables se puede consultar con wd.data('wage1', description=True) desde Python; la aplicación presenta nombres, tipos y faltantes, sin traducir ni inventar unidades.

La tabla de Wooldridge presenta columnas float con separador de miles y seis decimales. Es formato visual: no se modifican las opciones globales de pandas ni se redondean los cálculos o valores exportados.

## Tamaño y faltantes

Se admiten hasta 50.000 filas y 100 columnas en las tablas del motor: cubre los 115 conjuntos de la versión instalada. CSV conserva su límite de entrada de 10.000 filas y 2 MB. Todos los cálculos usan la tabla completa; cada modelo aplica sus reglas explícitas de faltantes y sus límites de tiempo.

Para tablas de más de 10.000 filas, el JSON de resultados incluye solo las primeras 1.000 observaciones, records_complete=false y una nota visible. n y la huella corresponden al conjunto completo. Esto evita exceder el límite del transporte. No confundir esa muestra de exportación con la muestra de estimación; la vista previa muestra las primeras ocho filas.

Las columnas mixtas de algunos conjuntos se conservan como texto, sin conversión o imputación automática. Disponer de un conjunto no garantiza identificación causal, estacionariedad, convergencia ni cobertura bibliográfica completa.

## Verificación

Pruebas sin red cargan los 115 conjuntos y contrastan dimensiones/esquema contra el catálogo. OLS sobre wage1 se compara con statsmodels; se comprueba cambio a card/hprice1, copia independiente, rechazo de rutas y exportación acotada de conjuntos grandes.

Fuentes: [paquete Python y uso de data()](https://github.com/spring-haru/wooldridge), [versión en PyPI](https://pypi.org/project/wooldridge/0.5.0/).

## Ejemplo OLS múltiple (0.7.1)

Conectar data de Wooldridge (wage1) a data de OLS múltiple. Pulsar Usar ejemplo wage1 en el inspector o elegir respuesta wage y marcar educ, exper, tenure; covarianza HC3. Ejecutar y mostrar la salida con el ojo del nodo. El proyecto examples/wooldridge-wage1-multiple-ols.json también se puede importar. La respuesta no se puede seleccionar como regresor. Las casillas descartan nombres iniciales x/z inexistentes al elegir columnas nuevas, y eliminan repeticiones.

No escribir toda la fórmula en una casilla: respuesta y regresores son campos separados. El intercepto lo añade el motor. Es una asociación salarial condicionada a esas variables; no demuestra causalidad.

### Regresión y ecuación (0.7.2)

Ejecuta el modelo y abre Regresión. El selector permite elegir OLS simple o múltiple; se conserva la selección al consultar otros nodos. Ecuación, junto a Proyectos, muestra ese mismo modelo: forma teórica, estimación y significado de variables. En wage1 usa wage como dependiente y educ, exper, tenure como regresores. La presentación de la ecuación simple se conserva.
