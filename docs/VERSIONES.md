# Versiones, entorno y decisiones

Registro inicial: 2026-11-01, zona America/Mexico_City. Versión canónica del proyecto: archivo `VERSION` = **0.8.4**. Alpha local con dependencias frontend/Python instaladas y lockfiles. Electron local ejecutado en macOS; instaladores y Tauri compilado siguen pendientes. Las versiones objetivo son decisiones de diseño y no se presentan como las últimas disponibles.

## Entorno observado

| Componente | Valor observado | Uso |
|---|---|---|
| Git | 2.53.0 | Inicialización, commits y push |
| Python del sistema | 3.15.0 | Disponible; no es el motor científico |
| Python del entorno .venv | 3.12.12 | Motor y pruebas científicas |
| Node.js | v22.22.3 | Disponible; frontend no instalado |
| Rust | No disponible en PATH | Pendiente para compilar Tauri |
| pdftotext | Disponible en /opt/homebrew/bin | Extracción local de los 36 PDF |
| Sistema | macOS, zsh | Host de preparación, sin validar builds destino |

## Stack adoptado en 0.2.0

Locks: `apps/desktop/package-lock.json` y `uv.lock`. Instalación reproducible con npm ci y uv sync --frozen. Licencias obtenidas de metadatos instalados; se debe revisar el conjunto transitivo antes de distribuir binarios.

| Componente | Versión exacta | Licencia / estado |
|---|---|---|
| React / React DOM | 19.3.1 | MIT |
| @xyflow/react | 12.12.0 | MIT |
| @tauri-apps/api / CLI | 2.12.4 | MIT OR Apache-2.0 |
| lucide-react | 1.66.0 | ISC |
| TypeScript | 7.0.2 | Apache-2.0 |
| Vite | 8.3.5 | MIT |
| @vitejs/plugin-react | 6.1.2 | MIT |
| NumPy | 2.5.4 | BSD-3-Clause y licencias de componentes vendorizados |
| pandas | 3.1.0 | BSD-3-Clause |
| statsmodels | 0.15.0 | BSD-3-Clause |
| wbdata | 1.1.0 | GPL-2.0+; revisar obligaciones al distribuir la aplicación |
| Tauri Rust / tauri-build | 2.12.5 / 2.7.4 | Fijados en Cargo.toml, no instalados ni compilados |
| serde_json | 1.0.145 | Fijado en Cargo.toml, sin Cargo.lock todavía |

Dependencias de tipos: @types/react 19.3.0, @types/react-dom 19.3.0 y @types/node 26.6.6. Versiones transitivas exactas en sus lockfiles.

## Diseño inicial y componentes pendientes

La siguiente tabla conserva la propuesta inicial de 0.1.0. Los componentes ya adoptados se rigen por la tabla anterior; las alternativas restantes no se han instalado.

| Componente | Objetivo | Estado de versión exacta |
|---|---|---|
| Python científico | 3.12.x inicialmente | Seleccionar patch y verificar ruedas |
| Tauri | Línea 2 | Fijar crates/CLI juntos y Cargo.lock en P1 |
| React Flow | Paquete @xyflow/react, línea 12 de referencia | Fijar versión compatible en P1 |
| React, TypeScript, Vite, Zustand, Plotly.js | Selección en P1 | No instalados; fijar npm lockfile |
| pandas, NumPy, SciPy, statsmodels | Motor científico | Fijar versiones y lock Python tras pruebas |
| arch | Volatilidad univariada | Validar parámetros, convergencia y empaquetado |
| wbdata | World Bank | Comprobar firma, paginación y tratamiento de fechas |
| PyArrow, openpyxl | Parquet y Excel | Fijar según runtime científico |
| scikit-learn, hmmlearn, semopy, linearmodels | Candidatos para extensiones | Evaluar API, licencia y compatibilidad; no adoptados |
| PyInstaller | Empaquetado Python | Fijar después de validar por target |
| SQLite | Biblioteca del runtime Python | Registrar sqlite_version en manifiestos |

## Reglas

