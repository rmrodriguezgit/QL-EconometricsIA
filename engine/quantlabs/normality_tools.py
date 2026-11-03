"""Explicit alignment, classroom mean imputation and descriptive normality diagnostics."""
import re
import numpy as np
import pandas as pd
from scipy import stats
from .core import EngineError,number

def run_normality_tool(kind,inputs,params):
    from .tools import columns,frame_result,report,table
    if kind=='join_series':
        left,right=inputs['left'],inputs['right'];parts=[]
        for side,frame in [('left',left),('right',right)]:
            key=params.get(side+'_key','periodo');value=params.get(side+'_value','valor');alias=params.get(side+'_name',side)
            if key==value or key not in frame or value not in frame:raise EngineError('INVALID_PARAMETERS',f'Selecciona tiempo y valor existentes y distintos en la tabla {side}.')
            if not isinstance(alias,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,49}',alias) or alias=='periodo':raise EngineError('INVALID_PARAMETERS','Los nombres de salida deben ser distintos de periodo y usar letras, números o guion bajo.')
            if frame[key].isna().any() or frame[key].duplicated().any():raise EngineError('INVALID_PARAMETERS','Las claves deben ser únicas y no vacías en cada tabla; separa países antes de unir.')
            if not pd.api.types.is_numeric_dtype(frame[value]):raise EngineError('INVALID_PARAMETERS','Los valores de ambas series deben ser numéricos.')
            part=frame[[key,value]].copy();part.columns=['periodo',alias];parts.append(part)
        if params.get('left_name','left')==params.get('right_name','right'):raise EngineError('INVALID_PARAMETERS','Los nombres de las dos variables deben ser distintos.')
        # Explicit outer alignment; no row-position joins and no silent aggregation.
        if pd.api.types.is_numeric_dtype(parts[0].periodo)!=pd.api.types.is_numeric_dtype(parts[1].periodo):raise EngineError('INVALID_PARAMETERS','Las claves temporales deben tener el mismo tipo en ambas tablas.')
        data=parts[0].merge(parts[1],on='periodo',how='outer',validate='one_to_one',sort=True)
        result=frame_result(data,'Unión exterior por período: conserva todos los años y los faltantes. Sin imputación ni agregación.');result['alignment']={'left_rows':len(left),'right_rows':len(right),'rows':len(data),'how':'outer','key':'periodo'}
        return result,{'data':data}
    if kind=='impute_mean':
        frame=inputs['data'];names=columns(frame,params.get('columns','lending_rate,final_consumption'));data=frame.copy();audit=[]
        for name in names:
            observed=frame[name].dropna()
            if observed.empty:raise EngineError('INSUFFICIENT_SAMPLE',f'{name} no tiene datos observados; no se puede estimar una media.')
            mean=float(observed.mean());missing=int(frame[name].isna().sum())
            data[name]=frame[name].astype(float).fillna(mean);audit.append({'column':name,'mean':mean,'observed':len(observed),'filled':missing})
        data.attrs['quantlabs_imputation']=audit
        result=frame_result(data,'Imputación explícita con la media de la tabla conectada. Reduce la dispersión y puede distorsionar correlaciones, pruebas de normalidad e inferencia. No equivale a recuperar datos reales. Para validación predictiva, aprende la media solo con entrenamiento; este nodo didáctico usa toda su entrada.')
        result['imputation']=audit
        return result,{'data':data}
    residual=kind=='residual_normality'
    if residual:
        model=inputs['model']
        if model.kind not in ['ols','multiple_ols','robust','covariance'] or not hasattr(model.fit,'resid'):raise EngineError('INVALID_PARAMETERS','Conecta un modelo lineal OLS simple o múltiple.')
        frame=pd.DataFrame({'residuos':np.asarray(model.fit.resid,dtype=float)});names=['residuos']
    else:
        frame=inputs['data'];names=columns(frame,params.get('columns','lending_rate,final_consumption'))
    alpha=number(params,'alpha',.05,.001,.2)
    result=report('H₀: distribución normal. p < α aporta evidencia contra H₀; no rechazar no demuestra normalidad. OLS no exige variables normales; la normalidad de errores interviene en inferencia exacta bajo los demás supuestos clásicos. Los residuos son aproximaciones a errores no observados.')
    result['normality']=[];summary=[];tests=[]
    for name in names:
        raw=frame[name];values=raw.dropna().to_numpy(dtype=float);n=len(values)
        if n<3:raise EngineError('INSUFFICIENT_SAMPLE',f'{name}: se necesitan al menos tres observaciones.')
        if not np.isfinite(values).all():raise EngineError('INVALID_PARAMETERS','No se admiten valores infinitos.')
        std=float(np.std(values,ddof=1));constant=std==0
        summary.append([name,n,int(raw.isna().sum()),float(np.mean(values)),float(np.median(values)),std,float(np.var(values,ddof=1))])
        # Shapiro p-values above 5000 observations are not reliable: no silent subsampling.
        if constant:
            result['warnings'].append(f'{name}: columna constante; pruebas de normalidad no definidas.')
        elif n<=5000:
            stat,p=stats.shapiro(values);tests.append([name,'Shapiro–Wilk',n,float(stat),float(p),alpha,'Rechazar H₀' if p<alpha else 'No rechazar H₀'])
        else:result['warnings'].append(f'{name}: Shapiro–Wilk omitido porque n > 5000.')
        if not constant:
            stat,p=stats.jarque_bera(values);tests.append([name,'Jarque–Bera (asintótico)',n,float(stat),float(p),alpha,'Rechazar H₀' if p<alpha else 'No rechazar H₀'])
        if n<2000:result['warnings'].append(f'{name}: Jarque–Bera usa una aproximación asintótica; interpretar con cautela en muestras pequeñas.')
        counts,bounds=np.histogram(values,bins=min(50,max(5,int(np.sqrt(n)))))
        theoretical,ordered=stats.probplot(values,dist='norm',fit=False);indices=np.unique(np.linspace(0,n-1,min(n,400)).astype(int))
        result['normality'].append({'column':name,'histogram':{'column':name,'n':n,'missing':int(raw.isna().sum()),'bins':[{'lower':float(bounds[i]),'upper':float(bounds[i+1]),'count':int(counts[i])} for i in range(len(counts))]},'qq':{'points':[[float(theoretical[i]),float(ordered[i])] for i in indices],'mean':float(np.mean(values)),'std':std,'n':n,'shown':len(indices)}})
    result['tables']=[table('Estadísticos descriptivos',['Variable','n observado','Faltantes','Media','Mediana','Desv. muestral (n−1)','Varianza muestral (n−1)'],summary),table('Pruebas de normalidad',['Variable','Prueba','n','Estadístico','p-valor','α','Decisión'],tests)]
    result['limitations']=['Media = Σxᵢ/n. La media no se divide entre grados de libertad. Varianza muestral = Σ(xᵢ−media)²/(n−1); desviación = raíz de la varianza.','Las pruebas suponen observaciones independientes; las series temporales pueden tener tendencia y autocorrelación. Normalidad no demuestra estacionariedad ni causalidad.','La imputación con media puede alterar estas pruebas. Compare datos observados y datos imputados; no fuerce normalidad para habilitar OLS.','No se corrige por comparaciones múltiples entre columnas o pruebas.']
    result['n']=len(frame)
    return result,{'result':result}
