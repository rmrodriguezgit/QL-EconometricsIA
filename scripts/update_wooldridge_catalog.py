"""Build metadata only from the installed pinned package; never vendor data rows."""
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import json
import warnings
import pandas as pd
import wooldridge as wd

ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    items=[]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',pd.errors.DtypeWarning)
        for path in sorted((Path(wd.__file__).parent/'datasets').glob('*.csv.bz2')):
            name=path.name.removesuffix('.csv.bz2')
            frame=wd.data(name).copy()
            items.append({'id':name,'rows':len(frame),'columns':[{'name':str(col),'type':str(frame[col].dtype),'numeric':pd.api.types.is_numeric_dtype(frame[col]),'missing':int(frame[col].isna().sum())} for col in frame]})
    data={'catalog_version':1,'package':'wooldridge','package_version':version('wooldridge'),'source_url':'https://github.com/spring-haru/wooldridge','generated_at':datetime.now(timezone.utc).isoformat(),'items':items}
    (ROOT/'packages/contracts/wooldridgeCatalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(items)} conjuntos catalogados; solo nombres, tipos y tamaños, sin observaciones.')