1. Cambiar VERSION con SemVer: patch para correcciones compatibles, minor para módulos compatibles, major para incompatibilidades públicas. Mientras sea 0.x, documentar también cambios incompatibles.
2. No incrementar versión por cada guardado; agrupar una unidad funcional, documentar CHANGELOG.md y crear commit.
3. Antes de introducir dependencias: fijar versión exacta y lockfile, registrar licencia, motivo y compatibilidad. No usar etiquetas flotantes como garantía de reproducibilidad.
4. La versión del esquema JSON y de cada nodo se registra aparte y requiere migración explícita.
5. Cada ejecución debe capturar versiones reales del motor y bibliotecas; no confundirlas con objetivos de esta tabla.
6. El commit identifica el árbol exacto. No se incrusta su propio SHA en el mismo commit: usar `git rev-parse HEAD`, historial y manifiestos posteriores.

## Decisiones de arquitectura

| ID | Fecha | Decisión | Revisión |
|---|---|---|---|
| ADR-001 | 2026-11-01 | Tauri + React + motor Python | Revisar al validar builds en P1 |
| ADR-002 | 2026-11-01 | JSON-RPC por stdio; no servidor HTTP inicial | Revisar si se requiere API remota |
| ADR-003 | 2026-11-01 | PDF y datasets privados fuera de Git | Publicar solo inventarios y ejemplos sintéticos |
| ADR-004 | 2026-11-01 | Commits y push al cerrar unidades de trabajo | Script invocable y regla persistente en AGENTS.md |

