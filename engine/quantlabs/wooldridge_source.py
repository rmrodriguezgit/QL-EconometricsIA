"""Local textbook data; names are an allowlist, never paths or expressions."""
from importlib.metadata import version
import json
import warnings
import pandas as pd
from .core import EngineError, ROOT

CATALOG=json.loads((ROOT/'packages/contracts/wooldridgeCatalog.json').read_text())
DATASETS={item['id']:item for item in CATALOG['items']}

def load_wooldridge(name: str) -> pd.DataFrame:
    if not isinstance(name,str) or name not in DATASETS:
        raise EngineError('INVALID_DATASET','Selecciona un conjunto del catálogo Wooldridge, por ejemplo wage1 o card.')
    import wooldridge as wd
    from .parallel import capture_warnings
    with capture_warnings():  # descarta DtypeWarning sin tocar el estado global de avisos
        frame=wd.data(name).copy()
    if frame.empty or len(frame)>50000 or len(frame.columns)>100:
        raise EngineError('DATASET_LIMIT','El conjunto supera el límite de 50.000 filas o 100 columnas.')
    return frame

def wooldridge_data(parameters):
    name=parameters.get('dataset','wage1')
    frame=load_wooldridge(name)
    return frame,{'provider':'Wooldridge','dataset':name,'package':'wooldridge','package_version':version('wooldridge'),'source_url':CATALOG['source_url'],'units':'Consultar la documentación del conjunto y sus variables; no inferidas.','note':'Datos clásicos del paquete instalado. Las columnas de tipos mixtos se conservan, sin convertirlas ni imputarlas.'}
