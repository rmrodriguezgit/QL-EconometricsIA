# Escritorio Electron y estudio visual

Versión 0.5.0 · 2026-11-01 · modo desarrollo supervisado 0.11.1 · 2026-11-04.

## Arrancar

Desde la raíz del checkout:

```bash
uv sync
npm ci --prefix apps/desktop
npm run desktop --prefix apps/desktop
```

El último comando compila React y abre Electron con los archivos locales, sin Vite, servidor HTTP ni Rust. El motor usa el Python de .venv y los proyectos de este checkout. Se requiere conservar el repositorio y su entorno Python: esta entrega todavía no es un instalador independiente.

### Modo desarrollo con recarga (0.11.1)

Un solo proceso supervisor (`scripts/desktop-dev.cjs`) arranca Vite **dentro de su propio proceso** y abre Electron sobre `http://127.0.0.1:1420`:

```bash
npm run desktop:dev --prefix apps/desktop
```

En macOS también sirve el doble clic en `Arrancar-Quantlabs-Dev.command` (equivale a `node scripts/launch.cjs --dev`: prepara dependencias como el arrancador normal pero no compila).

| Qué cambias | Qué ocurre |
|---|---|
| `apps/desktop/src/**` (React, CSS) | Recarga en caliente (HMR) sin perder la ventana. |
| `packages/contracts/*.json` | Vite recarga la interfaz. |
| `engine/quantlabs/**` (Python) | Efecto inmediato en el siguiente cálculo: cada RPC arranca un proceso Python nuevo. |
| `apps/desktop/electron/main.cjs`, `runtime.cjs`, `preload.cjs` | El supervisor reinicia Electron automáticamente. |
| Tras `git pull` | Basta con Cmd/Ctrl+Shift+R (recarga sin caché); si cambió `package-lock.json`, sal y ejecuta `npm ci --prefix apps/desktop`. |

**Cierre sin procesos residentes.** «Salir por completo» (Cmd/Ctrl+Q), cerrar la ventana, Ctrl+C en la terminal o cerrar la terminal terminan Electron, Vite y los procesos Python en curso. «Reiniciar aplicación» pide el reinicio al supervisor (código de salida 75) en vez de lanzar un Electron huérfano. Electron vigila al supervisor y se cierra si este muere, incluso con `kill -9`; como Vite corre en el mismo proceso que el supervisor, tampoco queda huérfano. Verificado en macOS el 2026-11-04 con los cuatro casos (salida de la app, Ctrl+C, `kill -9` del supervisor y reinicio por cambio de `preload.cjs`): ningún proceso Electron, Vite ni Python restante.

## Controles

- Recargar interfaz, también Cmd/Ctrl+R: reinicia React y conserva el grafo en sessionStorage. Los resultados se recalculan al ejecutar. Un proyecto sin guardar pide confirmar el descarte del estado visible; la copia del grafo de la sesión sigue disponible al recargar. Guardar proyecto conserva además el JSON en Mis proyectos.
- Recargar sin caché, Cmd/Ctrl+Shift+R: útil tras actualizar el código en modo desarrollo.
- Reiniciar aplicación: cierra la instancia y vuelve a arrancar Electron (en modo desarrollo lo hace el supervisor). Guardar primero: la recuperación de sesión cubre recarga, no promete persistencia del borrador tras salir.
- Salir por completo, también Cmd/Ctrl+Q: cierra ventanas, cancela cálculos activos, termina sus procesos Python y sale incluso en macOS. Cerrar la última ventana tiene el mismo efecto; no hay bandeja ni servicio residente.
- Buscar actualizaciones: consulta el último GitHub Release del repositorio propio. Compara versiones numéricas y ofrece una URL fija de Releases. No descarga ni ejecuta instaladores automáticamente. Un 404 se presenta como ausencia de releases, no como aplicación actualizada.

Actualizar el checkout: guardar proyectos, salir, ejecutar git pull --ff-only, uv sync y npm ci --prefix apps/desktop; después arrancar de nuevo. No ejecutar git pull desde el renderer ni reemplazar dependencias mientras se calcula.

## Espacio de trabajo a pantalla completa (0.12.0)

El botón **Ampliar** (icono de flechas, junto a *Ejecutar flujo*) hace que el lienzo ocupe toda la ventana para revisar grafos grandes. Biblioteca, inspector, guía y resultados quedan ocultos; el grafo se reencuadra automáticamente. Una barra flotante muestra el nombre del proyecto, nodos y conexiones, y ofrece **Encuadrar**, **Ejecutar** y **Volver al layout**. `Esc` también regresa al layout normal; si hay un diálogo abierto (Cerebro IA, Proyectos, Ecuación), `Esc` lo cierra primero. Los diálogos se muestran por encima del lienzo ampliado. Ocupa la ventana, no el monitor: para el monitor completo combínalo con *Vista → Pantalla completa* de Electron.

### Resultados a pantalla completa (0.12.1)

El botón **Ampliar** de la cabecera de resultados (junto a *Exportar*) extiende el área **Resultados · Regresión · Descriptivos · Trazabilidad** a toda la ventana. Las pestañas quedan fijas arriba mientras el contenido se desplaza, y siguen funcionando. **Volver al layout** o `Esc` restauran la disposición. Ampliar el lienzo cierra la ampliación de resultados y viceversa; solo una vista ampliada a la vez.

## Interfaz

