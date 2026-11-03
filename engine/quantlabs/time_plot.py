"""Chronological line plots without mixing repeated periods or filling missing values."""
import re
import numpy as np
import pandas as pd
from .core import EngineError

def time_plot(frame, params):
    time=params.get('time','periodo');value=params.get('value','valor');mode=params.get('time_mode','year')
    if time==value or time not in frame or value not in frame:
        raise EngineError('INVALID_PARAMETERS','Selecciona columnas distintas de tiempo y valor de la tabla conectada.')
    if mode not in ['year','date']:
        raise EngineError('INVALID_PARAMETERS','Formato temporal: year (años) o date (fechas ISO AAAA-MM-DD).')
    if not pd.api.types.is_numeric_dtype(frame[value]):
        raise EngineError('INVALID_PARAMETERS','La variable del eje vertical debe ser numérica.')
    if np.isinf(frame[value].to_numpy(dtype=float)).any():
        raise EngineError('INVALID_PARAMETERS','No se admiten valores infinitos.')
    work=frame[[time,value]].copy();missing_time=int(work[time].isna().sum());work=work.dropna(subset=[time])
    if mode=='year':
        parsed=pd.to_numeric(work[time],errors='coerce')
        if parsed.isna().any() or not np.isfinite(parsed).all() or (parsed%1!=0).any():
            raise EngineError('INVALID_PARAMETERS','El tiempo debe contener años enteros; para fechas elige date.')
        work['_x']=parsed.astype(float);work['_label']=parsed.astype(int).astype(str)
    else:
        text=work[time].astype(str)
        if not text.map(lambda item:bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',item))).all():
            raise EngineError('INVALID_PARAMETERS','Usa fechas ISO AAAA-MM-DD sin horas.')
        dates=pd.to_datetime(text,format='%Y-%m-%d',errors='coerce')
        if dates.isna().any():raise EngineError('INVALID_PARAMETERS','Hay fechas inválidas en la columna temporal.')
        work['_x']=dates.map(lambda date:float(date.toordinal()));work['_label']=text
    if work['_x'].duplicated().any():
        raise EngineError('INVALID_PARAMETERS','Hay períodos repetidos. Filtra un país o una serie antes de dibujar; no se agregan observaciones automáticamente.')
    work=work.sort_values('_x',kind='stable')
    if work[value].notna().sum()<2:raise EngineError('INSUFFICIENT_SAMPLE','Se necesitan al menos dos valores observados con tiempo válido.')
    points=[];previous=None;gaps=0
    for _,row in work.iterrows():
        x=float(row['_x'])
        if mode=='year' and previous is not None and x-previous>1:
            points.append({'x':previous+1,'y':None,'label':'Períodos ausentes'});gaps+=1
        points.append({'x':x,'y':None if pd.isna(row[value]) else float(row[value]),'label':row['_label']});previous=x
    return {'kind':'time_plot','n':int(work[value].notna().sum()),'missing':int(work[value].isna().sum()),'missing_time':missing_time,'gaps':gaps,'time':time,'value':value,'time_mode':mode,'title':str(params.get('title','Serie temporal'))[:150],'x_label':str(params.get('x_label','Fecha'))[:100],'y_label':str(params.get('y_label','Valor'))[:100],'points':points,'note':'Valores ordenados por tiempo; sin agregación ni imputación. Los faltantes interrumpen la línea. En modo date se unen las fechas observadas; no se presupone frecuencia diaria.'}
