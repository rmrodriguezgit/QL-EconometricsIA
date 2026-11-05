"""Paralelismo del motor: hilos para nodos independientes del grafo y captura de avisos por hilo.

- ``workers()``: hilos por ejecución (``QL_ENGINE_THREADS``; 1 = secuencial).
- ``capture_warnings()``: sustituye a ``warnings.catch_warnings(record=True)``, que modifica estado
  global y mezclaría avisos de nodos que corren a la vez. Cada hilo guarda los suyos.
- ``jobs_for(work)``: procesos para cálculos internos grandes (joblib/loky); 1 si el trabajo es pequeño,
  porque arrancar procesos cuesta más que lo que ahorran con muestras de clase.
"""
from contextlib import contextmanager
import os
import threading
import warnings

_local = threading.local()
_lock = threading.Lock()
_installed = False
_original_show = warnings.showwarning
PROCESS_WORK_THRESHOLD = 2_000_000  # filas × ajustes a partir de las cuales compensa usar procesos


def cpu_count():
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return max(1, os.cpu_count() or 1)


def workers():
    raw = os.environ.get('QL_ENGINE_THREADS', '')
    if raw.strip().isdigit():
        return max(1, min(32, int(raw)))
    return max(1, min(8, cpu_count()))


def jobs_for(work):
    """Procesos para un cálculo interno: solo con trabajo grande y si no se pidió modo secuencial."""
    if work < PROCESS_WORK_THRESHOLD or os.environ.get('QL_ENGINE_PROCESSES', '') == '1':
        return 1
    raw = os.environ.get('QL_ENGINE_PROCESSES', '')
    limit = int(raw) if raw.isdigit() and int(raw) > 0 else max(1, cpu_count() - 1)
    return max(1, min(limit, cpu_count()))


def _show(message, category, filename, lineno, file=None, line=None):
    sink = getattr(_local, 'sink', None)
    if sink is not None:
        sink.append(warnings.WarningMessage(message, category, filename, lineno, file, line))
        return
    _original_show(message, category, filename, lineno, file, line)


def install():
    global _installed
    with _lock:
        if not _installed:
            # Igual que el antiguo simplefilter('always') dentro de catch_warnings: cada aviso se registra.
            warnings.simplefilter('always')
            warnings.showwarning = _show
            _installed = True


@contextmanager
def capture_warnings():
    """Lista de avisos emitidos por este hilo dentro del bloque."""
    install()
    previous, sink = getattr(_local, 'sink', None), []
    _local.sink = sink
    try:
        yield sink
    finally:
        _local.sink = previous
