# Historial de cambios

## 0.4.0 - 2026-11-01

- Reconstrucción de los 28 ejemplos como grafos conectados sin usar el nodo de receta cerrada: 131 pasos y 49 tipos de herramienta usados.
- Registro compartido de 53 tipos entre interfaz y motor, con puertos Dataset/FittedModel/Transformer/Result, salidas múltiples y control de conexiones.
- Transformaciones, entrenamiento/prueba, escalado separado, modelos, diagnósticos, comparación e interpretación como herramientas reutilizables.
- Guía por nodo con instrucciones, resultado esperado, pregunta, pendientes, navegación e inspección del resultado real.
- Ejecución hasta un nodo con su subgrafo de dependencias; trazabilidad de ejecuciones guiadas y comprobación de huellas al acumular salidas.
- Generadores con ecuación visible; parámetros aprendidos de escaladores inspeccionables; controles de calendario irregular y prevención de fuga de información.
- Inventario de herramientas y pendientes por módulo. Recetas 0.3.0 preservadas solo para compatibilidad.

## 0.3.0 - 2026-11-01

- Catálogo de 28 experimentos reproducibles, uno por módulo curricular, con objetivos, preguntas, temas, bibliografía y alcance explícito.
- Experimentos científicos ejecutables de inferencia, regresión, diagnóstico, series, cointegración, GARCH, cuantiles, robustez, PCA/factores, IV, selección, backtest, HMM, clustering, redes, Monte Carlo y SEM.
- Administrador de proyectos con JSON editable, validación, apertura en canvas, ejecución, guardado, copias, importación/exportación y papelera restaurable.
- Persistencia local con revisiones SHA-256, bloqueo entre procesos, escritura atómica y protección ante archivos dañados o rutas no autorizadas.
- Guardado de borradores separado de ejecución; aviso de cambios pendientes y prevención de superposición OLS sobre fuentes distintas.
- Auditoría funcional documentada y pestaña de comprobaciones del sistema.
- Nuevas dependencias científicas exactas y lock actualizado; módulos curriculares completos e instaladores siguen pendientes.

## 0.2.1 - 2026-11-01

- Selector desplegable de indicadores del Banco Mundial con nombres, códigos, fuente, búsqueda sin distinción de acentos y paginación.
- Catálogo completo de la API en español con caché de 24 horas, validación de todas sus páginas y copia anterior como respaldo ante fallo de red.
- Consultas de datos con fuente explícita y códigos que distinguen mayúsculas/minúsculas, compatibles con la selección del catálogo.
- Desconexión individual de enlaces desde el inspector o desde su línea seleccionada, sin eliminar módulos y con Deshacer.
- Pruebas de catálogo, paginación, integridad de caché, fallo de red y propagación de la fuente a wbdata.

## 0.2.0 - 2026-11-01

- Alpha local React/React Flow con canvas, inspector, búsqueda de nodos, conexiones, deshacer y panel de resultados.
- Motor Python JSON-RPC con validación de DAG, límites de carga, errores por nodo y aislamiento de ramas.
- Fuentes simuladas con semilla, CSV y consulta anual World Bank; descriptivos, dispersión y OLS simple clásico/HC3.
- Ventana de ecuación con modelo poblacional, recta estimada y definiciones usando los coeficientes reales.
- Guardar/abrir proyectos JSON y exportar resultados con snapshots, versiones y huellas SHA-256.
- Locks Python/npm, esquema JSON compartido y pruebas científicas con fixtures conocidos.
- Integración Tauri preparada; compilación nativa, Cargo.lock y sidecar empaquetado pendientes por falta de Rust.
- P1 sigue abierta; C01-C04/C09 parcialmente implementados.

## 0.1.0 - 2026-11-01

- Diseño de aplicación educativa de escritorio macOS/Windows con canvas de nodos, Tauri, React y motor científico Python.
- Inventario de 36 capítulos con huellas SHA-256 y cobertura curricular en 28 módulos.
- Contratos propuestos de IPC/DAG, trazabilidad de datos, diagnósticos científicos, lecciones, accesibilidad y distribución.
- Plan por fases, versiones observadas/propuestas y decisiones pendientes.
- Script de commits/push con alcance controlado, validación documental, pruebas y CI macOS/Windows.
- Bibliografía original y datasets privados excluidos de Git.

La aplicación y sus instaladores están pendientes de implementación. Los cambios de publicación se verifican en Git, sin registrar un SHA autorreferente en esta entrega.

## 0.5.0 · 2026-11-01