Referencia revisada: [Quantlabs-Blueprints](https://github.com/rmrodriguezgit/Quantlabs-Blueprints), concretamente su renderer/styles.css y main/main.ts, 2026-11-01. Se adopta la organización de estudio oscuro con biblioteca, canvas, inspector y resultados, conservando los contratos, ejemplos y motor de Econometrics. No se cambia el remoto Git.

La recta OLS es amarilla brillante (#ffd166), de 3 px y con leyenda; los puntos permanecen verdes. La cuadrícula se atenúa. Se eliminaron fuentes remotas para que el escritorio funcione sin descargarlas.

## Rendimiento: multiproceso e hilos (0.17.0)

Antes, cada solicitud arrancaba un Python nuevo y volvía a cargar pandas, statsmodels y scikit-learn (~1,1 s por clic) aunque el cálculo durase milisegundos. Ahora hay tres niveles de paralelismo:

| Nivel | Qué hace | Ajuste |
|---|---|---|
| **Procesos persistentes** (`electron/runtime.cjs`) | Grupo de trabajadores `python -m quantlabs` que atienden una solicitud tras otra por stdin/stdout. Al abrir la app se precargan 2 (`engine.warmup`); crecen bajo demanda hasta el máximo, y los extra se cierran tras 60 s ociosos. Cada proceso se reemplaza tras 200 solicitudes. Varias solicitudes (ejecutar, buscar indicadores, Cerebro IA) corren a la vez en procesos distintos. | `QL_ENGINE_WORKERS` (por defecto núcleos − 1, máximo 4) |
| **Hilos por ejecución** (`engine/quantlabs/core.py`, `parallel.py`) | Los nodos sin dependencia entre sí se calculan a la vez; el orden del informe y las huellas no cambian. Los avisos se capturan por hilo para no mezclarse. | `QL_ENGINE_THREADS` (por defecto núcleos, máximo 8; `1` = secuencial) |
| **Procesos dentro de un nodo** | `GridSearchCV` de la optimización de hiperparámetros usa varios procesos solo cuando filas × variables × ajustes supera 2 millones; con muestras de clase sigue en uno, porque arrancar procesos costaría más. | `QL_ENGINE_PROCESSES` (`1` = desactivado) |

Mediciones en este equipo (macOS, 8 núcleos):

| Caso | Antes | Ahora |
|---|---|---|
| Ejecutar el ejemplo C22 desde la interfaz (puente) | 1,03–1,10 s | 0,033 s (primera solicitud tras arrancar Vite: 1,15 s; en Electron ya está precargado) |
| Flujo inicial (4 nodos) desde la interfaz | — | 66–69 ms |
| Ramas pesadas (n = 10 000: 2 MLP, cuantiles, k-means, búsqueda lasso) | 3,15 s | 2,29 s con hilos |
| Cuatro series del Banco Mundial en paralelo (sin caché) | 13,9 s | 8,4 s con hilos |
| GridSearchCV elastic net (20 000 filas, 120 candidatos × 5 pliegues) | 1,18 s | 0,55 s con 7 procesos (la primera vez 2,7 s por el arranque de los procesos) |
| 28 ejemplos curriculares con librerías ya cargadas | 0,82 s | 0,84 s con hilos: son tan pequeños que el GIL de Python anula la ganancia |

Los resultados son idénticos con y sin hilos (`tests/test_parallel.py` compara los 28 ejemplos). Los procesos no quedan en memoria: al salir se detienen, y si Electron muere a la fuerza cada trabajador termina al cerrarse su entrada. En desarrollo, un cambio en `engine/quantlabs` o `packages/contracts` reemplaza los procesos sin reiniciar la app. El puente de Vite usa el mismo grupo, pero lo abre al primer uso para no duplicar procesos con Electron.

## Arquitectura y límites

Electron 45.2.1 instalado y fijado en package-lock.json. Renderer aislado y sandbox, sin Node; preload expone solo RPC y acciones concretas. El proceso principal valida ventana/frame/origen y métodos RPC. Protocolo quantlabs://studio sirve únicamente dist; CSP restringe scripts a recursos locales. Navegación y ventanas externas bloqueadas; el enlace a Releases usa una URL fija.

Cada RPC arranca Python por stdio, limita entrada/salida y tiempo. Los procesos se siguen hasta close; al salir se envía SIGTERM y después SIGKILL si no responden. No se crea un servidor Python residente. El transporte web de desarrollo se mantiene para el navegador. Tauri queda como integración anterior, sin compilar, y no es necesario para esta ruta.

Pendiente: Python redistribuible por plataforma, empaquetador/instaladores, firma/notarización y feed firmado para actualización automática. Las APIs nativas no sustituyen esas etapas. Fuentes: [seguridad Electron](https://www.electronjs.org/docs/latest/tutorial/security), [autoUpdater](https://www.electronjs.org/docs/latest/api/auto-updater).

## Verificación

Pruebas Node del motor real: lista permitida, tamaño máximo, respuesta JSON, liberación del proceso, cancelación y comparación de versiones. Se incorporan al script de sincronización. Compilación TypeScript/Vite y pruebas Python siguen siendo obligatorias. Prueba manual de la ventana macOS: cálculo OLS, recarga, aviso de Releases y salida completa. No se declara verificado Windows ni un instalador firmado.

## Empezar de cero (0.5.1)

Pulsar **Nuevo proyecto**, escribir el nombre y añadir datos simulados, CSV o World Bank. El canvas explica los pasos. El proyecto anterior guardado se conserva en Mis proyectos; los cambios sin guardar requieren confirmar antes de cambiar de flujo. Ejecutar se habilita al añadir el primer nodo.
