"""Reusable visual tools. Every calculation consumes the artifacts wired into its ports."""
from dataclasses import dataclass, replace
import os
import json
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from .core import EngineError, number, finite_json, digest, NODE_CATALOG

@dataclass
class Fitted:
    kind: str
    fit: object
    frame: pd.DataFrame
    features: list
    target: str | None = None
    label: str = ''

@dataclass
class Scaler:
    fit: object
    columns: list


def columns(frame, value):
    if not isinstance(value,str): raise EngineError('INVALID_PARAMETERS','Escribe columnas separadas por coma.')
    names=[name.strip() for name in value.split(',') if name.strip()]
    if not names:
        raise EngineError('INVALID_PARAMETERS','Selecciona al menos una variable en las casillas del inspector.')
    missing=[name for name in names if name not in frame]
    repeated=sorted({name for name in names if names.count(name)>1})
    if missing or repeated:
        detail=(' No existen: '+', '.join(missing)+'.' if missing else '')+(' Repetidas: '+', '.join(repeated)+'.' if repeated else '')
        raise EngineError('INVALID_PARAMETERS',detail.strip()+' Selecciona las variables de la tabla conectada en el inspector.')
    if any(not pd.api.types.is_numeric_dtype(frame[name]) for name in names):
        raise EngineError('INVALID_PARAMETERS','Las columnas elegidas deben ser numéricas.')
    if np.isinf(frame[names].to_numpy(dtype=float)).any(): raise EngineError('INVALID_PARAMETERS','No se admiten valores infinitos.')
    return names


def sample(frame,names,minimum=4):
    values=frame[names].dropna().copy()
    if len(values)<minimum: raise EngineError('INSUFFICIENT_SAMPLE',f'Se necesitan al menos {minimum} observaciones completas.')
    return values


def report(text='',**metrics):
    return {'kind':'analysis','interpretation':text,'metrics':[{'label':key,'value':value} for key,value in metrics.items()], 'tables':[], 'series':[], 'limitations':[], 'warnings':[]}


def table(title,names,rows): return {'title':title,'columns':names,'rows':rows}


def series(label,values): return {'label':label,'points':[[i,float(value)] for i,value in enumerate(np.asarray(values).ravel()[:200])]}


def regression_report(model,text='Coeficientes de la muestra conectada; una asociación no demuestra causalidad.'):
    fit=model.fit
    params=np.asarray(fit.params);errors=np.asarray(fit.bse);pvalues=np.asarray(fit.pvalues)
    names=list(getattr(fit.model,'exog_names',['const',*model.features]))
    result=report(text,n_ajuste=len(model.frame))
    result['tables']=[table('Estimación e inferencia',['Término','Coeficiente','Error estándar','p-valor'],[[name,params[i],errors[i],pvalues[i]] for i,name in enumerate(names)])]
    return result


def frame_result(frame,note):
    records=json.loads(frame.to_json(orient='records',double_precision=15))
    return {'kind':'dataset','columns':frame.columns.tolist(),'numeric_columns':frame.select_dtypes(include='number').columns.tolist(),'n':len(frame),'preview':records[:8],'records':records if len(records)<=10000 else records[:1000],'records_complete':len(records)<=10000,'column_types':{str(col):str(frame[col].dtype) for col in frame},'note':note+(' La tabla tiene más de 10.000 filas: el JSON incluye solo las primeras 1.000; el cálculo y la huella usan todas.' if len(records)>10000 else ''),'data_sha256':digest(records)}


