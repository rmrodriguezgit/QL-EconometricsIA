"""Original reproducible teaching experiments. Only registered topics are executable."""
import warnings
import os
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from .core import EngineError, finite_json, number, ols


def table(title, columns, rows):
    return {'title': title, 'columns': columns, 'rows': rows}


def run_experiment(parameters):
    topic = parameters.get('topic', 'C01')
    if topic not in [f'C{i:02}' for i in range(1, 29)]:
        raise EngineError('INVALID_PARAMETERS', 'Selecciona un tema C01-C28.')
    seed = number(parameters, 'seed', 42, 0, 2**32 - 1, True)
    n = number(parameters, 'n', 300, 100, 1200, True)
    with warnings.catch_warnings(record=True) as messages:
        warnings.simplefilter('always')
        result = calculate(topic, n, seed)
    result.update({'kind': 'experiment', 'topic': topic, 'n': n, 'seed': seed,
                   'warnings': list(dict.fromkeys(str(message.message) for message in messages))[:8],
                   'scope': 'Experimento introductorio ejecutable; no completa todos los subtemas del módulo.'})
    return finite_json(result)


def calculate(topic, n, seed):
    os.environ.setdefault('LOKY_MAX_CPU_COUNT', '1')
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    y = 2 + .8*x + rng.normal(size=n)
    X = sm.add_constant(x)
    result = {'metrics': [], 'tables': [], 'series': [], 'interpretation': '', 'limitations': []}
    def metrics(**values):
        result['metrics'] = [{'label': key, 'value': value} for key, value in values.items()]
    def series(label, values):
        result['series'].append({'label': label, 'points': [[i, float(v)] for i, v in enumerate(values[:200])]})
    if topic == 'C01':
        fit = sm.OLS(y, X).fit()
        metrics(intercepto_estimado=fit.params[0], pendiente_real=.8, pendiente_estimada=fit.params[1], R2=fit.rsquared)
        result['interpretation'] = 'Conocemos el proceso generador: y = 2 + 0.8x + error. La muestra produce estimaciones cercanas, pero no idénticas a los parámetros.'
    elif topic == 'C02':
        nominal = 100 * np.cumprod(1 + rng.normal(.06, .01, 12))
        price = 100 * np.cumprod(1 + rng.normal(.03, .005, 12))
        population = np.linspace(10, 12, 12)
        real = nominal / price * 100
        result['tables'] = [table('Nominal, real y por habitante', ['Año', 'Nominal', 'Índice de precios', 'Real (base 100)', 'Real per cápita'], [[2000+i, nominal[i], price[i], real[i], real[i]/population[i]] for i in range(12)])]
        result['interpretation'] = 'Deflactar divide por el índice de precios relativo a 100. El ajuste per cápita usa la población del mismo período.'
        result['limitations'] = ['Unidades monetarias y población artificiales; no son cifras de ningún país.']
    elif topic == 'C03':
        counts, bounds = np.histogram(y, bins=8)
        result['tables'] = [table('Histograma: conteos verificables', ['Límite inferior', 'Límite superior', 'Frecuencia'], [[bounds[i], bounds[i+1], int(counts[i])] for i in range(8)])]
        series('Observaciones y (primeras 200)', y)
        metrics(total_contado=int(counts.sum()), observaciones=n)
        result['interpretation'] = 'Los intervalos del histograma cubren toda la muestra. Cambiar sus límites puede modificar la percepción del patrón.'
    elif topic == 'C04':
        result['tables'] = [table('Estadística de la muestra', ['Variable', 'Media', 'Mediana', 'Desviación muestral', 'Mínimo', 'Máximo'], [[name, v.mean(), np.median(v), v.std(ddof=1), v.min(), v.max()] for name,v in [('x',x),('y',y)]])]
        metrics(correlacion=np.corrcoef(x,y)[0,1], crecimiento_compuesto=(1.05**5-1))
        result['interpretation'] = 'La correlación resume asociación lineal; las medidas de centro y dispersión describen aspectos distintos de la distribución.'
    elif topic == 'C05':
        prevalence, sensitivity, false_positive = .01, .95, .05
        posterior = prevalence*sensitivity/(prevalence*sensitivity+(1-prevalence)*false_positive)
        means = rng.exponential(size=(2000,30)).mean(axis=1)
        metrics(probabilidad_previa=prevalence, probabilidad_condicional_Bayes=posterior, media_de_medias=means.mean(), desviacion_teorica=1/np.sqrt(30))
        series('Medias de muestras exponenciales', means)
        result['interpretation'] = 'La regla de Bayes incorpora la tasa base. El promedio de 30 variables exponenciales ilustra el teorema del límite central.'
    elif topic == 'C06':
        population = rng.lognormal(3, .7, 20000)
        random = rng.choice(population,n,replace=False)
        biased = rng.choice(population[population>np.quantile(population,.75)],n,replace=False)
        metrics(media_poblacional=population.mean(), muestra_aleatoria=random.mean(), muestra_sesgada=biased.mean())
        result['interpretation'] = 'Muestrear solo el cuartil superior genera sesgo de selección, aunque la muestra tenga el mismo tamaño.'
    elif topic == 'C07':
        sample = rng.normal(10,3,n)
        se = sample.std(ddof=1)/np.sqrt(n)
        lo, hi = stats.t.interval(.95,n-1,loc=sample.mean(),scale=se)
        metrics(media_real=10, media_estimada=sample.mean(), error_estandar=se, IC95_inferior=lo, IC95_superior=hi)
        result['interpretation'] = 'El intervalo t refleja incertidumbre del promedio. En muestreos repetidos, su procedimiento cubre la media aproximadamente el 95 % de las veces.'
    elif topic == 'C08':
        before = rng.normal(50,8,n)
        after = before + rng.normal(.5,2,n)
        test = stats.ttest_rel(after,before)
        metrics(efecto_medio=(after-before).mean(), estadistico_t=test.statistic, p_valor=test.pvalue)
        result['interpretation'] = 'La prueba usa diferencias dentro de cada par. Un p-valor pequeño no determina si el tamaño del cambio resulta importante en la práctica.'
    elif topic == 'C09':
        fit = ols(pd.DataFrame({'x':x,'y':y}), {'x':'x','y':'y','covariance':'HC3'})
        result['tables']=[table('Regresión OLS simple', ['Término','Coeficiente','Error estándar HC3','p-valor','IC95 inferior','IC95 superior'], [[r[k] for k in ['term','estimate','std_error','p_value','ci_low','ci_high']] for r in fit['coefficients']])]
        metrics(R2=fit['r_squared'], muestra_efectiva=fit['n'])
        result['interpretation'] = fit['note']
    elif topic == 'C10':
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        z = .9*x + rng.normal(0,.2,n)
        design = sm.add_constant(np.column_stack([x,z]))
        fit = sm.OLS(1+.7*x+.3*z+rng.normal(size=n),design).fit()
        metrics(R2=fit.rsquared, F=fit.fvalue, p_F=fit.f_pvalue, VIF_x=variance_inflation_factor(design,1))
        result['tables'] = [table('Regresión múltiple', ['Término','Estimación','Error estándar'], [[label,fit.params[i],fit.bse[i]] for i,label in enumerate(['Constante','x','z'])])]
        result['interpretation'] = 'x y z están muy correlacionadas. La multicolinealidad aumenta la incertidumbre de coeficientes individuales sin impedir necesariamente un buen ajuste global.'
    elif topic == 'C11':
        from statsmodels.stats.diagnostic import het_breuschpagan, het_white, acorr_breusch_godfrey
        y = 1+x+rng.normal(size=n)*(.2+2*np.abs(x))
        fit = sm.OLS(y,X).fit()
        bp = het_breuschpagan(fit.resid, np.column_stack([X,x*x]))
        white = het_white(fit.resid,X)
        bg = acorr_breusch_godfrey(fit,nlags=2)
        robust = fit.get_robustcov_results(cov_type='HC3')
        metrics(p_Breusch_Pagan=bp[1],p_White=white[1],p_Breusch_Godfrey=bg[1], error_clasico=fit.bse[1],error_HC3=robust.bse[1])
        result['interpretation'] = 'La varianza del ruido crece con |x|. White detecta formas no lineales; HC3 cambia la inferencia y conserva los coeficientes OLS.'
    elif topic == 'C12':
        binary = rng.binomial(1, stats.logistic.cdf(-.4+1.2*x))
        cut = int(.75*n)
        logit = sm.Logit(binary[:cut],X[:cut]).fit(disp=False)
        probit = sm.Probit(binary[:cut],X[:cut]).fit(disp=False)
        metrics(exactitud_logit=np.mean((logit.predict(X[cut:])>=.5)==binary[cut:]), exactitud_probit=np.mean((probit.predict(X[cut:])>=.5)==binary[cut:]), n_prueba=n-cut)
        result['tables']=[table('Respuesta binaria', ['Modelo','Intercepto','Pendiente'], [['Logit',*logit.params],['Probit',*probit.params]])]
        result['interpretation'] = 'Ambos modelos generan probabilidades entre cero y uno. La precisión se calcula fuera de la muestra de ajuste; sus coeficientes usan escalas diferentes.'
    elif topic == 'C13':
        capital, labor = rng.lognormal(2,.5,(2,n))
        output = 1.5*capital**.35*labor**.6*np.exp(rng.normal(0,.1,n))
        fit=sm.OLS(np.log(output),sm.add_constant(np.column_stack([np.log(capital),np.log(labor)]))).fit()
        metrics(elasticidad_capital=fit.params[1],elasticidad_trabajo=fit.params[2], suma_elasticidades=fit.params[1:].sum())
        result['interpretation'] = 'En el modelo Cobb-Douglas, los coeficientes de log capital y log trabajo son elasticidades. Todas las variables simuladas son positivas.'
    elif topic == 'C14':
        from statsmodels.tsa.stattools import acf
        ar=np.zeros(n); walk=np.cumsum(rng.normal(size=n))
        for t in range(1,n): ar[t]=.7*ar[t-1]+rng.normal()
        metrics(autocorrelacion_AR1=acf(ar,nlags=1)[1],autocorrelacion_random_walk=acf(walk,nlags=1)[1])
        series('AR(1) estacionario',ar);series('Paseo aleatorio',walk)
        result['interpretation'] = 'Ambas series tienen dependencia temporal, pero el paseo aleatorio acumula perturbaciones y no revierte a una media fija.'
    elif topic == 'C15':
        from statsmodels.tsa.arima.model import ARIMA
        values=np.zeros(n)
        for t in range(1,n): values[t]=.75*values[t-1]+rng.normal()
        cut=int(.8*n); fit=ARIMA(values[:cut],order=(1,0,0)).fit()
        prediction=fit.forecast(n-cut)
        metrics(RMSE_ARIMA=np.sqrt(np.mean((prediction-values[cut:])**2)),RMSE_ingenuo=np.sqrt(np.mean((values[cut-1]-values[cut:])**2)),n_entrenamiento=cut,n_prueba=n-cut)
        series('Observaciones de prueba',values[cut:]);series('Pronóstico ARIMA',prediction)
        result['interpretation'] = 'El ajuste usa solo el pasado. El bloque final queda reservado para evaluar el pronóstico frente a un baseline constante.'
    elif topic == 'C16':
        from statsmodels.tsa.stattools import adfuller, coint
        trend=np.cumsum(rng.normal(size=n)); related=1.5*trend+rng.normal(0,.4,n)
        fit=sm.OLS(related,sm.add_constant(trend)).fit(); residual=fit.resid
        ecm=sm.OLS(np.diff(related),sm.add_constant(np.column_stack([np.diff(trend),residual[:-1]]))).fit()
        metrics(p_ADF_nivel=adfuller(trend)[1],p_cointegracion=coint(related,trend)[1],ajuste_error=ecm.params[2])
        result['interpretation'] = 'Dos series con tendencia común pueden tener una combinación estacionaria. La corrección de errores relaciona el cambio actual con el desvío previo del equilibrio.'
        result['limitations']=['Es un caso sintético de una relación; Johansen y VECM de mayor dimensión quedan fuera de este experimento.']
    elif topic == 'C17':
        from arch import arch_model
        errors=np.zeros(n);variance=np.ones(n)
        for t in range(1,n):
            variance[t]=.1+.12*errors[t-1]**2+.8*variance[t-1]
            errors[t]=np.sqrt(variance[t])*rng.normal()
        fit=arch_model(errors,mean='Zero',vol='GARCH',p=1,q=1,rescale=False).fit(disp='off')
        if fit.convergence_flag != 0: raise EngineError('NON_CONVERGENCE','GARCH no convergió; cambia la semilla o aumenta la muestra.')
        metrics(omega=fit.params['omega'],alpha=fit.params['alpha[1]'],beta=fit.params['beta[1]'],persistencia=fit.params['alpha[1]']+fit.params['beta[1]'])
        series('Volatilidad condicional estimada',fit.conditional_volatility)
        result['interpretation']='GARCH(1,1) estima una varianza dependiente de perturbaciones y varianzas pasadas. El motor comprueba convergencia.'
        result['limitations']=['Ejemplo univariado; no implementa EGARCH ni GARCH multivariado.']
    elif topic == 'C18':
        y=2+.8*x+rng.normal(size=n)*(.3+np.abs(x))
        rows=[]
        for q in [.25,.5,.75]:
            fit=sm.QuantReg(y,X).fit(q=q,max_iter=2000)
            rows.append([q,*fit.params])
        result['tables']=[table('Regresión por cuantiles', ['Cuantil','Intercepto','Pendiente'],rows)]
        result['interpretation']='Los cuantiles describen distintas partes de la respuesta condicional. Sus diferencias no sustituyen un contraste formal entre coeficientes.'
    elif topic == 'C19':
        y[:10]+=25
        classic=sm.OLS(y,X).fit();robust=sm.RLM(y,X,M=sm.robust.norms.HuberT()).fit()
        metrics(pendiente_real=.8,pendiente_OLS=classic.params[1],pendiente_Huber=robust.params[1])
        result['interpretation']='Huber reduce el peso de residuos grandes. Es un cambio de estimación, distinto de usar errores estándar HC3 con OLS.'
    elif topic == 'C20':
        from sklearn.decomposition import PCA, FactorAnalysis
        from sklearn.preprocessing import StandardScaler
        latent=rng.normal(size=(n,2)); values=latent@np.array([[1,.9,.8,0,0,0],[0,0,0,1,.9,.8]])+rng.normal(0,.3,(n,6))
        scaled=StandardScaler().fit_transform(values)
        pca=PCA(n_components=2).fit(scaled);factor=FactorAnalysis(n_components=2,random_state=seed).fit(scaled)
        metrics(varianza_PCA_dos_componentes=pca.explained_variance_ratio_.sum(),log_verosimilitud_factorial=factor.score(scaled))
        result['tables']=[table('Cargas PCA', ['Componente','x1','x2','x3','x4','x5','x6'],[[i+1,*row] for i,row in enumerate(pca.components_)])]
        result['interpretation']='PCA maximiza varianza explicada; análisis factorial distingue factores comunes y ruido específico. Sus cargas no son equivalentes.'
    elif topic == 'C21':
        from statsmodels.sandbox.regression.gmm import IV2SLS
        z=rng.normal(size=n);u=rng.normal(size=n);endogenous=.9*z+.7*u+rng.normal(0,.3,n);outcome=1+2*endogenous+u
        design=sm.add_constant(endogenous)
        classic=sm.OLS(outcome,design).fit();iv=IV2SLS(outcome,design,sm.add_constant(z)).fit()
        metrics(pendiente_real=2,pendiente_OLS=classic.params[1],pendiente_IV2SLS=iv.params[1],correlacion_instrumento_regresor=np.corrcoef(z,endogenous)[0,1])
        result['interpretation']='z está relacionado con x y se genera independientemente del error. La comparación ilustra el sesgo de endogeneidad de OLS.'
        result['limitations']=['La exogeneidad del instrumento se conoce por construcción; en datos reales exige justificación. WLS/GLS/MLE/GMM son ampliaciones del módulo.']
    elif topic == 'C22':
        x=rng.uniform(-2,2,n);y=1+x+.4*x*x+rng.normal(0,.8,n);cut=int(.75*n);rows=[]
        for degree in range(1,7):
            design=np.column_stack([x**power for power in range(degree+1)])
            fit=sm.OLS(y[:cut],design[:cut]).fit();pred=fit.predict(design[cut:])
            rows.append([degree,fit.aic,fit.bic,np.sqrt(np.mean((pred-y[cut:])**2))])
        result['tables']=[table('Selección con muestra común', ['Grado','AIC entrenamiento','BIC entrenamiento','RMSE prueba'],rows)]
        result['interpretation']='AIC y BIC se calculan sobre la misma muestra de entrenamiento. El bloque de prueba mide capacidad predictiva sin reajustar los modelos.'
    elif topic == 'C23':
        returns=rng.normal(.0003,.012,n)
        signal=(pd.Series(returns).rolling(5).mean().shift(1)>0).astype(float).to_numpy()
        turnover=np.abs(np.diff(np.r_[0.,signal]));net=signal*returns-turnover*.0005
        cut=int(.7*n)
        gross=np.prod(1+signal[cut:]*returns[cut:])-1;after=np.prod(1+net[cut:])-1;benchmark=np.prod(1+returns[cut:])-1
        metrics(retorno_estrategia_bruto=gross,retorno_estrategia_con_costos=after,retorno_baseline=benchmark)
        series('Capital fuera de muestra',np.cumprod(1+net[cut:]))
        result['interpretation']='La señal usa solo rendimientos anteriores. Los costos se aplican cuando cambia la posición y se evalúa únicamente el tramo final.'
        result['limitations']=['Datos artificiales, sin selección de activos ni operaciones reales; no demuestran rentabilidad futura.']
    elif topic == 'C24':
        from hmmlearn.hmm import GaussianHMM
        from sklearn.mixture import GaussianMixture
        states=np.zeros(n,dtype=int)
        for t in range(1,n): states[t]=states[t-1] if rng.random()<.96 else 1-states[t-1]
        values=rng.normal(np.where(states==0,-2,2),.6).reshape(-1,1)
        hmm=GaussianHMM(n_components=2,n_iter=150,tol=1e-4,random_state=seed).fit(values)
        mixture=GaussianMixture(n_components=2,random_state=seed).fit(values)
        predicted=hmm.predict(values)
        metrics(acierto_estados_permutacion=max(np.mean(predicted==states),np.mean(1-predicted==states)),loglik_HMM=hmm.score(values),loglik_mezcla=mixture.score(values)*n,convergencia=int(hmm.monitor_.converged))
        result['tables']=[table('Transiciones estimadas HMM',['Estado origen','Hacia 0','Hacia 1'],[[i,*row] for i,row in enumerate(hmm.transmat_)])]
        result['interpretation']='El HMM estima transiciones temporales. La mezcla gaussiana asigna grupos sin ese mecanismo. Las etiquetas de estado se pueden permutar.'
    elif topic == 'C25':
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score
        labels=np.arange(n)%3;values=rng.normal(size=(n,2))*.3+np.array([[-2,-1],[0,2],[2,-1]])[labels]
        scale=StandardScaler().fit(values);scaled=scale.transform(values)
        fit=KMeans(n_clusters=3,n_init=10,random_state=seed).fit(scaled)
        metrics(silueta=silhouette_score(scaled,fit.labels_),inercia=fit.inertia_)
        result['tables']=[table('Centroides en unidades originales',['Grupo','Coordenada 1','Coordenada 2'],[[i,*row] for i,row in enumerate(scale.inverse_transform(fit.cluster_centers_))])]
        result['interpretation']='K-means agrupa por distancia después de escalar. Las etiquetas identifican grupos, no clases económicas conocidas.'
    elif topic == 'C26':
        from sklearn.neural_network import MLPRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline
        from sklearn.compose import TransformedTargetRegressor
        from sklearn.linear_model import LinearRegression
        x=rng.uniform(-3,3,(n,1));y=np.sin(x[:,0])+rng.normal(0,.1,n);cut=int(.8*n)
        model=TransformedTargetRegressor(regressor=make_pipeline(StandardScaler(),MLPRegressor(hidden_layer_sizes=(12,),solver='lbfgs',max_iter=1200,random_state=seed)),transformer=StandardScaler()).fit(x[:cut],y[:cut])
        baseline=LinearRegression().fit(x[:cut],y[:cut])
        metrics(RMSE_red_neuronal=np.sqrt(np.mean((model.predict(x[cut:])-y[cut:])**2)),RMSE_lineal=np.sqrt(np.mean((baseline.predict(x[cut:])-y[cut:])**2)),n_prueba=n-cut)
        result['interpretation']='La red aprende una relación no lineal. Los escaladores se ajustan únicamente dentro del entrenamiento y la prueba se compara con un modelo lineal.'
    elif topic == 'C27':
        prices=100*np.prod(1+rng.normal(.03,.015,(5000,5)),axis=1)
        metrics(precio_medio_cinco_anios=prices.mean(),percentil_5=np.quantile(prices,.05),percentil_95=np.quantile(prices,.95),error_Monte_Carlo=prices.std(ddof=1)/np.sqrt(5000),probabilidad_precio_mayor_120=np.mean(prices>120))
        result['interpretation']='Se simulan 5.000 trayectorias de inflación durante cinco años. Los percentiles describen escenarios bajo los supuestos del generador, no una predicción garantizada.'
    elif topic == 'C28':
        import semopy
        factor=rng.normal(size=n)
        data=pd.DataFrame({'x1':factor+rng.normal(0,.3,n),'x2':.8*factor+rng.normal(0,.3,n),'x3':1.2*factor+rng.normal(0,.3,n),'y':.7*factor+rng.normal(0,.5,n)})
        model=semopy.Model('factor =~ x1 + x2 + x3\ny ~ factor')
        fit=model.fit(data)
        if not fit.success: raise EngineError('NON_CONVERGENCE','El SEM no convergió para esta muestra.')
        estimates=model.inspect();stats_frame=semopy.calc_stats(model)
        metrics(CFI=float(stats_frame.loc['Value','CFI']),RMSEA=float(stats_frame.loc['Value','RMSEA']),grados_libertad=int(stats_frame.loc['Value','DoF']))
        result['tables']=[table('Modelo de medición y trayectorias',['Respuesta','Operador','Predictor','Estimación'],estimates[['lval','op','rval','Estimate']].values.tolist())]
        result['interpretation']='Tres indicadores miden un factor latente; una trayectoria lo relaciona con y. La primera carga fija la escala del factor para identificar el modelo.'
        result['limitations']=['El ajuste del SEM no demuestra causalidad. La estructura se conoce porque los datos fueron generados con ese mecanismo.']
    return result
