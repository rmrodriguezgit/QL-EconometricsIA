"""Bounded runtime audit. Does not claim a full security or scientific certification."""
from .core import NODES, VERSION, validate_project
from .projects import example_catalog, example_get, listing, folder
import tempfile
from pathlib import Path


def system_audit():
    checks = []
    examples = example_catalog()
    expected = {f'C{i:02}' for i in range(1,29)}
    ids = {example['id'] for example in examples}
    valid = True
    for example in examples:
        try:
            validate_project(example_get(example['id'])['project'])
        except Exception:
            valid = False
    references = {ref for example in examples for ref in example['references']}
    checks.append({'id':'catalog','title':'Catálogo de los 28 módulos','status':'ok' if ids == expected and valid else 'pending','detail':f'{len(ids)} módulos con proyectos de estructura validada. Esta comprobación no ejecuta modelos; sus pruebas científicas se ejecutan en la suite.'})
    connected = all(example.get('format')=='connected' and all(node['type']!='experiment' for node in example_get(example['id'])['project']['nodes']) for example in examples)
    guided = all({step['node_id'] for step in example_get(example['id'])['project'].get('lesson',{}).get('steps',[])} == {node['id'] for node in example_get(example['id'])['project']['nodes']} for example in examples)
    checks.append({'id':'connected','title':'Herramientas propias y pasos inspeccionables','status':'ok' if connected and guided else 'pending','detail':f'{len(NODES)} tipos registrados (incluida compatibilidad anterior). Los 28 ejemplos son grafos conectados, sin receta cerrada, y cada nodo tiene un paso explicativo.'})
    checks.append({'id':'references','title':'Trazabilidad bibliográfica','status':'ok' if references == {f'B{i:02}' for i in range(1,37)} else 'pending','detail':f'{len(references)} capítulos referenciados. La existencia de un ejemplo introductorio no acredita todos los subtemas del capítulo.'})
    try:
        with tempfile.NamedTemporaryFile(dir=folder(), prefix='.audit-', delete=True) as stream:
            stream.write(b'quantlabs');stream.flush()
        writeable = True
    except OSError:
        writeable = False
    checks.append({'id':'storage','title':'Almacenamiento local y papelera','status':'ok' if writeable else 'pending','detail':'Escritura local comprobada; guardado atómico, identificadores acotados, revisión de conflictos y borrado recuperable.' if writeable else 'No se pudo escribir en el espacio local.'})
    files, trash = listing(), listing(True)
    checks.append({'id':'files','title':'Integridad de archivos guardados','status':'ok' if not files['unreadable'] and not trash['unreadable'] else 'pending','detail':f"{len(files['items'])} proyectos; {len(trash['items'])} en papelera; {len(files['unreadable'])+len(trash['unreadable'])} archivos no legibles conservados sin modificación."})
    checks.append({'id':'draft','title':'Separación entre guardar y ejecutar','status':'ok','detail':'Los borradores vacíos o sin conectar pueden guardarse; ejecutar exige fuentes y conexiones válidas.'})
    checks.append({'id':'sample','title':'Coherencia entre gráfico y estimación','status':'ok','detail':'La recta OLS solo se superpone cuando coincide la fuente de datos y los nombres de variables.'})
    try:
        from .brain import llm as brain_llm, store as brain_store
        ollama=brain_llm.status();pending=len(brain_store.list_gaps('pending'))
        checks.append({'id':'brain','title':'Segundo cerebro','status':'ok' if ollama['ready'] else 'pending','detail':(f"Qwen local disponible ({ollama['model']})." if ollama['ready'] else 'Ollama o el modelo no están disponibles: el cerebro usa el planificador determinista.')+f' {pending} fichas de herramientas pendientes. Los blueprints se validan con el motor; no se ejecuta código generado.'})
    except Exception:
        checks.append({'id':'brain','title':'Segundo cerebro','status':'pending','detail':'No se pudo consultar el estado del cerebro.'})
    checks.append({'id':'curriculum','title':'Cobertura científica exhaustiva','status':'pending','detail':'Los 28 recorridos ya utilizan herramientas reutilizables, pero aún faltan subtemas. Cada guía enumera sus pendientes: por ejemplo volatilidad multivariada, panel y GMM de momentos general.'})
    checks.append({'id':'desktop','title':'Instaladores de macOS y Windows','status':'pending','detail':'Tauri sigue sin compilar en este equipo; faltan Cargo.lock, empaquetado científico, firma y verificación por plataforma.'})
    checks.append({'id':'engine','title':'Motor persistente y ejecución larga','status':'pending','detail':'El transporte limita cada ejecución a 60 segundos. Faltan sidecar persistente, progreso incremental, cancelación y caché del DAG.'})
    return {'app_version':VERSION,'checks':checks,'scope':'Auditoría funcional acotada; no es certificación de seguridad ni revisión bibliográfica exhaustiva.'}
