"""Keep wbdata's shelve cache private to one engine process.

The shared JSON indicator catalog remains separate. Existing cache files are
never deleted: a broken or concurrently written shelf must not block imports.
"""
import atexit
from functools import lru_cache
import os
from pathlib import Path
import tempfile


@lru_cache(maxsize=1)
def client():
    temporary = tempfile.TemporaryDirectory(prefix='quantlabs-wbdata-')
    atexit.register(temporary.cleanup)
    cache = str(Path(temporary.name) / 'cache')
    previous = os.environ.get('WBDATA_CACHE_PATH')
    os.environ['WBDATA_CACHE_PATH'] = cache
    try:
        # wbdata also creates a default Client during import; isolate that too.
        import wbdata
        return wbdata.Client(cache_path=cache)
    finally:
        if previous is None:
            os.environ.pop('WBDATA_CACHE_PATH', None)
        else:
            os.environ['WBDATA_CACHE_PATH'] = previous
