"""Tukey box plot: linear quartiles, observed whiskers and explicit outliers."""
import re
import operator
import numpy as np
from .core import EngineError,number

def box_plot(frame,params,with_data=False):
    from .tools import columns
    name=columns(frame,params.get('column','valor'))[0]
    color=params.get('color','#51df83')
    if not isinstance(color,str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',color):raise EngineError('INVALID_PARAMETERS','Selecciona un color hexadecimal, por ejemplo #51df83.')
    values=frame[name].dropna().to_numpy(dtype=float)
    if not len(values):raise EngineError('INSUFFICIENT_SAMPLE','La variable elegida no tiene valores observados.')
    data=frame.copy();audit=None
    condition=params.get('operator','none')
    comparisons={'>':operator.gt,'>=':operator.ge,'<':operator.lt,'<=':operator.le,'==':operator.eq,'!=':operator.ne}
    if condition!='none':
        if condition not in comparisons:raise EngineError('INVALID_PARAMETERS','Operador de comparación no válido.')
        threshold=number(params,'threshold',14.5,-1e100,1e100)
        mean=float(values.mean())  # Exactly the mean of the original observed values, including those to replace.
        mask=(comparisons[condition](frame[name],threshold)&frame[name].notna()).fillna(False)
        data[name]=frame[name].astype(float).where(~mask,mean)
        audit={'operator':condition,'threshold':threshold,'mean':mean,'matched':int(mask.sum()),'observed':len(values)}
        values=data[name].dropna().to_numpy(dtype=float)
    q1,median,q3=np.quantile(values,[.25,.5,.75],method='linear');iqr=q3-q1
    lower,upper=q1-1.5*iqr,q3+1.5*iqr
    inside=values[(values>=lower)&(values<=upper)]
    outliers=np.sort(values[(values<lower)|(values>upper)])
    result={'kind':'boxplot','column':name,'title':str(params.get('title','Distribución de los valores'))[:150],'y_label':str(params.get('y_label','Valores'))[:100],'color':color,'n':len(values),'missing':int(frame[name].isna().sum()),'q1':float(q1),'median':float(median),'q3':float(q3),'iqr':float(iqr),'lower_fence':float(lower),'upper_fence':float(upper),'whisker_low':float(min(q1,inside.min())),'whisker_high':float(max(q3,inside.max())),'minimum':float(values.min()),'maximum':float(values.max()),'outliers':outliers.tolist(),'note':'Caja: Q1–Q3; línea central: mediana. Bigotes: valores observados extremos dentro de Q1−1,5×RIC y Q3+1,5×RIC; si no hay observaciones más allá de un cuartil, terminan en ese cuartil. Los puntos exteriores son atípicos según esta regla, no errores que deban borrarse. Se excluyen y cuentan los faltantes; no se rellenan automáticamente.'}

    if audit:
        result['replacement']=audit
        result['note']+=' Reemplazo condicional explícito con la media original; puede alterar la distribución y la inferencia. La fuente permanece intacta.'
    return (result,data) if with_data else result
