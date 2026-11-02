# Auditoría funcional y correcciones de sistemas

Versión 0.4.0 · 2026-11-01 · Alcance: aplicación local React/Python, contratos, ejemplos, persistencia, integridad y ciclo de trabajo. No es certificación de seguridad, auditoría de todos los capítulos ni validación de instaladores inexistentes.

## Hallazgos corregidos

| ID | Prioridad | Evidencia anterior | Implementación | Verificación |
|---|---|---|---|---|
| A01 | Alta | Guardar solo descargaba un archivo; no existía biblioteca administrada | Espacio local .quantlabs/projects, lista, lectura, guardado, actualización y copias | Ciclo guardar/abrir/editar/guardar en backend y navegador |
| A02 | Alta | No había borrado recuperable | Papelera local y restauración; ejemplos originales inmutables | Pruebas de mover/restaurar conservando proyecto y revisión |
| A03 | Alta | Dos sesiones podían sobrescribir el mismo proyecto | Revisión SHA-256 esperada, bloqueo entre procesos y escritura mediante temporal + reemplazo atómico | Revisión obsoleta rechazada, exclusión entre procesos probada y fallo de escritura conserva archivo anterior |
| A04 | Alta | Un flujo sin conexiones no podía guardarse | Validación de borrador separada de la validación de ejecución; se admiten proyectos vacíos | Guardado permitido; ejecución bloqueada con error claro |
| A05 | Alta | Solo había un ejemplo y ningún catálogo por módulo | 28 experimentos ejecutables C01-C28 con objetivos, preguntas, subtemas y referencias B01-B36 | Prueba que ejecuta los 28; cobertura de IDs y referencias |
| A06 | Media | No existía editor JSON en la aplicación | Ver, importar, editar, validar, aplicar al canvas, ejecutar, guardar y exportar JSON | Prueba visual del recorrido; errores conservan el texto |
| A07 | Media | La recta OLS podía dibujarse sobre otro dataset con nombres iguales | Propagación de identidad de fuente y verificación antes de superponer | Inspección de contrato y condición de render; los nombres solos ya no bastan |
| A08 | Media | IDs de conexiones duplicados no se detectaban | Unicidad de IDs de conexiones en el validador | Prueba de rechazo |
| A09 | Media | Archivos dañados podían impedir la lista completa | Verificación de JSON, metadatos, revisión e identidad; errores individuales se informan y conservan | Pruebas con JSON roto y metadatos incompletos |
| A10 | Media | Desconectar era poco visible | Texto Desconectar en el inspector, además del botón de línea y teclado | Flujo ya probado de desconexión y Deshacer; affordance ampliada |
| A11 | Media | Cerrar el navegador podía perder cambios sin aviso | Indicador de estado y aviso beforeunload al editar canvas o proyecto | Revisión de estado; no implica autoguardado |
| A12 | Media | No había estado auditable dentro de la app | Pestaña Auditoría: catálogo, referencias, escritura, integridad y pendientes | Prueba del endpoint y revisión en navegador |

## Límites que siguen abiertos

- **Currículo:** hay un experimento introductorio por módulo, no cobertura exhaustiva de cada subtema. GARCH multivariado, EGARCH, GMM general, panel y pruebas avanzadas requieren desarrollo y validación específicos.
- **Editor de nodos:** los ejemplos se reconstruyeron como herramientas independientes conectables. Siguen pendientes los estimadores y opciones de la matriz de HERRAMIENTAS.md.
- **Escritorio:** falta Rust, Cargo.lock, PyInstaller bloqueado, builds, firma/notarización y pruebas de instalación macOS/Windows. La aplicación sigue funcionando en modo local de desarrollo.
- **Ejecución:** procesos por solicitud, plazo máximo de 60 segundos, sin cola persistente, cancelación ni recuperación de una ejecución interrumpida.
- **Persistencia:** archivos JSON locales con papelera; sin sincronización remota, backups externos, auto guardado o SQLite/Parquet. Borrar datos del directorio local manualmente queda fuera del mecanismo de recuperación.
- **Ciencia:** las pruebas comprueban ejecución de los 28 ejemplos y propiedades conocidas de algunos generadores. No son una comparación exhaustiva de todos los resultados con implementaciones independientes. Advertencias de convergencia se muestran; no se ocultan.
- **Accesibilidad y plataformas:** TypeScript/build y suites locales comprobados; CI macOS/Windows debe terminar antes de afirmar verificación remota. Falta una auditoría de accesibilidad completa.

## Comprobación reproducible

```sh
uv run python scripts/check_docs.py
uv run python -m unittest discover -s tests -v
npm run build --prefix apps/desktop
```

Las pruebas usan directorios temporales para guardar, editar, borrar y restaurar. No modifican proyectos personales. La auditoría de la app usa un archivo temporal de prueba que elimina al terminar, valida estructuras y lee metadatos; no ejecuta todos los modelos cada vez que se abre.

Fuentes de implementación científica consultadas el 2026-11-01: [arch](https://arch.readthedocs.io/en/latest/univariate/introduction.html), [hmmlearn](https://hmmlearn.readthedocs.io/en/latest/tutorial.html), [semopy](https://semopy.com/tutorial.html) y [scikit-learn MLP](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPRegressor.html). Las versiones adoptadas y sus licencias están en VERSIONES.md; las APIs se verificaron también contra las instalaciones bloqueadas.

## Hallazgos al construir los módulos con la propia aplicación (0.4.0)

| ID | Carencia encontrada | Corrección implementada | Evidencia |
|---|---|---|---|
| A13 | Las recetas impedían inspeccionar datos y pasos intermedios | 28 grafos sin experiment; 131 pasos explicados | Todos los ejemplos ejecutados con una prueba que prohíbe llamar la receta anterior |
| A14 | El canvas solo suponía entrada/salida data | Contrato compartido, puertos múltiples y artefactos de modelo/transformador/resultado | Validación de puertos, tipos y ciclos; build TypeScript |
| A15 | No podía usarse la estimación de un nodo en otro | Modelos ajustados conectados a diagnóstico, evaluación, covarianza y comparación | Pruebas de datos conectados y coeficientes conocidos |
| A16 | No había una forma explícita de aprender el escalador solo en train | split → standardize(train) → apply_scaler(test) | Fixture con valores extremos en prueba: la media del escalador sigue siendo la de entrenamiento |
| A17 | Cada clic ejecutaba todo el módulo | Ejecución de la clausura de ancestros con target_node | Pruebas de prefijos y ramas incompletas ajenas |
| A18 | La guía no explicaba qué revisar | Instrucciones, ecuación generadora, resultado esperado, salida por nodo y preguntas | Recorrido manual y validación de todas las referencias de pasos |
| A19 | Podían tratarse años ausentes como filas adyacentes | Rechazo explícito de calendario irregular y de compresión de faltantes temporales | Fixture de períodos 2000, 2001, 2003, 2004 rechazado al crear rezagos |

La lista de lo que falta ahora proviene de reconstruir cada recorrido con puertos reales. Se publica por módulo en HERRAMIENTAS.md y en cada guía. No se afirma soporte de métodos pendientes, como GARCH multivariado o GMM de momentos general; la herramienta gmm existente significa mezcla gaussiana y lo indica expresamente.

## Revisión 0.5.0

Electron incorporado con renderer aislado, origen/frame IPC validado, límites de procesos y terminación explícita. Las fuentes remotas fueron retiradas. Recta de regresión contrastada sobre estudio oscuro. Continúan pendientes instaladores, Python redistribuible, firma y actualización automática; consultar Releases no acredita esas capacidades. [Detalle](ELECTRON.md).
