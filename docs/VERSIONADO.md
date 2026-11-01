# Versionado y sincronización automática

Destino autorizado: `https://github.com/rmrodriguezgit/Quantlabs-Econometrics.git`, rama inicial `main`.

## Inicialización

El repositorio ya estaba inicializado y sin commits. Se conserva su contenido local. El primer commit agrupa documentación, inventario y automatización. Se establece `main`, remoto `origin` y seguimiento mediante `git push -u origin main`.

La identidad de autor, si no existe configuración previa, se configura solo en este repositorio como `rmrodriguezgit <rmrodriguezgit@users.noreply.github.com>`. Es un alias de privacidad elegido para el commit, no un correo personal verificado ni una firma criptográfica. Nunca se cambia configuración Git global.

## Cierre automático de cada unidad

```sh
python3 scripts/sync.py --message "docs: actualizar cobertura"
```

El script verifica la rama y el remoto, rechaza cambios ajenos ya staged, ejecuta el comprobador documental y pruebas de automatización, agrega solo archivos permitidos, crea commit si procede y siempre intenta push. El código distinto de cero indica fallo. No crea commits vacíos; si el push anterior falló, se puede repetir sin duplicar commits. Exige identidad Git configurada y autenticación disponible.

Rutas iniciales permitidas: README.md, AGENTS.md, CHANGELOG.md, VERSION, .gitignore, docs/, scripts/, tests/ y .github/. Al incorporar código se amplía explícitamente la lista en sync.py. Los PDF, ZIP y datos privados siguen excluidos incluso dentro de estas rutas. El script es invocable; AGENTS.md indica a los agentes ejecutarlo al terminar. No se ha instalado un monitor, hook ni scheduler.

## Conflictos y recuperación

- Sin red o credenciales: conservar commit local, resolver conexión/autenticación y repetir el script.
- Push rechazado por avances remotos: inspeccionar `git fetch origin` y diferencias; integrar con revisión y volver a validar. El script no hace merge/rebase automático.
- Documentación o pruebas inválidas: no crear commit; corregir y repetir.
- Cambios staged fuera de las rutas permitidas: revisar manualmente antes de sincronizar; no se deshace staging del usuario.
- No usar force push ni guardar tokens en archivos. Las credenciales del entorno gestionan el acceso.

## Automatización en GitHub

`.github/workflows/docs.yml` ejecuta validación documental y pruebas en macOS/Windows con Python 3.12 ante push y pull request. No modifica archivos ni crea commits recursivos. Su ejecución remota debe comprobarse después del push; una prueba local no prueba que CI haya terminado.
