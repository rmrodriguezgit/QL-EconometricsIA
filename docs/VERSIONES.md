# Versiones, entorno y decisiones

Registro inicial: 2026-11-01, zona America/Mexico_City. Versión canónica del proyecto: archivo `VERSION` = **0.4.0**. Alpha local con dependencias frontend/Python instaladas y lockfiles. La compilación nativa sigue pendiente. Las versiones objetivo son decisiones de diseño y no se presentan como las últimas disponibles.

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
