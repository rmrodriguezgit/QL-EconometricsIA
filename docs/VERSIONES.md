# Versiones, entorno y decisiones

Registro inicial: 2026-11-01, zona America/Mexico_City. Versión canónica del proyecto: archivo `VERSION` = **0.1.0**. Diseño inicial, sin dependencias de aplicación instaladas ni lockfiles. Las versiones objetivo son decisiones de diseño y no se presentan como las últimas disponibles.

## Entorno observado

| Componente | Valor observado | Uso |
|---|---|---|
| Git | 2.53.0 | Inicialización, commits y push |
| Python | 3.15.0 | Herramientas documentales de biblioteca estándar |
| Node.js | v22.22.3 | Disponible; frontend no instalado |
| Rust | No disponible en PATH | Pendiente para compilar Tauri |
| pdftotext | Disponible en /opt/homebrew/bin | Extracción local de los 36 PDF |
| Sistema | macOS, zsh | Host de preparación, sin validar builds destino |

## Stack propuesto, pendiente de bloqueo exacto

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
