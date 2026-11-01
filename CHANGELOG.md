# Historial de cambios

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