def synthetic(params):
    n=number(params,'n',300,20,10000,True);seed=number(params,'seed',42,0,2**32-1,True)
    scenario=params.get('scenario','regression');rng=np.random.default_rng(seed)
    x=rng.normal(size=n);error=rng.normal(size=n)
    if scenario=='regression': frame=pd.DataFrame({'ingreso':x,'consumo':2+.8*x+error})
    elif scenario=='multiple':
        z=.9*x+rng.normal(0,.2,n);frame=pd.DataFrame({'x':x,'z':z,'y':1+.7*x+.3*z+error})
    elif scenario=='hetero': frame=pd.DataFrame({'x':x,'y':1+x+error*(.2+2*np.abs(x))})
    elif scenario=='outliers':
        y=2+.8*x+error;y[:max(1,n//30)]+=25;frame=pd.DataFrame({'x':x,'y':y})
    elif scenario=='logistic': frame=pd.DataFrame({'x':x,'clase':rng.binomial(1,stats.logistic.cdf(-.4+1.2*x))})
    elif scenario=='prices':
        frame=pd.DataFrame({'periodo':np.arange(n),'nominal':100*np.cumprod(1+rng.normal(.006,.001,n)),'indice':100*np.cumprod(1+rng.normal(.003,.0005,n)),'poblacion':np.linspace(10,12,n)})
    elif scenario=='positive': frame=pd.DataFrame({'periodo':np.arange(n),'valor':100*np.cumprod(1+rng.normal(.003,.01,n))})
    elif scenario=='exponential': frame=pd.DataFrame({'valor':rng.exponential(size=n)})
    elif scenario=='income': frame=pd.DataFrame({'valor':rng.lognormal(3,.7,n)})
    elif scenario=='normal': frame=pd.DataFrame({'valor':rng.normal(10,3,n)})
    elif scenario=='pairs':
        before=rng.normal(50,8,n);frame=pd.DataFrame({'antes':before,'despues':before+rng.normal(.5,2,n)})
    elif scenario=='cobb':
        capital,labor=rng.lognormal(2,.5,(2,n));frame=pd.DataFrame({'capital':capital,'trabajo':labor,'produccion':1.5*capital**.35*labor**.6*np.exp(rng.normal(0,.1,n))})
    elif scenario=='ar1':
        ar=np.zeros(n)
        for t in range(1,n): ar[t]=.75*ar[t-1]+rng.normal()
        frame=pd.DataFrame({'periodo':np.arange(n),'y':ar,'walk':np.cumsum(rng.normal(size=n))})
    elif scenario=='cointegrated':
        trend=np.cumsum(rng.normal(size=n));frame=pd.DataFrame({'periodo':np.arange(n),'x':trend,'y':1.5*trend+rng.normal(0,.4,n)})
    elif scenario=='garch':
        errors=np.zeros(n);variance=np.ones(n)
        for t in range(1,n):
            variance[t]=.1+.12*errors[t-1]**2+.8*variance[t-1];errors[t]=np.sqrt(variance[t])*rng.normal()
        frame=pd.DataFrame({'periodo':np.arange(n),'retorno':errors})
    elif scenario=='factors':
        latent=rng.normal(size=(n,2));values=latent@np.array([[1,.9,.8,0,0,0],[0,0,0,1,.9,.8]])+rng.normal(0,.3,(n,6));frame=pd.DataFrame(values,columns=[f'x{i}' for i in range(1,7)])
    elif scenario=='endogenous':
        z=rng.normal(size=n);u=rng.normal(size=n);endogenous=.9*z+.7*u+rng.normal(0,.3,n);frame=pd.DataFrame({'z':z,'x':endogenous,'y':1+2*endogenous+u})
    elif scenario=='polynomial':
        x=rng.uniform(-2,2,n);frame=pd.DataFrame({'x':x,'y':1+x+.4*x*x+rng.normal(0,.8,n)})
    elif scenario=='returns': frame=pd.DataFrame({'periodo':np.arange(n),'retorno':rng.normal(.0003,.012,n)})
    elif scenario=='regimes':
        states=np.zeros(n,dtype=int)
        for t in range(1,n): states[t]=states[t-1] if rng.random()<.96 else 1-states[t-1]
        frame=pd.DataFrame({'periodo':np.arange(n),'valor':rng.normal(np.where(states==0,-2,2),.6),'estado_real':states})
    elif scenario=='clusters':
        labels=np.arange(n)%3;values=rng.normal(size=(n,2))*.3+np.array([[-2,-1],[0,2],[2,-1]])[labels];frame=pd.DataFrame(values,columns=['x1','x2'])
    elif scenario=='nonlinear':
        x=rng.uniform(-3,3,n);frame=pd.DataFrame({'x':x,'y':np.sin(x)+rng.normal(0,.1,n)})
    elif scenario=='inflation': frame=pd.DataFrame(rng.normal(.03,.015,(n,5)),columns=[f'r{i}' for i in range(1,6)])
    elif scenario=='sem':
        factor=rng.normal(size=n);frame=pd.DataFrame({'x1':factor+rng.normal(0,.3,n),'x2':.8*factor+rng.normal(0,.3,n),'x3':1.2*factor+rng.normal(0,.3,n),'y':.7*factor+rng.normal(0,.5,n)})
    else: raise EngineError('INVALID_PARAMETERS','Escenario desconocido. Consulta la lista de escenarios del generador.')
    return frame


def time_order(frame):
    if 'periodo' in frame:
        if frame['periodo'].duplicated().any() or not frame['periodo'].is_monotonic_increasing:
            raise EngineError('INVALID_PARAMETERS','Se requieren períodos únicos y ordenados. Separa los países de un panel y revisa la frecuencia antes de transformar.')
    if 'periodo' in frame and len(frame)>2:
        if not pd.api.types.is_numeric_dtype(frame['periodo']):raise EngineError('IRREGULAR_PERIOD','En esta versión, periodo debe ser numérico y regular.')
        spacing=np.diff(frame['periodo'].to_numpy(dtype=float))
        if not np.allclose(spacing,spacing[0]):raise EngineError('IRREGULAR_PERIOD','Hay períodos ausentes o frecuencia irregular. Regulariza el calendario explícitamente antes de usar esta herramienta temporal.')
    return frame


def ensure_contiguous(data):
    if len(data)>1 and (not data.index.is_monotonic_increasing or not np.all(np.diff(data.index.to_numpy())==1)):
        raise EngineError('IRREGULAR_PERIOD','No se pueden comprimir faltantes internos o mezclar filas al estimar una serie temporal.')


def predict(model,frame):
    fit=model.fit
    if model.kind=='arima':
        values=sample(time_order(frame),columns(frame,model.target),1);ensure_contiguous(values)
        if model.frame.index.max()>=values.index.min():
            raise EngineError('INVALID_PARAMETERS','El bloque de prueba temporal debe estar después del entrenamiento y conservar sus índices.')
        return np.asarray(fit.forecast(len(values))),values[model.target].to_numpy(),values
    names=list(dict.fromkeys([*model.features,*([model.target] if model.target else [])]))
    values=sample(frame,columns(frame,','.join(names)),2)
    design=values[model.features]
    if model.kind in ['ols','multiple_ols','robust','iv2sls','logit','ecm','covariance']: design=sm.add_constant(design,has_constant='add')
    if model.kind in ['hmm','gmm','kmeans']: return fit.predict(design.to_numpy()),None,values
    return np.asarray(fit.predict(design)),values[model.target].to_numpy(),values


def model_sample(model):
    return digest({'target':model.target,'rows':model.frame[[model.target]].to_json(orient='split',double_precision=15) if model.target else model.frame.to_json(orient='split',double_precision=15)})


def calculate(kind,inputs,params):
    frame=inputs.get('data')
    if kind=='synthetic':
        frame=synthetic(params);result=frame_result(frame,'Datos artificiales; escenario y semilla explícitos.');result['scenario_info']=NODE_CATALOG['synthetic']['scenario_info'][params.get('scenario','regression')];return result,{'data':frame}
    if kind=='report':
        incoming=inputs['result'];result=dict(incoming)
        result['teaching_note']=str(params.get('note','Interpreta la muestra y sus supuestos.'))
        return result,{'result':result}
    if kind in ['log','deflate','per_capita','growth','lag','difference','polynomial','compound','signal','standardize','apply_scaler','sample']:
        data=frame.copy();note='Transformación de la tabla conectada; los faltantes se conservan.';extra={}
        if kind=='log':
            names=columns(data,params.get('columns','capital,trabajo,produccion'))
            if (data[names].dropna()<=0).any().any(): raise EngineError('INVALID_PARAMETERS','El logaritmo requiere valores positivos.')
            for name in names: data['log_'+name]=np.log(data[name])
        elif kind=='deflate':
            value,index=columns(data,','.join([params.get('nominal','nominal'),params.get('index','indice')]))
            if (data[index].dropna()<=0).any(): raise EngineError('INVALID_PARAMETERS','El índice de precios debe ser positivo.')
            data[params.get('output','real')]=data[value]/data[index]*number(params,'base',100,.0001,1e6)
        elif kind=='per_capita':
            value,pop=columns(data,','.join([params.get('value','real'),params.get('population','poblacion')]))
            if (data[pop].dropna()<=0).any(): raise EngineError('INVALID_PARAMETERS','La población debe ser positiva.')
            data[params.get('output','real_per_capita')]=data[value]/data[pop]
        elif kind in ['growth','lag','difference']:
            time_order(data);name=columns(data,params.get('column','valor' if kind=='growth' else 'y'))[0]
            periods=number(params,'periods',1,1,100,True)
            if kind=='growth':
                if (data[name].shift(1).dropna()==0).any(): raise EngineError('INVALID_PARAMETERS','El período base no puede ser cero.')
                data[params.get('output','crecimiento')]=data[name].pct_change(fill_method=None)*100
            elif kind=='lag':data[f'lag_{periods}_{name}']=data[name].shift(periods)
            else:data[f'diff_{periods}_{name}']=data[name].diff(periods)
        elif kind=='polynomial':
            name=columns(data,params.get('column','x'))[0];degree=number(params,'degree',3,2,8,True)
            for power in range(2,degree+1): data[f'{name}{power}']=data[name]**power
        elif kind=='compound':
            names=columns(data,params.get('columns','r1,r2,r3,r4,r5'))
            if (data[names].dropna()<=-1).any().any():raise EngineError('INVALID_PARAMETERS','Las tasas deben ser mayores a -1.')
            data[params.get('output','precio')]=number(params,'initial',100,.001,1e9)*(1+data[names]).prod(axis=1,skipna=False)
        elif kind=='signal':
            time_order(data);name=columns(data,params.get('column','retorno'))[0];window=number(params,'lookback',5,1,100,True)
            past=data[name].rolling(window).mean().shift(1)
            data[params.get('output','senal')]=np.where(past.isna(),0.,(past>0).astype(float))
        elif kind=='standardize':
            from sklearn.preprocessing import StandardScaler
            names=columns(data,params.get('columns','x'));scaler=StandardScaler().fit(sample(data,names))
            data[names]=scaler.transform(data[names]);extra['transformer']=Scaler(scaler,names)
            note=f'Escalador ajustado solo a estas {int(scaler.n_samples_seen_)} filas completas. Usa Aplicar escalador para la prueba.'
        elif kind=='apply_scaler':
            transformer=inputs['transformer'];names=columns(data,','.join(transformer.columns));data[names]=transformer.fit.transform(data[names])
            note='Se aplicó un escalador existente sin volver a ajustarlo.'
        elif kind=='sample':
            n=number(params,'n',100,2,min(10000,len(data)),True);seed=number(params,'seed',42,0,2**32-1,True);method=params.get('method','aleatorio')
            if method=='sesgado':
                name=columns(data,params.get('column','valor'))[0];data=data[data[name]>data[name].quantile(.75)]
            elif method!='aleatorio':raise EngineError('INVALID_PARAMETERS','El muestreo debe ser aleatorio o sesgado.')
            if len(data)<n:raise EngineError('INSUFFICIENT_SAMPLE','La población elegible es menor que la muestra solicitada.')
            data=data.sample(n=n,random_state=seed).sort_index().copy();note='Muestreo sin reemplazo; se conserva el orden de las filas seleccionadas.'
        if len(data.columns)>50:raise EngineError('INVALID_PARAMETERS','La transformación supera 50 columnas.')
        return frame_result(data,note),{'data':data,**extra}
    if kind=='split':
        fraction=number(params,'fraction',.75,.1,.9);cut=int(len(frame)*fraction)
        if cut<4 or len(frame)-cut<4:raise EngineError('INSUFFICIENT_SAMPLE','Cada partición necesita al menos cuatro filas.')
        method=params.get('method','temporal');data=frame
        if method=='aleatorio': data=frame.sample(frac=1,random_state=number(params,'seed',42,0,2**32-1,True))
        elif method=='temporal':time_order(frame)
        else:raise EngineError('INVALID_PARAMETERS','Usa temporal o aleatorio.')
        train,test=data.iloc[:cut].copy(),data.iloc[cut:].copy()
        result=report('Partición sin ajustar modelos ni escaladores.',n_entrenamiento=len(train),n_prueba=len(test));result['n']=len(data)
        result['tables']=[table('Índices de las particiones',['Partición','Filas','Primer índice','Último índice'],[['train',len(train),int(train.index[0]),int(train.index[-1])],['test',len(test),int(test.index[0]),int(test.index[-1])]])]
        return result,{'train':train,'test':test,'result':result}
    result=report();outputs={}
    if kind in ['multiple_ols','robust','iv2sls','logit','mlp']:
        features=columns(frame,params.get('features','x'));target=columns(frame,params.get('y','y'))[0]
        if target in features:raise EngineError('INVALID_PARAMETERS','La respuesta no puede ser uno de sus regresores.')
        names=[*features,target];instruments=[]
        if kind=='iv2sls':instruments=columns(frame,params.get('instruments','z'));names=list(dict.fromkeys([*names,*instruments]))
        data=sample(frame,names,max(8,len(features)+3));design=sm.add_constant(data[features],has_constant='add')
        if np.linalg.matrix_rank(design)<design.shape[1]:raise EngineError('RANK_DEFICIENT','La matriz de diseño no tiene rango completo.')
        if kind=='multiple_ols':
            cov=params.get('covariance','nonrobust')
            if cov not in ['nonrobust','HC3']:raise EngineError('INVALID_PARAMETERS','Selecciona nonrobust o HC3.')
            fit=sm.OLS(data[target],design).fit(cov_type=cov)
        elif kind=='robust':fit=sm.RLM(data[target],design,M=sm.robust.norms.HuberT()).fit()
        elif kind=='iv2sls':
            from statsmodels.sandbox.regression.gmm import IV2SLS
            instrument_design=sm.add_constant(data[instruments],has_constant='add')
            if instrument_design.shape[1]<design.shape[1] or np.linalg.matrix_rank(instrument_design)<instrument_design.shape[1]:raise EngineError('RANK_DEFICIENT','Se necesitan instrumentos suficientes e independientes.')
            fit=IV2SLS(data[target],design,instrument_design).fit()
        elif kind=='logit':
            if not set(data[target].unique()).issubset({0,1}) or len(data[target].unique())!=2:raise EngineError('INVALID_PARAMETERS','La respuesta debe contener ambas clases 0 y 1.')
            method=params.get('method','logit')
            if method not in ['logit','probit']:raise EngineError('INVALID_PARAMETERS','Selecciona logit o probit.')
            fit=(sm.Logit if method=='logit' else sm.Probit)(data[target],design).fit(disp=False)
            if not fit.mle_retvals.get('converged',False):raise EngineError('NON_CONVERGENCE','El clasificador no convergió.')
        else:
            from sklearn.neural_network import MLPRegressor
            fit=MLPRegressor(hidden_layer_sizes=(number(params,'hidden',12,1,100,True),),solver='lbfgs',max_iter=1200,random_state=number(params,'seed',42,0,2**32-1,True)).fit(data[features],data[target])
        model=Fitted(kind,fit,data,features,target,kind);outputs['model']=model
        result=regression_report(model) if kind!='mlp' else report('Red ajustada; conecta datos de prueba para evaluar sin reajustar.',n_ajuste=len(data),iteraciones=fit.n_iter_)
        result['n']=len(data);result['dropped']=len(frame)-len(data)
        if kind=='multiple_ols':
            interval=fit.conf_int()
            result['regression']={'y':target,'features':features,'n':len(data),'dropped':len(frame)-len(data),'r_squared':float(fit.rsquared),'r_squared_adj':float(fit.rsquared_adj),'aic':float(fit.aic),'bic':float(fit.bic),'covariance':cov,'coefficients':[{'term':name,'estimate':float(fit.params[name]),'std_error':float(fit.bse[name]),'p_value':float(fit.pvalues[name]),'ci_low':float(interval.loc[name,0]),'ci_high':float(interval.loc[name,1])} for name in fit.params.index]}
            result['metrics'].extend([{'label':'R²','value':fit.rsquared},{'label':'R² ajustado','value':fit.rsquared_adj}])
    elif kind in ['arima','garch']:
        name=columns(frame,params.get('column','y' if kind=='arima' else 'retorno'))[0];data=sample(time_order(frame),[name],20);ensure_contiguous(data)
        if kind=='arima':
            from statsmodels.tsa.arima.model import ARIMA
            order=tuple(number(params,k,v,0,5,True) for k,v in [('p',1),('d',0),('q',0)])
            fit=ARIMA(data[name].to_numpy(),order=order).fit()
            if not fit.mle_retvals.get('converged',False):raise EngineError('NON_CONVERGENCE','ARIMA no convergió.')
            result=report('ARIMA ajustado solo a su tabla de entrada. Evalúa con otra tabla.',AIC=fit.aic,BIC=fit.bic,n_ajuste=len(data))
        else:
            from arch import arch_model
            fit=arch_model(data[name].to_numpy(),mean='Zero',vol='GARCH',p=number(params,'p',1,1,5,True),q=number(params,'q',1,1,5,True),rescale=False).fit(disp='off')
            if fit.convergence_flag:raise EngineError('NON_CONVERGENCE','GARCH no convergió.')
            result=report('Volatilidad estimada sobre los retornos conectados.',AIC=fit.aic,BIC=fit.bic)
            result['tables']=[table('Parámetros de volatilidad',['Parámetro','Estimación'],[[name,value] for name,value in fit.params.items()])];result['series']=[series('Volatilidad condicional',fit.conditional_volatility)]
        outputs['model']=Fitted(kind,fit,data,[],name,kind);result['n']=len(data);result['dropped']=len(frame)-len(data)
    elif kind in ['hmm','gmm','kmeans']:
        os.environ.setdefault('LOKY_MAX_CPU_COUNT','1')
        names=columns(frame,params.get('columns','valor'));data=sample(frame,names,10);seed=number(params,'seed',42,0,2**32-1,True)
        if kind=='hmm':
            time_order(frame);ensure_contiguous(data)
            from hmmlearn.hmm import GaussianHMM
            fit=GaussianHMM(n_components=number(params,'states',2,2,5,True),n_iter=150,tol=1e-4,random_state=seed).fit(data.to_numpy())
            history=list(fit.monitor_.history);converged=len(history)>1 and abs(history[-1]-history[-2])<fit.tol
            result=report('Se estiman estados y transiciones. Las etiquetas pueden permutarse.',log_verosimilitud=fit.score(data.to_numpy()),tolerancia_alcanzada=int(converged))
            if not converged:result['limitations'].append('No se alcanzó la tolerancia de convergencia; revisa la muestra y los parámetros.')
            result['tables']=[table('Transiciones',['Desde',*[f'Hacia {i}' for i in range(fit.n_components)]],[[i,*row] for i,row in enumerate(fit.transmat_)])]
        elif kind=='gmm':
            from sklearn.mixture import GaussianMixture
            fit=GaussianMixture(n_components=number(params,'components',2,2,5,True),random_state=seed).fit(data.to_numpy())
            if not fit.converged_:raise EngineError('NON_CONVERGENCE','La mezcla no convergió.')
            result=report('Mezcla sin dependencia temporal; no es un HMM ni el método generalizado de momentos.',log_verosimilitud=fit.score(data.to_numpy())*len(data))
        else:
            from sklearn.cluster import KMeans
            fit=KMeans(n_clusters=number(params,'clusters',3,2,min(10,len(data)-1),True),n_init=10,random_state=seed).fit(data.to_numpy())
            result=report('Agrupación por distancia sobre las columnas conectadas.',inercia=fit.inertia_)
            result['tables']=[table('Centroides en escala de entrada',['Grupo',*names],[[i,*row] for i,row in enumerate(fit.cluster_centers_)])]
        outputs['model']=Fitted(kind,fit,data,names,None,kind);result['n']=len(data)
    elif kind=='evaluate':
        model=inputs['model']
        if model.kind in ['hmm','gmm','kmeans','garch']:raise EngineError('TYPE_MISMATCH','Este modelo necesita su diagnóstico específico, no evaluación de una respuesta.')
        predicted,actual,data=predict(model,frame)
        result=report('Evaluación sobre la tabla conectada, sin volver a ajustar el modelo.',n_evaluacion=len(data),RMSE=np.sqrt(np.mean((actual-predicted)**2)),MAE=np.mean(np.abs(actual-predicted)))
        if model.kind=='logit':result['metrics'].append({'label':'exactitud_umbral_0.5','value':np.mean((predicted>=.5)==actual)})
        result['series']=[series('Observado',actual),series('Predicho',predicted)];result['n']=len(data)
    elif kind=='compare_models':
        first,second=inputs['first'],inputs['second'];same=model_sample(first)==model_sample(second) and first.kind in ['ols','multiple_ols','covariance'] and second.kind in ['ols','multiple_ols','covariance']
        rows=[]
        for model in [first,second]:
            if model.kind in ['hmm','gmm']:
                data=sample(frame,columns(frame,','.join(model.features)));values=data.to_numpy();score=model.fit.score(values)*(len(data) if model.kind=='gmm' else 1)
                rows.append([model.label,len(model.frame),len(data),score,None,None])
            else:
                predicted,actual,data=predict(model,frame);error=np.sqrt(np.mean((predicted-actual)**2))
                rows.append([model.label,len(model.frame),len(data),error,getattr(model.fit,'aic',None) if same else None,getattr(model.fit,'bic',None) if same else None])
        temporal_models={first.kind,second.kind}.issubset({'hmm','gmm'})
        result=report('Comparación sobre los mismos datos conectados. '+('Las verosimilitudes tienen supuestos temporales distintos; no bastan para escoger un modelo.' if temporal_models else 'Revisa si son datos de prueba o del propio ajuste.'))
        result['tables']=[table('Comparación',['Modelo','n ajuste','n evaluación','Loglik' if temporal_models else 'RMSE','AIC misma muestra','BIC misma muestra'],rows)]
        if not same:result['limitations'].append('Las muestras o especificaciones de ajuste difieren: AIC/BIC no se presentan como comparables.')
        result['limitations'].append('Evaluación declarada: '+str(params.get('evaluation','muestra_comun')))
    elif kind in ['diagnostics','covariance']:
        model=inputs['model'];fit=model.fit
        if kind=='covariance':
            if model.kind not in ['ols','multiple_ols','ecm','covariance']:raise EngineError('TYPE_MISMATCH','Esta herramienta requiere una regresión OLS.')
            method=params.get('method','HC3')
            if method not in ['HC3','HAC','nonrobust']:raise EngineError('INVALID_PARAMETERS','Selecciona HC3, HAC o nonrobust.')
            adjusted=sm.OLS(fit.model.endog,fit.model.exog).fit(cov_type=method,**({'cov_kwds':{'maxlags':1}} if method=='HAC' else {}))
            updated=replace(model,kind='covariance',fit=adjusted,label='OLS '+method);result=regression_report(updated,'La covarianza cambia la inferencia, no los coeficientes.');outputs['model']=updated
        elif model.kind=='garch':
            from statsmodels.stats.diagnostic import het_arch, acorr_ljungbox
            values=np.asarray(fit.std_resid);values=values[np.isfinite(values)]
            result=report('Diagnóstico de residuos estandarizados de GARCH.',p_ARCH_LM=het_arch(values,nlags=5)[1],p_Ljung_Box=acorr_ljungbox(values,lags=[5],return_df=True)['lb_pvalue'].iloc[0])
        elif model.kind in ['ols','multiple_ols','ecm','covariance']:
            from statsmodels.stats.diagnostic import het_breuschpagan,het_white,acorr_breusch_godfrey
            from statsmodels.stats.stattools import durbin_watson
            from statsmodels.stats.outliers_influence import variance_inflation_factor
            result=report('Contrasta supuestos del modelo conectado; no confunde errores estándar robustos con estimación robusta.',p_BP=het_breuschpagan(fit.resid,fit.model.exog)[1],p_White=het_white(fit.resid,fit.model.exog)[1],p_BG=acorr_breusch_godfrey(fit,nlags=2)[1],Durbin_Watson=durbin_watson(fit.resid))
            result['tables']=[table('Colinealidad',['Columna','VIF'],[[name,variance_inflation_factor(fit.model.exog,i)] for i,name in enumerate(fit.model.exog_names) if i])]
        else:raise EngineError('TYPE_MISMATCH','Usa la herramienta de evaluación específica de este modelo.')
    elif kind=='silhouette':
        from sklearn.metrics import silhouette_score
        model=inputs['model']
        if model.kind!='kmeans':raise EngineError('TYPE_MISMATCH','La silueta requiere un modelo k-means.')
        data=sample(frame,columns(frame,','.join(model.features)));labels=model.fit.predict(data.to_numpy())
        if len(set(labels))<2:raise EngineError('INSUFFICIENT_SAMPLE','La evaluación necesita al menos dos grupos.')
        result=report('Separación de grupos en la tabla conectada; no reajusta los centroides.',silueta=silhouette_score(data,labels,sample_size=min(2000,len(data)),random_state=42),n=len(data))
    elif kind in ['histogram','correlation','mean_ci','paired_test','probability','sampling_audit','unit_root','monte_carlo','backtest','quantile','pca','factor_analysis','cointegration','ecm','sem','acf']:
        result,extra=analyze(kind,inputs,params);outputs.update(extra)
    else:raise EngineError('INVALID_PARAMETERS','Herramienta no implementada.')
    if 'result' not in outputs:outputs['result']=result
    return result,outputs


def analyze(kind,inputs,params):
    frame=inputs.get('data');result=report();outputs={}
    if kind=='acf':
        from statsmodels.tsa.stattools import acf
        time_order(frame);names=columns(frame,params.get('columns','y,walk'));lags=number(params,'lags',10,1,40,True);rows=[]
        for name in names:
            data=sample(frame,[name],lags+2);ensure_contiguous(data);values=acf(data[name],nlags=lags)
            rows.extend([[name,i,value] for i,value in enumerate(values)])
        result=report('ACF de cada serie observada, en el orden temporal recibido. Se excluyen faltantes de cada columna.')
        result['tables']=[table('Autocorrelación',['Serie','Rezago','ACF'],rows)]
    elif kind=='sampling_audit':
        name=params.get('column','valor');rows=[]
        for port in ['population','sample','biased']:
            data=sample(inputs[port],columns(inputs[port],name));rows.append([port,len(data),data[name].mean(),data[name].std(ddof=1)])
        result=report('Compara población y muestras reales conectadas. La selección sesgada puede desplazar la media.')
        result['tables']=[table('Muestreo',['Entrada','Filas','Media','Desviación muestral'],rows)]
    elif kind=='histogram':
        name=columns(frame,params.get('column','y'))[0];data=sample(frame,[name],1);counts,bounds=np.histogram(data[name],bins=number(params,'bins',8,2,50,True))
        result=report('La suma de las frecuencias corresponde a la muestra completa de esta variable.',n=len(data),faltantes=len(frame)-len(data))
        result['n']=len(data)
        result['histogram']={'column':name,'n':len(data),'missing':len(frame)-len(data),'bins':[{'lower':float(bounds[i]),'upper':float(bounds[i+1]),'count':int(counts[i])} for i in range(len(counts))]}
        result['tables']=[table('Histograma',['Desde','Hasta','Frecuencia'],[[bounds[i],bounds[i+1],int(counts[i])] for i in range(len(counts))])]
    elif kind=='correlation':
        names=columns(frame,params.get('columns','ingreso,consumo'));data=sample(frame,names)
        result=report('Se utilizan las mismas filas completas para todas las columnas. Asociación no implica causalidad.',n=len(data),faltantes=len(frame)-len(data))
        result['tables']=[table('Correlación',['Variable',*names],[[name,*data.corr().loc[name].tolist()] for name in names]),table('Covarianza',['Variable',*names],[[name,*data.cov().loc[name].tolist()] for name in names])]
    elif kind=='mean_ci':
        name=columns(frame,params.get('column','valor'))[0];data=sample(frame,[name],2);confidence=number(params,'confidence',.95,.5,.999);se=data[name].std(ddof=1)/np.sqrt(len(data));lo,hi=stats.t.interval(confidence,len(data)-1,loc=data[name].mean(),scale=se)
        result=report('Intervalo t de la media de la tabla conectada. Su nivel describe cobertura del procedimiento, no probabilidad de un parámetro fijo.',n=len(data),media=data[name].mean(),error_estandar=se,limite_inferior=lo,limite_superior=hi)
    elif kind=='paired_test':
        before,after=columns(frame,','.join([params.get('before','antes'),params.get('after','despues')]))
        data=sample(frame,[before,after],3);test=stats.ttest_rel(data[after],data[before])
        result=report('Prueba de diferencias dentro de cada par. Compara tamaño del efecto e incertidumbre.',n=len(data),diferencia_media=(data[after]-data[before]).mean(),t=test.statistic,p_valor=test.pvalue)
    elif kind=='probability':
        name=columns(frame,params.get('column','valor'))[0];data=sample(frame,[name],2);prior=number(params,'prior',.01,.000001,.999999);sensitivity=number(params,'sensitivity',.95,0,1);false=number(params,'false_positive',.05,0,1)
        denominator=prior*sensitivity+(1-prior)*false
        if denominator==0:raise EngineError('INVALID_PARAMETERS','El evento condicionado tiene probabilidad cero.')
        rng=np.random.default_rng(number(params,'seed',42,0,2**32-1,True));replications=number(params,'replications',2000,100,10000,True);size=number(params,'sample_size',30,2,200,True)
        means=rng.choice(data[name].to_numpy(),size=(replications,size),replace=True).mean(axis=1)
        result=report('Bayes usa tasas base explícitas; el TCL se explora remuestreando la tabla conectada.',posterior_Bayes=prior*sensitivity/denominator,media_poblacion_empirica=data[name].mean(),media_de_medias=means.mean(),desviacion_medias=means.std(ddof=1))
        result['series']=[series('Medias remuestreadas (primeras 200)',means)]
    elif kind=='unit_root':
        from statsmodels.tsa.stattools import adfuller
        names=columns(frame,params.get('columns','x,y'));time_order(frame);rows=[]
        for name in names:
            data=sample(frame,[name],20);ensure_contiguous(data);test=adfuller(data[name]);rows.append([name,len(data),test[0],test[1],test[2]])
        result=report('ADF contrasta raíz unitaria con constante. No rechazar no prueba que la serie tenga una raíz unitaria.')
        result['tables']=[table('ADF',['Serie','n','Estadístico','p-valor','Rezagos'],rows)]
    elif kind=='monte_carlo':
        name=columns(frame,params.get('column','precio'))[0];data=sample(frame,[name],2)[name];threshold=number(params,'threshold',120,-1e12,1e12)
        result=report('Resumen de las trayectorias conectadas; no vuelve a simularlas.',replicas=len(data),media=data.mean(),percentil_5=data.quantile(.05),percentil_95=data.quantile(.95),error_Monte_Carlo=data.std(ddof=1)/np.sqrt(len(data)),probabilidad_superar_umbral=np.mean(data>threshold))
    elif kind=='backtest':
        ret,signal=columns(frame,','.join([params.get('returns','retorno'),params.get('signal','senal')]))
        data=sample(time_order(frame),[ret,signal],10);ensure_contiguous(data);cost=number(params,'cost',.0005,0,.1)
        if not set(data[signal].unique()).issubset({0,1}):raise EngineError('INVALID_PARAMETERS','La señal debe ser 0 o 1.')
        turnover=np.abs(np.diff(np.r_[0.,data[signal].to_numpy()]));gross=data[ret].to_numpy()*data[signal].to_numpy();net=gross-turnover*cost
        result=report('Costos por cambio de posición. La entrada debe contener una señal causal; la herramienta no conoce cómo fue creada.',retorno_bruto=np.prod(1+gross)-1,retorno_neto=np.prod(1+net)-1,baseline=np.prod(1+data[ret])-1,n=len(data))
        result['series']=[series('Capital neto',np.cumprod(1+net))];result['limitations']=['Datos sintéticos; sin operaciones reales ni garantía de rentabilidad. La posición inicial se abre desde cero.']
    elif kind=='quantile':
        x,y=columns(frame,','.join([params.get('x','x'),params.get('y','y')]))
        data=sample(frame,[x,y],20)
        try:quantiles=[float(value.strip()) for value in str(params.get('quantiles','.25,.5,.75')).split(',')]
        except ValueError:raise EngineError('INVALID_PARAMETERS','Escribe cuantiles numéricos separados por coma.')
        if not 1<=len(quantiles)<=9 or any(not 0<q<1 for q in quantiles):raise EngineError('INVALID_PARAMETERS','Los cuantiles deben estar entre 0 y 1.')
        rows=[]
        for q in quantiles:
            fit=sm.QuantReg(data[y],sm.add_constant(data[[x]],has_constant='add')).fit(q=q,max_iter=2000);rows.append([q,*fit.params])
        result=report('Cuantiles condicionales ajustados a la misma tabla. Diferencias observadas no sustituyen un contraste formal.',n=len(data));result['tables']=[table('Cuantiles',['q','Intercepto','Pendiente'],rows)]
    elif kind in ['pca','factor_analysis']:
        from sklearn.decomposition import PCA,FactorAnalysis
        names=columns(frame,params.get('columns','x1,x2,x3,x4,x5,x6'));data=sample(frame,names,10);components=number(params,'components',2,1,min(len(names),len(data)),True)
        fit=PCA(n_components=components).fit(data) if kind=='pca' else FactorAnalysis(n_components=components,random_state=number(params,'seed',42,0,2**32-1,True)).fit(data)
        result=report('PCA maximiza varianza explicada; el modelo factorial separa ruido específico. La escala recibida afecta el resultado.',n=len(data),**({'varianza_explicada':fit.explained_variance_ratio_.sum()} if kind=='pca' else {'log_verosimilitud_promedio':fit.score(data)}))
        result['tables']=[table('Cargas',['Componente',*names],[[i+1,*row] for i,row in enumerate(fit.components_)])]
    elif kind=='cointegration':
        from statsmodels.tsa.stattools import coint
        x,y=columns(frame,','.join([params.get('x','x'),params.get('y','y')]))
        data=sample(time_order(frame),[x,y],30);ensure_contiguous(data);fit=sm.OLS(data[y],sm.add_constant(data[[x]],has_constant='add')).fit();output=frame.copy();output['equilibrio']=np.nan;output.loc[data.index,'equilibrio']=fit.resid
        test=coint(data[y],data[x]);result=report('Relación de largo plazo y error de equilibrio. Debe revisarse integración antes de interpretar cointegración.',p_Engle_Granger=test[1],pendiente_largo_plazo=fit.params[x],n=len(data));outputs['data']=output
    elif kind=='ecm':
        x,y,error=columns(frame,','.join([params.get('x','x'),params.get('y','y'),params.get('error','equilibrio')]))
        time_order(frame);data=pd.DataFrame({'delta_x':frame[x].diff(),'error_previo':frame[error].shift(1),'delta_y':frame[y].diff()}).dropna()
        data=sample(data,['delta_x','error_previo','delta_y'],8);ensure_contiguous(data);fit=sm.OLS(data['delta_y'],sm.add_constant(data[['delta_x','error_previo']],has_constant='add')).fit();model=Fitted('ecm',fit,data,['delta_x','error_previo'],'delta_y','ECM')
        result=regression_report(model,'El ajuste al equilibrio utiliza el error del período anterior, nunca el actual.');outputs['model']=model
    elif kind=='sem':
        import semopy
        if params.get('template','factor_path')!='factor_path':raise EngineError('INVALID_PARAMETERS','Solo está registrada la plantilla factor_path.')
        data=sample(frame,columns(frame,'x1,x2,x3,y'),30);fit=semopy.Model('factor =~ x1 + x2 + x3\ny ~ factor');optimization=fit.fit(data)
        if not optimization.success:raise EngineError('NON_CONVERGENCE','SEM no convergió.')
        estimates=fit.inspect();indices=semopy.calc_stats(fit)
        result=report('La primera carga fija la escala del factor. El ajuste no demuestra causalidad.',n=len(data),CFI=indices.loc['Value','CFI'],RMSEA=indices.loc['Value','RMSEA'])
        result['tables']=[table('Medición y trayectoria',['Respuesta','Operador','Predictor','Estimación'],estimates[['lval','op','rval','Estimate']].values.tolist())];result['limitations']=['Plantilla registrada: factor =~ x1 + x2 + x3; y ~ factor. No acepta expresiones Python.']
    return result,outputs


def run_tool(kind,inputs,params):
    if kind=='time_plot':
        from .time_plot import time_plot
        result=time_plot(inputs['data'],params)
        return finite_json(result),{'result':result}
    with warnings.catch_warnings(record=True) as messages:
        warnings.simplefilter('always')
        try: result,outputs=calculate(kind,inputs,params)
        except EngineError: raise
        except (ValueError,np.linalg.LinAlgError) as error:
            raise EngineError('ESTIMATION_ERROR','No se puede estimar con esta muestra o configuración: '+str(error)[:240]) from error
    if kind=='standardize':
        transformer=outputs['transformer'];result['transformer']={'columns':transformer.columns,'mean':transformer.fit.mean_.tolist(),'scale':transformer.fit.scale_.tolist(),'n_fit':int(transformer.fit.n_samples_seen_)}
    if result.get('kind')=='analysis':
        result.setdefault('topic',kind);result.setdefault('n',len(inputs['data']) if isinstance(inputs.get('data'),pd.DataFrame) else None)
        result['warnings']=list(dict.fromkeys([*result.get('warnings',[]),*[str(message.message) for message in messages]]))[:8]
        result.setdefault('scope','Cálculo sobre los artefactos de entrada; no completa todos los subtemas del módulo.')
    return finite_json(result),outputs