- Estudio oscuro inspirado en Quantlabs-Blueprints: biblioteca, canvas, inspector y resultados. Fuentes locales; mejor contraste de controles y tablas.
- Electron 45.2.1 con RPC stdio, procesos Python acotados y cierre completo; recargar, reiniciar y salir. Recuperación del grafo al recargar.
- Consulta de GitHub Releases con estado explícito cuando no existen versiones publicadas; distribución firmada y actualización automática siguen pendientes.
- Recta OLS amarilla brillante, mayor grosor, leyenda y cuadrícula atenuada.
- Pruebas Node de ciclo de vida y validación IPC integradas en sync.py.

## 0.5.1 · 2026-11-01

- Botón visible Nuevo proyecto en la barra principal, con protección de cambios sin guardar.
- Canvas vacío con instrucciones y acceso directo a datos simulados; ejecutar permanece deshabilitado sin nodos.

## 0.5.2 · 2026-11-01

- Corrección de caché wbdata compartida dañada: cada proceso usa una caché temporal aislada, incluso durante la importación del paquete. Conserva cachés anteriores y catálogo JSON.
- Dispersión muestra las columnas disponibles ante un error y ofrece configurar periodo/valor al conectarse con Banco Mundial.

## 0.5.3 · 2026-11-01

- Código completo, nombre y fuente del indicador con ajuste de línea; metadatos seleccionados conservados en el proyecto.
- Listas de variables para OLS y Dispersión, intercambio X/Y, contexto de la serie y vista de datos. Selección por casillas para regresores/instrumentos y columnas múltiples en modelos y transformaciones.
- Carga de columnas desde la tabla conectada; esquema numérico explícito del motor, separado por puerto. Invalida al cambiar indicador, datos o conexiones, sin reutilizar resultados anteriores.
- Selección inicial periodo/valor al conectar World Bank a OLS o Dispersión con sus parámetros originales; no sustituye elecciones personalizadas.
- Pulsar el código abre un diálogo flotante amplio con selección actual, nombre, código completo, fuente, búsqueda y lista paginada.

## 0.5.4 · 2026-11-01

- Catálogo oficial de 217 países/economías y 79 regiones/agregados del Banco Mundial, en español, integrado para consulta sin conexión.
- Selector flotante con búsqueda por nombre/ISO 2/ISO 3 y estrellas de favoritos. Favoritos persistentes por perfil local y al inicio de la lista; marcar estrella no modifica el país del proyecto.
- Script de actualización valida páginas, totalidad y unicidad antes de sustituir el catálogo. Pruebas de filtro, orden y recuperación de preferencias.

## 0.5.5 · 2026-11-01

- Histograma visible como barras, con variable, intervalos, frecuencias, observaciones válidas y faltantes; conserva tabla numérica.
- Seleccionar un nodo abre Resultados. Modelos y transformaciones adicionales muestran su salida en proyectos libres, además de los recorridos guiados.
- El número de observaciones del nodo Histograma corresponde a los valores utilizados, excluyendo faltantes.

## 0.6.0 · 2026-11-01

- Ojo por nodo para mostrar/ocultar su salida. Resultados agrupa las salidas visibles y la regresión conserva acceso propio.
- Recomendaciones al situarse, enfocar o pulsar una salida, basadas en sus tipos de puerto. Añadir y conectar en un paso; entradas adicionales pendientes explícitas.
- Conserva cálculos de nodos/ancestros sin cambios al editar ramas independientes. Invalida dependientes al cambiar datos o especificación, marcando pendientes y manteniendo trazabilidad del cálculo original.

## 0.7.0 · 2026-11-02

- Nueva fuente Wooldridge con 115 conjuntos locales, catálogo, búsqueda, tipos y faltantes. wooldridge 0.5.0 fijado en pyproject.toml y uv.lock.
- Carga copia completa mediante wd.data(name).copy(); al elegir otro conjunto actualiza columnas y retira modelos dependientes anteriores.
- Capacidad de tablas ampliada a 50.000 filas/100 columnas; conjuntos mayores de 10.000 filas exportan solo 1.000 registros de muestra en JSON, con indicación explícita. Cálculos y huella conservan todas las filas.
- Presentación de floats Wooldridge con seis decimales sin modificar datos ni redondear cálculos.

## 0.7.1 · 2026-11-02

- Recomendaciones de salida solo con doble clic, o Enter para teclado; elimina activación por hover, foco o clic simple.
- OLS múltiple conectado a wage1 ofrece ejemplo wage ~ educ + exper + tenure con HC3. Respuesta aparece primero y no puede marcarse como regresor.
- Elegir casillas retira nombres inexistentes y repetidos; los errores identifican qué columnas faltan o están duplicadas.

## 0.7.2 - 2026-11-02

- Pestaña Regresión para OLS simple y múltiple, con selección persistente del modelo, coeficientes, intervalos y métricas.
- Ecuación múltiple junto a Proyectos: especificación, estimación numérica y explicación de variables; ecuación simple conservada.
- Resultados estructurados de OLS múltiple contrastados con statsmodels HC3.
