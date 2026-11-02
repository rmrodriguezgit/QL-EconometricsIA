"""Refresh bundled public World Bank country/aggregate metadata, never observations."""
from datetime import datetime, timezone
from pathlib import Path
import json
import requests

ROOT=Path(__file__).resolve().parents[1]
URL='https://api.worldbank.org/v2/es/country'

def download():
    rows=[]
    total=None
    pages=1
    for page in range(1,21):
        response=requests.get(URL,params={'format':'json','per_page':400,'page':page},timeout=(5,20))
        response.raise_for_status()
        metadata,batch=response.json()
        if int(metadata['page'])!=page or not isinstance(batch,list):raise ValueError('Página inválida')
        if total is None:total=int(metadata['total']);pages=int(metadata['pages'])
        if not 1<=pages<=20 or int(metadata['total'])!=total or int(metadata['pages'])!=pages:raise ValueError('Catálogo cambió durante descarga')
        rows.extend(batch)
        if page==pages:break
    if len(rows)!=total:raise ValueError('Catálogo incompleto')
    items=[]
    for row in rows:
        code=row['id']
        if not isinstance(code,str) or len(code)!=3 or not code.isalpha():raise ValueError('Código no compatible')
        items.append({'id':code,'iso2':row['iso2Code'],'name':row['name'],'region':row['region']['value'],'aggregate':row['region']['id']=='NA'})
    if len({item['id'] for item in items})!=len(items):raise ValueError('Códigos repetidos')
    return {'catalog_version':1,'language':'es','source_url':URL,'retrieved_at':datetime.now(timezone.utc).isoformat(),'items':sorted(items,key=lambda row:row['id'])}

if __name__=='__main__':
    data=download()
    path=ROOT/'packages/contracts/worldbankCountries.json'
    temporary=path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)
    print(f"{len(data['items'])} países/economías y agregados guardados; {sum(not row['aggregate'] for row in data['items'])} países/economías.")
