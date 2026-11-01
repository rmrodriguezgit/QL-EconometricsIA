"""Local project workspace: versioned writes and recoverable deletion, no arbitrary paths."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import uuid

from .core import EngineError, ROOT, canonical, digest, validate_project

MAX_BYTES = 3_000_000


def workspace():
    return Path(os.environ.get('QUANTLABS_WORKSPACE', str(ROOT / '.quantlabs/projects')))


def identifier(value):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise EngineError('INVALID_FILE_ID', 'Identificador de proyecto no válido.')
    return value


def folder(trash=False):
    path = workspace() / ('trash' if trash else 'files')
    if path.is_symlink():
        raise EngineError('INVALID_FILE', 'La carpeta de proyectos no puede ser un enlace simbólico.')
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_path(value, trash=False):
    path = folder(trash) / f'{identifier(value)}.json'
    if path.is_symlink():
        raise EngineError('INVALID_FILE', 'No se permiten enlaces simbólicos en el espacio de proyectos.')
    return path


def read(value, trash=False):
    path = file_path(value, trash)
    try:
        if path.stat().st_size > MAX_BYTES:
            raise ValueError('File too large')
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('id') != value or not isinstance(data.get('project'), dict):
            raise ValueError('Invalid file')
        if any(not isinstance(data.get(key), str) for key in ['title', 'revision', 'created_at', 'updated_at']):
            raise ValueError('Missing metadata')
        datetime.fromisoformat(data['created_at']); datetime.fromisoformat(data['updated_at'])
        validate_project(data['project'], require_connected=False)
        if data['revision'] != digest(data['project']):
            raise ValueError('Revision mismatch')
        return data
    except FileNotFoundError as exc:
        raise EngineError('FILE_NOT_FOUND', 'El proyecto no existe en esta carpeta.') from exc
    except (KeyError, ValueError, OSError) as exc:
        raise EngineError('INVALID_FILE', 'El archivo está dañado o no contiene un proyecto compatible.') from exc


def listing(trash=False):
    items, errors = [], []
    for path in folder(trash).glob('*.json'):
        try:
            data = read(path.stem, trash)
            items.append({key: data[key] for key in ['id', 'title', 'revision', 'created_at', 'updated_at']})
        except EngineError:
            errors.append(path.name)
    return {'items': sorted(items, key=lambda item: item['updated_at'], reverse=True),
            'unreadable': errors, 'trash': trash}


def save(project, value=None, expected_revision=None):
    validate_project(project, require_connected=False)
    value = identifier(value) if value is not None else str(uuid.uuid4())
    path = file_path(value)
    now = datetime.now(timezone.utc).isoformat()
    created = now
    if path.exists():
        previous = read(value)
        if expected_revision != previous['revision']:
            raise EngineError('FILE_CONFLICT', 'El proyecto cambió desde que lo abriste. Abre la versión actual o guarda una copia.')
        created = previous['created_at']
    elif expected_revision is not None:
        raise EngineError('FILE_NOT_FOUND', 'El archivo original ya no existe. Guarda una copia nueva.')
    data = {'id': value, 'title': project['title'] or 'Sin título', 'created_at': created,
            'updated_at': now, 'revision': digest(project), 'project': project}
    encoded = canonical(data)
    if len(encoded.encode('utf-8')) > MAX_BYTES:
        raise EngineError('FILE_TOO_LARGE', 'El proyecto supera el límite de 3 MB.')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        if temporary:
            temporary.unlink(missing_ok=True)
        raise EngineError('FILE_WRITE_FAILED', 'No se pudo guardar el proyecto. El archivo anterior se conserva.') from exc
    return data


def move(value, expected_revision, restore=False):
    data = read(value, trash=restore)
    if data['revision'] != expected_revision:
        raise EngineError('FILE_CONFLICT', 'El archivo cambió. Actualiza la lista antes de moverlo.')
    target = file_path(value, trash=not restore)
    if target.exists():
        raise EngineError('FILE_CONFLICT', 'Ya existe un archivo con ese identificador en el destino.')
    os.replace(file_path(value, trash=restore), target)
    return data


def example_catalog():
    data = json.loads((ROOT / 'examples/catalog.json').read_text(encoding='utf-8'))
    return data['examples']


def example_get(value):
    for example in example_catalog():
        if example['id'] == value:
            project = json.loads((ROOT / 'examples/projects' / f'{value}.json').read_text(encoding='utf-8'))
            validate_project(project)
            return {'example': example, 'project': project}
    raise EngineError('EXAMPLE_NOT_FOUND', 'No existe ese ejemplo en el catálogo.')


@contextmanager
def mutation_lock():
    path = workspace()
    path.mkdir(parents=True, exist_ok=True)
    with (path / '.write.lock').open('a+b') as lock:
        try:
            if os.name == 'nt':
                import msvcrt
                if os.fstat(lock.fileno()).st_size == 0:
                    lock.write(b'0'); lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            raise EngineError('FILE_BUSY', 'Otra operación está guardando archivos. Reintenta.') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def dispatch_files(method, params):
    if method == 'examples.list':
        return {'items': example_catalog()}
    if method == 'examples.read':
        return example_get(params.get('id'))
    if method == 'projects.list':
        trash = params.get('trash', False)
        if not isinstance(trash, bool):
            raise EngineError('INVALID_PARAMETERS', 'La carpeta solicitada no es válida.')
        return listing(trash)
    if method == 'projects.read':
        return read(params.get('id'))
    if method == 'projects.save':
        with mutation_lock():
            return save(params.get('project'), params.get('id'), params.get('expected_revision'))
    if method == 'projects.delete':
        with mutation_lock():
            return move(params.get('id'), params.get('expected_revision'))
    if method == 'projects.restore':
        with mutation_lock():
            return move(params.get('id'), params.get('expected_revision'), restore=True)
    raise EngineError('INVALID_METHOD', 'Operación de archivo desconocida.')
