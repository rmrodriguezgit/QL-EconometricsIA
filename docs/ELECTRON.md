# Escritorio Electron y estudio visual

Versión 0.5.0 · 2026-11-01.

## Arrancar

Desde la raíz del checkout:

```bash
uv sync
npm ci --prefix apps/desktop
npm run desktop --prefix apps/desktop
```

El último comando compila React y abre Electron con los archivos locales, sin Vite, servidor HTTP ni Rust. El motor usa el Python de .venv y los proyectos de este checkout. Se requiere conservar el repositorio y su entorno Python: esta entrega todavía no es un instalador independiente.

Para desarrollar con recarga automática, mantener dos terminales:

```bash
npm run dev --prefix apps/desktop
npm run desktop:dev --prefix apps/desktop
```

## Controles

- Recargar interfaz, también Cmd/Ctrl+R: reinicia React y conserva el grafo en sessionStorage. Los resultados se recalculan al ejecutar. Un proyecto sin guardar pide confirmar el descarte del estado visible; la copia del grafo de la sesión sigue disponible al recargar. Guardar proyecto conserva además el JSON en Mis proyectos.
- Reiniciar aplicación: cierra la instancia y vuelve a arrancar Electron. Guardar primero: la recuperación de sesión cubre recarga, no promete persistencia del borrador tras salir.
- Salir por completo, también Cmd/Ctrl+Q: cierra ventanas, cancela cálculos activos, termina sus procesos Python y sale incluso en macOS. Cerrar la última ventana tiene el mismo efecto; no hay bandeja ni servicio residente.
- Buscar actualizaciones: consulta el último GitHub Release del repositorio propio. Compara versiones numéricas y ofrece una URL fija de Releases. No descarga ni ejecuta instaladores automáticamente. Un 404 se presenta como ausencia de releases, no como aplicación actualizada.

Actualizar el checkout: guardar proyectos, salir, ejecutar git pull --ff-only, uv sync y npm ci --prefix apps/desktop; después arrancar de nuevo. No ejecutar git pull desde el renderer ni reemplazar dependencias mientras se calcula.

## Interfaz

Referencia revisada: [Quantlabs-Blueprints](https://github.com/rmrodriguezgit/Quantlabs-Blueprints), concretamente su renderer/styles.css y main/main.ts, 2026-11-01. Se adopta la organización de estudio oscuro con biblioteca, canvas, inspector y resultados, conservando los contratos, ejemplos y motor de Econometrics. No se cambia el remoto Git.

La recta OLS es amarilla brillante (#ffd166), de 3 px y con leyenda; los puntos permanecen verdes. La cuadrícula se atenúa. Se eliminaron fuentes remotas para que el escritorio funcione sin descargarlas.

## Arquitectura y límites

Electron 45.2.1 instalado y fijado en package-lock.json. Renderer aislado y sandbox, sin Node; preload expone solo RPC y acciones concretas. El proceso principal valida ventana/frame/origen y métodos RPC. Protocolo quantlabs://studio sirve únicamente dist; CSP restringe scripts a recursos locales. Navegación y ventanas externas bloqueadas; el enlace a Releases usa una URL fija.

Cada RPC arranca Python por stdio, limita entrada/salida y tiempo. Los procesos se siguen hasta close; al salir se envía SIGTERM y después SIGKILL si no responden. No se crea un servidor Python residente. El transporte web de desarrollo se mantiene para el navegador. Tauri queda como integración anterior, sin compilar, y no es necesario para esta ruta.

Pendiente: Python redistribuible por plataforma, empaquetador/instaladores, firma/notarización y feed firmado para actualización automática. Las APIs nativas no sustituyen esas etapas. Fuentes: [seguridad Electron](https://www.electronjs.org/docs/latest/tutorial/security), [autoUpdater](https://www.electronjs.org/docs/latest/api/auto-updater).

## Verificación

Pruebas Node del motor real: lista permitida, tamaño máximo, respuesta JSON, liberación del proceso, cancelación y comparación de versiones. Se incorporan al script de sincronización. Compilación TypeScript/Vite y pruebas Python siguen siendo obligatorias. Prueba manual de la ventana macOS: cálculo OLS, recarga, aviso de Releases y salida completa. No se declara verificado Windows ni un instalador firmado.