Fuentes técnicas consultadas: [Tauri](https://v2.tauri.app/develop/sidecar/) y [React Flow](https://reactflow.dev/), 2026-11-01. No se afirma haber verificado patches de paquetes todavía no adoptados.

## Decisiones de implementación 0.2.0

- ADR-005: puente HTTP limitado a loopback durante desarrollo, mientras Tauri se valida. El puente lanza el mismo protocolo stdio; el build estático no incluye servidor.
- ADR-006: primer gráfico de dispersión SVG integrado, sin Plotly/Zustand todavía. Estado React y guardado JSON; las bibliotecas propuestas se adoptarán cuando una necesidad concreta lo justifique.
- ADR-007: snapshots JSON con 15 decimales y errores por nodo; Parquet, SQLite, caché del DAG, progreso y cancelación permanecen pendientes.
- ADR-008: implementación inicial de OLS simple para verificar el circuito datos-modelo-resultado; no cerrar C09 ni P2 antes de inferencia, lecciones y auditoría bibliográfica.

## Entrega 0.2.1

Sin dependencias nuevas. Se sincronizaron VERSION, pyproject.toml/uv.lock, package.json/package-lock.json, versión de interfaz y configuración Tauri en 0.2.1. Protocolo, esquema de proyecto y versiones de nodo siguen en 1.0.0; `source` es un parámetro opcional del nodo World Bank, con valor por defecto 2 para proyectos anteriores.

Catálogo consultado el 2026-11-01: 29.544 filas de metadatos, reducidas a 29.533 pares únicos de fuente/código. Este conteo es una observación, no una constante de aplicación. Fuente: https://api.worldbank.org/v2/es/indicator. Nombres en español cuando los entrega el proveedor; la consulta puede no tener observaciones para ciertos países, años o frecuencias.

## Entrega 0.3.0

Se adoptan arch 8.0.0 (NCSA), scikit-learn 1.9.1 (BSD-3-Clause), hmmlearn 0.3.3 y semopy 2.3.11. Los metadatos instalados de las dos últimas no declaran una licencia; queda pendiente cotejar sus archivos de licencia antes de distribuir binarios. Todas están fijadas exactamente en pyproject.toml y uv.lock. Las versiones transitivas, incluido scipy, permanecen en el lock; la ejecución registra sus versiones reales. No se adopta una licencia global del proyecto automáticamente.

VERSION, pyproject.toml/uv.lock, package.json/package-lock.json, interfaz y configuración Tauri pasan a 0.3.0. Esquema de proyecto/protocolo/nodos: 1.0.0. Se añade el tipo experiment y métodos de proyectos/ejemplos/auditoría. Los proyectos previos se conservan compatibles; las aplicaciones antiguas rechazan el nuevo tipo de nodo.

ADR-009: archivos JSON locales con papelera y revisión esperada para el administrador inicial, sin esperar a SQLite. Las mutaciones se serializan con bloqueo del sistema operativo y escrituras atómicas.

ADR-010: catálogo de experimentos registrados C01-C28, ejecutables con n/semilla y tablas/interpretaciones. Su alcance introductorio no cierra módulos. El código científico no procede del JSON del usuario.

ADR-011: el borrador permite cero nodos o entradas incompletas; ejecutar exige un grafo listo. La interfaz muestra esa diferencia y conserva archivos inválidos sin intentar repararlos de forma destructiva.

## Entrega 0.4.0

No se añaden dependencias. Las versiones exactas de bibliotecas siguen en uv.lock/package-lock.json. VERSION, pyproject.toml/uv.lock, frontend y Tauri se sincronizan en 0.4.0. El catálogo de ejemplos pasa a revisión 2.0.0; el esquema de proyectos y protocolo siguen en 1.0.0 con extensiones aditivas (lesson, nuevos tipos y target_node). Aplicaciones anteriores rechazan herramientas que desconocen.

ADR-012: el contrato compartido packages/contracts/nodeCatalog.json define herramientas, puertos, parámetros, opciones y explicaciones. Frontend y backend consumen el mismo archivo; la compatibilidad de puertos se valida en ambos extremos.

ADR-013: cada ejemplo usa un grafo con generador, transformaciones/estimadores y reporte independientes. experiment se conserva para abrir archivos 0.3.0, pero ningún ejemplo del catálogo lo utiliza.

ADR-014: ejecutar un paso recalcula su clausura de dependencias, no los nodos posteriores. No se introduce una caché persistente ni se declara soporte de cancelación. La interfaz solo acumula resultados de pasos con grafo y huellas comunes iguales.

## Entrega 0.5.0

ADR-007: adoptar Electron como ruta de escritorio activa a petición del usuario, con estudio oscuro siguiendo Quantlabs-Blueprints. Electron **45.2.1**, obtenido del registro npm oficial e instalado con versión exacta el 2026-11-01; package-lock.json registra dependencias e integridades. React, Vite, TypeScript y bibliotecas científicas conservan sus versiones. VERSION, paquetes, lockfiles, frontend y metadatos Tauri pasan a 0.5.0; protocolo/esquema/nodos siguen 1.0.0. Detalles, fuentes y límites: [ELECTRON.md](ELECTRON.md).

## Entrega 0.5.1

Sin dependencias nuevas. Versiones de aplicación y lockfiles sincronizadas en 0.5.1. Inicio de proyecto vacío accesible desde la barra principal.

## Entrega 0.5.2

Sin dependencias nuevas; metadatos y lockfiles sincronizados en 0.5.2. wbdata 1.1.0 conserva su versión y usa shelve temporal por proceso. No se modifica el catálogo JSON persistente ni se borran cachés anteriores.

## Entrega 0.5.3

Sin dependencias nuevas. Versiones y lockfiles sincronizados en 0.5.3. Node 22.22.3 ejecuta las pruebas TypeScript de selección mediante --experimental-strip-types. Esquema/protocolo siguen 1.0.0: numeric_columns y metadatos de indicador son extensiones aditivas.

## Entrega 0.5.4

Sin dependencias nuevas. Metadatos y lockfiles en 0.5.4. Catálogo público de países revisión 1 descargado del API oficial del Banco Mundial; fuente y hora UTC exacta en packages/contracts/worldbankCountries.json. No contiene observaciones económicas.

## Entrega 0.5.5

Sin dependencias nuevas. Metadatos y lockfiles sincronizados en 0.5.5. Histograma añade metadatos aditivos de intervalos/frecuencias para representación SVG local; esquema/protocolo siguen 1.0.0.

## Entrega 0.6.0

Sin dependencias nuevas; aplicación y lockfiles en 0.6.0. Contratos/protocolo/nodos siguen 1.0.0. Retención de resultados y recomendaciones son funciones de interfaz probadas sobre firmas de ancestros y tipos del registro.

## Entrega 0.7.0

Nueva dependencia **wooldridge==0.5.0**, consultada e instalada desde PyPI el 2026-11-02. uv.lock fija integridad y resolución; resto de dependencias sin cambios. Metadatos de aplicación y lockfiles en 0.7.0; esquema/protocolo/nodos siguen 1.0.0 con nuevo tipo wooldridge. Catálogo generado de la instalación: 115 conjuntos, con fuente/versión/hora exactas y solo metadatos. [Guía](WOOLDRIDGE.md).

## Entrega 0.7.1

Sin dependencias nuevas. Aplicación y lockfiles sincronizados en 0.7.1. Protocolo/esquema/nodos siguen 1.0.0. Ejemplo OLS múltiple verificado con statsmodels sobre wage1.

## 0.7.2 · 2026-11-02

Corrección de la pestaña Regresión y ecuación múltiple; misma selección de modelo entre pestaña y diálogo. OLS simple conserva su ecuación y gráfico. Sin cambios de dependencias.

## 0.7.3 · 2026-11-03

Arrancadores de fuente para macOS y Windows. Node >=22 y uv son requisitos externos; uv prepara Python 3.12. Sin nuevas dependencias. Se utiliza npm ci con package-lock y uv sync --frozen; no se instalan herramientas globales. README muestra versiones declaradas en los manifiestos, sin atribuir a Econometrics releases de Blueprints ni PyTorch. Ver docs/ARRANQUE.md para límites de verificación.

## 0.7.4 · 2026-11-03

Serie temporal incorpora el tipo time_plot al registro compartido (55 herramientas), calculado con pandas y representado mediante SVG de React. Sin dependencias nuevas. Pruebas de calendario, faltantes, validación e integración CSV; compilación TypeScript. La disponibilidad de datos del ejemplo Banco Mundial depende del servicio externo.

## 0.7.5 · 2026-11-03

Ajuste visual de Serie temporal: grosor de 3,5 a 2,5 unidades SVG, leyenda a juego y radio de puntos de 3 a 2. Sin cambios de dependencias ni cálculos.

## 0.7.6 · 2026-11-03

Color configurable de Serie temporal mediante parámetro hexadecimal validado. Selector nativo HTML de color; sin nuevas dependencias. Proyectos anteriores conservan verde al omitir el parámetro.

## 0.8.0 · 2026-11-03

Cuatro nodos nuevos, 59 herramientas registradas. Unión exterior por período sin duplicados; media por columnas; diagnósticos descriptivos y de residuos. SciPy ya era dependencia transitiva del stack científico; no se incorporan paquetes. Shapiro limitado a n≤5000 sin submuestreo silencioso; Q–Q muestra hasta 400 cuantiles y pruebas usan todos los observados. Ejemplo N01 se distribuye con el frontend sin alterar los 28 módulos del catálogo curricular. Disponibilidad remota no sustituye la prueba de integración sin red.

## 0.8.1 · 2026-11-03

Boxplot añade el tipo 60. Cálculo NumPy con cuartiles lineales y bigotes 1,5×RIC; SVG React. Sin dependencias nuevas. Pruebas numéricas y CSV; compilación frontend.

## 0.8.2 · 2026-11-03

Boxplot mantiene el tipo (60 herramientas) y añade salida Dataset y tratamiento condicional por media. Comparadores en lista cerrada, sin eval; media original y faltantes conservados. Parámetros compatibles con proyectos anteriores; selector visible aunque no incluyan operator. Sin nuevas dependencias.

## 0.8.3 · 2026-11-03

Resultados utiliza el mismo panel de salidas visibles en proyectos libres y recorridos guiados. Se retira la rama que limitaba los recorridos a una sola salida. Navegación por tarjetas y pasos abre Resultados; Regresión conserva su panel propio. Sin cambios científicos ni dependencias.

## 0.8.4 · 2026-11-03

61 tipos: covariance_matrix añade covarianza de variables Dataset → Result. Correlación conserva sus dos matrices y ambas salidas se muestran por defecto. Pearson y covarianza ddof=1 mediante pandas; filas completas comunes y constantes no definidas explícitas. Sin nuevas dependencias. Pruebas numéricas e integración CSV.
