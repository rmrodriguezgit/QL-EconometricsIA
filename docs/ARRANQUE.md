# Arranque de escritorio · 0.7.3

## Uso

1. Instala Node.js 22 o posterior con npm y uv, accesibles en PATH.
2. Clona o extrae el repositorio completo en una carpeta escribible.
3. Abre `Arrancar-Quantlabs.command` en macOS o `Arrancar-Quantlabs.cmd` en Windows con doble clic.
4. Espera el progreso de preparación, construcción y apertura de Electron. Guarda el proyecto antes de salir.

No hace falta activar `.venv` ni ejecutar comandos de desarrollo en cada sesión. La primera preparación necesita red para Python 3.12 y los paquetes. El arrancador no instala Node o uv ni cambia ajustes del sistema. No descarga automáticamente nuevas versiones del repositorio. Si falla, muestra el comando afectado y deja la terminal abierta para leerlo; vuelve a intentarlo después de resolver la causa.

En macOS se añaden a PATH las ubicaciones habituales de Homebrew y uv. Las instalaciones de Node gestionadas únicamente por una shell interactiva deben quedar accesibles en PATH. Si un ZIP pierde permisos: `chmod +x Arrancar-Quantlabs.command` desde la raíz. En Windows se usa `cmd.exe` para npm y `.venv/Scripts/python.exe` para el motor; las rutas con espacios se mantienen como argumentos separados.

## Diseño e implementación

Los dos accesos ejecutan `scripts/launch.cjs`, que trabaja desde la raíz del repositorio aunque se abra desde otra carpeta. Sincroniza Python con el lock y construye la interfaz antes de abrir Electron. Usa una huella de package.json, package-lock, plataforma, arquitectura y versión mayor de Node para reutilizar npm. Si faltan las herramientas o cambia la huella, vuelve a ejecutar npm ci. La marca de instalación solo se guarda después del éxito en `.cache/launcher/`, excluida de Git.

Cerrar Electron devuelve el control al arrancador. Los errores de preparación o ejecución devuelven un código distinto de cero. El cierre de procesos Python corresponde al runtime de Electron existente.

## Verificación y límites

- Verificados en macOS: requisitos con `node scripts/launch.cjs --check`, sintaxis Bash, pruebas de la huella de instalación y construcción del frontend.
- El enrutamiento de comandos Windows se comprueba con pruebas unitarias; no equivale a una ejecución real en Windows. Doble clic y ciclo completo en Windows pendientes de verificar en ese sistema.
- El ciclo completo del nuevo arrancador mediante Finder tampoco se presenta como verificado por las pruebas unitarias.
- No son paquetes `.app`, `.dmg` ni instaladores `.exe`; siguen requiriendo el repositorio y las herramientas iniciales. Firma, distribución y actualización automática permanecen pendientes.

Esta unidad mejora el acceso al laboratorio. No cambia la cobertura curricular ni completa los temas pendientes en [COBERTURA.md](COBERTURA.md).
