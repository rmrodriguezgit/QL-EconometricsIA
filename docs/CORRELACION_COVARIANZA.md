# Correlación y covarianza · 0.8.4

1. Añade **Correlación** o **Covarianza de variables** desde **Exploración**.
2. Conecta una tabla a `data`. Para interés y consumo, usa la salida de **Unir series por período**; no conectes dos fuentes independientes a una sola entrada.
3. Marca al menos dos columnas, por ejemplo `lending_rate` y `final_consumption`. Si no aparecen, pulsa **Cargar columnas de la fuente**.
4. Ejecuta el flujo y consulta **Resultados**. Las matrices aparecen con el ojo activo por defecto y cuentan con accesos en el panel de salidas.

N01 incluye ambas herramientas en ramas conectadas a datos observados antes de imputar. Si ya tienes una copia anterior guardada, añade los nodos a esa copia o abre de nuevo N01 desde Ejemplos; los proyectos guardados no se modifican automáticamente.

**Correlación** muestra la matriz de Pearson y, por compatibilidad, la de covarianza. **Covarianza de variables** permite consultar solo la matriz muestral. **Cambiar covarianza** ajusta errores estándar e inferencia de un modelo y conserva su función distinta.

Se usan exactamente las mismas filas completas para todas las variables elegidas; se informa n y filas excluidas. No hay imputación implícita ni muestras distintas por par. Se requieren al menos dos variables y dos observaciones completas. Pearson es adimensional; la covarianza usa divisor n−1 y unidades producto. Su diagonal contiene varianzas. Las correlaciones de columnas constantes se muestran como **No definido**, con advertencia; sus covarianzas pueden ser cero.

La escala afecta la covarianza, y la tendencia, dependencia temporal o imputación pueden alterar la interpretación. Ninguna matriz demuestra causalidad. No se calculan p-valores ni intervalos en esta unidad.

Implementados selectores, resultados y acceso desde N01. Verificación numérica contra NumPy y fórmulas conocidas, constantes, faltantes, validaciones e integración CSV en tests/test_association.py; compilación TypeScript para la integración de interfaz. Referencia B18; C04 mantiene alcance parcial.
