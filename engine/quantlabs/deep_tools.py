"""Redes multicapa definidas capa por capa y un agente de aprendizaje por refuerzo, en numpy.

Red multicapa (como en Quantlabs-Blueprints: Network Input → capas → Network Output → entrenador):
- ``nn_input``  define la capa de entrada (columnas y estandarización) y produce una especificación ``Network``.
- ``nn_layer``  añade una capa intermedia: densa (unidades + activación) o dropout. Se encadenan tantas como se quiera (≤ 12).
- ``nn_output`` cierra la red con la capa de salida: respuesta y tarea (regresión → lineal + MSE; clasificación → sigmoide + entropía cruzada).
- ``nn_train``  recibe la red y una tabla, entrena con retropropagación (Adam, RMSprop o SGD, L2, mini-lotes,
  parada temprana sobre la última fracción de las filas) y produce un ``FittedModel`` que ``evaluate`` acepta.

Aprendizaje por refuerzo (``rl_agent``): Q-learning o SARSA tabular para operar un activo con acciones
corto / efectivo / largo, recompensa = posición × rendimiento siguiente − costo por cambio de posición.
Entrena en el bloque inicial y evalúa la política codiciosa fuera de muestra frente a comprar y mantener.

Sin PyTorch ni TensorFlow: todo es numpy, reproducible con semilla y verificable con gradientes numéricos.
"""
from dataclasses import dataclass, field
import copy
import numpy as np
import pandas as pd

from .core import EngineError, number

DEEP_TOOLS = {'nn_input', 'nn_layer', 'nn_output', 'nn_train', 'rl_agent'}
ACTIVATIONS = ['relu', 'leaky_relu', 'elu', 'tanh', 'sigmoide', 'swish', 'lineal']
MAX_LAYERS = 12


def fail(message, code='INVALID_PARAMETERS'):
    raise EngineError(code, message)


def choice(params, key, options, default):
    value = params.get(key, default)
    if value not in options:
        fail(f'{key}: elige {", ".join(options)}.')
    return value


def names(value, label):
    items = [item.strip() for item in str(value or '').split(',') if item.strip()]
    if not items:
        fail(f'Indica {label} separadas por coma.')
    if len(set(items)) != len(items):
        fail(f'Hay {label} repetidas.')
    return items


# ---------------------------------------------------------------- activaciones

def activate(name, z):
    if name == 'relu':
        return np.maximum(z, 0)
    if name == 'leaky_relu':
        return np.where(z > 0, z, .01 * z)
    if name == 'elu':
        return np.where(z > 0, z, np.expm1(np.minimum(z, 0)))
    if name == 'tanh':
        return np.tanh(z)
    if name == 'sigmoide':
        return 1 / (1 + np.exp(-np.clip(z, -60, 60)))
    if name == 'swish':
        return z / (1 + np.exp(-np.clip(z, -60, 60)))
    return z


def derivative(name, z, a):
    if name == 'relu':
        return (z > 0).astype(float)
    if name == 'leaky_relu':
        return np.where(z > 0, 1., .01)
    if name == 'elu':
        return np.where(z > 0, 1., a + 1)
    if name == 'tanh':
        return 1 - a * a
    if name == 'sigmoide':
        return a * (1 - a)
    if name == 'swish':
        s = 1 / (1 + np.exp(-np.clip(z, -60, 60)))
        return s + z * s * (1 - s)
    return np.ones_like(z)


# ---------------------------------------------------------------- especificación de la red (artefacto Network)

def layer_rows(spec):
    """Tabla de arquitectura: forma de entrada/salida y parámetros de cada capa."""
    width = len(spec['input']['features'])
    rows = [['Entrada', f'{width} variables' + (' estandarizadas' if spec['input']['standardize'] else ''), '—', width, '—', 0]]
    for i, layer in enumerate(spec['layers'], 1):
        if layer['type'] == 'densa':
            rows.append([f'Oculta {i}', 'Densa', width, layer['units'], layer['activation'], width * layer['units'] + layer['units']])
            width = layer['units']
        else:
            rows.append([f'Oculta {i}', f'Dropout {layer["rate"]:.2f}', width, width, '—', 0])
    if spec.get('output'):
        out = spec['output']
        rows.append(['Salida', f'Densa → {out["target"]}', width, 1, 'sigmoide' if out['task'] == 'clasificacion' else 'lineal', width + 1])
    return rows


def architecture_table(spec):
    return {'title': 'Arquitectura de la red', 'columns': ['Capa', 'Operación', 'Entrada', 'Salida', 'Activación', 'Parámetros'], 'rows': layer_rows(spec)}


def spec_result(spec, text):
    rows = layer_rows(spec)
    return {'kind': 'analysis', 'interpretation': text, 'tables': [architecture_table(spec)], 'series': [], 'limitations': [], 'warnings': [],
            'metrics': [{'label': 'capas_ocultas', 'value': len(spec['layers'])}, {'label': 'parametros', 'value': int(sum(r[5] for r in rows))},
                        {'label': 'red_completa', 'value': 'sí' if spec.get('output') else 'no'}],
            'network': copy.deepcopy(spec)}


def need_network(inputs):
    spec = inputs.get('network')
    if not isinstance(spec, dict) or 'input' not in spec:
        fail('Conecta una capa de entrada (o una capa anterior) al puerto network.', 'TYPE_MISMATCH')
    return copy.deepcopy(spec)


def nn_input(params):
    features = names(params.get('features', 'x'), 'las columnas de entrada')
    if len(features) > 100:
        fail('Como máximo 100 variables de entrada.')
    standardize = choice(params, 'standardize', ['si', 'no'], 'si') == 'si'
    spec = {'input': {'features': features, 'standardize': standardize}, 'layers': [], 'output': None}
    return spec_result(spec, f'Capa de entrada con {len(features)} variables. Añade capas intermedias y cierra con una capa de salida.'), spec


def nn_layer(inputs, params):
    spec = need_network(inputs)
    if spec.get('output'):
        fail('La red ya tiene capa de salida: añade las capas intermedias antes de ella.')
    if len(spec['layers']) >= MAX_LAYERS:
        fail(f'Como máximo {MAX_LAYERS} capas intermedias.')
    kind = choice(params, 'layer_type', ['densa', 'dropout'], 'densa')
    if kind == 'densa':
        layer = {'type': 'densa', 'units': number(params, 'units', 16, 1, 512, True), 'activation': choice(params, 'activation', ACTIVATIONS, 'relu')}
    else:
        if not any(item['type'] == 'densa' for item in spec['layers']):
            fail('Coloca el dropout después de una capa densa.')
        layer = {'type': 'dropout', 'rate': number(params, 'rate', .2, 0, .9)}
    spec['layers'].append(layer)
    text = (f'Capa densa de {layer["units"]} neuronas con activación {layer["activation"]}.' if kind == 'densa'
            else f'Dropout: apaga al azar {layer["rate"]:.0%} de las neuronas en cada paso de entrenamiento (no al predecir).')
    return spec_result(spec, text), spec


def nn_output(inputs, params):
    spec = need_network(inputs)
    if spec.get('output'):
        fail('La red ya tiene una capa de salida.')
    if not any(item['type'] == 'densa' for item in spec['layers']):
        fail('Añade al menos una capa densa intermedia antes de la salida.')
    target = str(params.get('y', 'y')).strip()
    if not target or target in spec['input']['features']:
        fail('La respuesta debe ser una columna distinta de las de entrada.')
    spec['output'] = {'target': target, 'task': choice(params, 'task', ['regresion', 'clasificacion'], 'regresion')}
    task = 'una neurona lineal y error cuadrático medio' if spec['output']['task'] == 'regresion' else 'una neurona sigmoide y entropía cruzada binaria'
    return spec_result(spec, f'Capa de salida para {target}: {task}. Conecta la red y una tabla al entrenador.'), spec


# ---------------------------------------------------------------- red entrenable

@dataclass
class DeepNetwork:
    spec: dict
    weights: list = field(default_factory=list)
    x_mean: np.ndarray | None = None
    x_scale: np.ndarray | None = None
    y_mean: float = 0.
    y_scale: float = 1.

    @property
    def task(self):
        return self.spec['output']['task']

    def dense_layers(self):
        return [layer for layer in self.spec['layers'] if layer['type'] == 'densa']

    def init(self, rng):
        width = len(self.spec['input']['features'])
        self.weights = []
        for layer in self.dense_layers() + [{'units': 1, 'activation': 'lineal'}]:
            gain = 2. if layer['activation'] in ('relu', 'leaky_relu', 'elu', 'swish') else 1.
            self.weights.append([rng.normal(0, np.sqrt(gain / width), (width, layer['units'])), np.zeros(layer['units'])])
            width = layer['units']

    def forward(self, x, rng=None):
        """Devuelve la salida y la caché para retropropagación. rng ≠ None activa el dropout (entrenamiento)."""
        cache, a, w = [], x, 0
        for layer in self.spec['layers']:
            if layer['type'] == 'densa':
                W, b = self.weights[w]
                z = a @ W + b
                out = activate(layer['activation'], z)
                cache.append(('densa', a, z, out, layer['activation'], w))
                a, w = out, w + 1
            elif rng is not None and layer['rate'] > 0:
                mask = (rng.random(a.shape) >= layer['rate']) / (1 - layer['rate'])
                cache.append(('dropout', mask))
                a = a * mask
        W, b = self.weights[w]
        z = a @ W + b
        output = activate('sigmoide', z) if self.task == 'clasificacion' else z
        cache.append(('salida', a, w))
        return output[:, 0], cache

    def loss(self, output, y, l2):
        if self.task == 'clasificacion':
            p = np.clip(output, 1e-12, 1 - 1e-12)
            value = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
        else:
            value = np.mean((output - y) ** 2)
        return value + l2 * sum(float(np.sum(W * W)) for W, _ in self.weights) / 2

    def gradients(self, output, y, cache, l2):
        n = len(y)
        # Con sigmoide + entropía cruzada y con salida lineal + MSE el gradiente respecto de z es (salida − y) / n (× 2 en MSE).
        delta = ((output - y) * (1 if self.task == 'clasificacion' else 2) / n)[:, None]
        grads = [None] * len(self.weights)
        _, a, w = cache[-1]
        grads[w] = [a.T @ delta + l2 * self.weights[w][0], delta.sum(0)]
        delta = delta @ self.weights[w][0].T
        for entry in reversed(cache[:-1]):
            if entry[0] == 'dropout':
                delta = delta * entry[1]
                continue
            _, a, z, out, name, w = entry
            delta = delta * derivative(name, z, out)
            grads[w] = [a.T @ delta + l2 * self.weights[w][0], delta.sum(0)]
            delta = delta @ self.weights[w][0].T
        return grads

    def transform(self, frame):
        x = frame[self.spec['input']['features']].to_numpy(dtype=float)
        return (x - self.x_mean) / self.x_scale if self.x_mean is not None else x

    def predict(self, frame):
        output, _ = self.forward(self.transform(frame))
        return output if self.task == 'clasificacion' else output * self.y_scale + self.y_mean


def optimizer_step(net, grads, state, name, lr, t):
    for i, (pair, grad) in enumerate(zip(net.weights, grads)):
        for k in range(2):
            g = grad[k]
            if name == 'sgd':
                state[i][k][0] = .9 * state[i][k][0] + g
                pair[k] -= lr * state[i][k][0]
            elif name == 'rmsprop':
                state[i][k][1] = .9 * state[i][k][1] + .1 * g * g
                pair[k] -= lr * g / (np.sqrt(state[i][k][1]) + 1e-8)
            else:
                state[i][k][0] = .9 * state[i][k][0] + .1 * g
                state[i][k][1] = .999 * state[i][k][1] + .001 * g * g
                m, v = state[i][k][0] / (1 - .9 ** t), state[i][k][1] / (1 - .999 ** t)
                pair[k] -= lr * m / (np.sqrt(v) + 1e-8)


def nn_train(inputs, params):
    spec = need_network(inputs)
    if not spec.get('output'):
        fail('La red está incompleta: conecta una capa de salida antes del entrenador.')
    frame = inputs['data']
    features, target = spec['input']['features'], spec['output']['target']
    missing = [name for name in features + [target] if name not in frame.columns]
    if missing:
        fail(f'La tabla no tiene {", ".join(missing)}. Columnas disponibles: {", ".join(map(str, frame.columns))}.')
    data = frame[features + [target]].apply(pd.to_numeric, errors='coerce').dropna()
    if len(data) < 20:
        fail('Se necesitan al menos 20 filas completas para entrenar la red.', 'INSUFFICIENT_SAMPLE')
    epochs = number(params, 'epochs', 300, 1, 5000, True)
    batch = number(params, 'batch_size', 32, 2, 4096, True)
    lr = number(params, 'learning_rate', .01, 1e-6, 1)
    l2 = number(params, 'l2', 1e-4, 0, 10)
    patience = number(params, 'patience', 30, 1, 5000, True)
    fraction = number(params, 'validation', .2, 0, .5)
    optimizer = choice(params, 'optimizer', ['adam', 'rmsprop', 'sgd'], 'adam')
    seed = number(params, 'seed', 42, 0, 2**32 - 1, True)
    rng = np.random.default_rng(seed)
    task = spec['output']['task']
    y_all = data[target].to_numpy(dtype=float)
    if task == 'clasificacion' and not set(np.unique(y_all)).issubset({0., 1.}):
        fail('Para clasificación la respuesta debe valer 0 o 1.')
    # Validación = últimas filas (respeta el orden temporal); el escalado se aprende solo con el bloque de ajuste.
    n_val = int(round(len(data) * fraction)) if fraction > 0 else 0
    n_fit = len(data) - n_val
    if n_fit < 10:
        fail('La validación deja menos de 10 filas para ajustar.', 'INSUFFICIENT_SAMPLE')
    net = DeepNetwork(spec)
    x_all = data[features].to_numpy(dtype=float)
    if spec['input']['standardize']:
        net.x_mean = x_all[:n_fit].mean(0)
        net.x_scale = np.where(x_all[:n_fit].std(0) > 0, x_all[:n_fit].std(0), 1.)
    if task == 'regresion':
        net.y_mean, net.y_scale = float(y_all[:n_fit].mean()), float(y_all[:n_fit].std() or 1.)
    x = net.transform(data)
    y = y_all if task == 'clasificacion' else (y_all - net.y_mean) / net.y_scale
    net.init(rng)
    state = [[[np.zeros_like(p), np.zeros_like(p)] for p in pair] for pair in net.weights]
    history, best, best_weights, stale, step = [], np.inf, copy.deepcopy(net.weights), 0, 0
    for epoch in range(epochs):
        order = rng.permutation(n_fit)
        for start in range(0, n_fit, batch):
            idx = order[start:start + batch]
            output, cache = net.forward(x[idx], rng)
            step += 1
            optimizer_step(net, net.gradients(output, y[idx], cache, l2), state, optimizer, lr, step)
        train_loss = net.loss(net.forward(x[:n_fit])[0], y[:n_fit], 0)
        val_loss = net.loss(net.forward(x[n_fit:])[0], y[n_fit:], 0) if n_val else train_loss
        if not np.isfinite(train_loss):
            fail('El entrenamiento divergió: reduce la tasa de aprendizaje o estandariza las entradas.', 'NON_CONVERGENCE')
        history.append((train_loss, val_loss))
        if val_loss < best - 1e-10:
            best, best_weights, stale = val_loss, copy.deepcopy(net.weights), 0
        else:
            stale += 1
            if stale >= patience:
                break
    net.weights = best_weights
    fitted = net.predict(data)
    rows = layer_rows(spec)
    metrics = {'n_ajuste': n_fit, 'n_validacion': n_val, 'epocas': len(history), 'mejor_epoca': int(np.argmin([h[1] for h in history]) + 1),
               'parametros': int(sum(r[5] for r in rows)), 'perdida_validacion': float(best)}
    if task == 'clasificacion':
        for label, part in [('ajuste', slice(0, n_fit)), ('validacion', slice(n_fit, None))]:
            if len(y_all[part]):
                metrics[f'exactitud_{label}'] = float(np.mean((fitted[part] >= .5) == y_all[part]))
    else:
        for label, part in [('ajuste', slice(0, n_fit)), ('validacion', slice(n_fit, None))]:
            actual, pred = y_all[part], fitted[part]
            if len(actual) > 1 and np.var(actual) > 0:
                metrics[f'R2_{label}'] = float(1 - np.mean((actual - pred) ** 2) / np.var(actual))
                metrics[f'RMSE_{label}'] = float(np.sqrt(np.mean((actual - pred) ** 2)))
    result = {'kind': 'analysis', 'metrics': [{'label': k, 'value': v} for k, v in metrics.items()],
              'interpretation': (f'Red multicapa entrenada con {optimizer} ({len(history)} épocas, parada temprana con paciencia {patience}). '
                                 'Se conservan los pesos de la mejor época de validación. Evalúa con datos de prueba separados.'),
              'tables': [architecture_table(spec)],
              'series': [{'label': 'Pérdida de entrenamiento', 'points': [[i + 1, float(h[0])] for i, h in enumerate(history)][-400:]},
                         {'label': 'Pérdida de validación', 'points': [[i + 1, float(h[1])] for i, h in enumerate(history)][-400:]}],
              'limitations': ['Una red puede sobreajustar: compárala con un modelo lineal en una muestra de prueba.',
                              'Los pesos dependen de la semilla; cambia la semilla para ver la variación.'], 'warnings': []}
    if n_val == 0:
        result['warnings'].append('Sin validación: la parada temprana usa la pérdida de ajuste.')
    from .tools import Fitted
    model = Fitted('deep_mlp', net, data, features, target, f'Red {"-".join(str(l["units"]) for l in net.dense_layers())} ({task})')
    return result, {'model': model, 'result': result}


# ---------------------------------------------------------------- aprendizaje por refuerzo

def max_drawdown(equity):
    return float(np.min(equity / np.maximum.accumulate(equity) - 1) * 100)


def rl_agent(inputs, params):
    frame = inputs['data']
    ret_name = str(params.get('returns', 'retorno'))
    state_names = names(params.get('state', ret_name), 'las variables de estado')
    for name in [ret_name, *state_names]:
        if name not in frame.columns:
            fail(f'No existe la columna «{name}». Disponibles: {", ".join(map(str, frame.columns))}.')
    unit = choice(params, 'unit', ['decimal', 'porcentaje'], 'decimal')
    method = choice(params, 'method', ['q_learning', 'sarsa'], 'q_learning')
    bins = number(params, 'bins', 3, 2, 10, True)
    episodes = number(params, 'episodes', 200, 1, 5000, True)
    alpha = number(params, 'alpha', .1, 1e-4, 1)
    gamma = number(params, 'gamma', .9, 0, .999)
    eps_end = number(params, 'epsilon', .05, 0, 1)
    cost = number(params, 'cost_bps', 5, 0, 1000) / 10000
    fraction = number(params, 'fraction', .7, .3, .9)
    per_year = number(params, 'periods_per_year', 252, 1, 100000, True)
    seed = number(params, 'seed', 42, 0, 2**32 - 1, True)
    data = frame[list(dict.fromkeys([ret_name, *state_names]))].apply(pd.to_numeric, errors='coerce').dropna()
    if len(data) < 40:
        fail('Se necesitan al menos 40 filas completas.', 'INSUFFICIENT_SAMPLE')
    returns = data[ret_name].to_numpy(dtype=float) / (100 if unit == 'porcentaje' else 1)
    # El estado en t usa valores conocidos en t; la recompensa usa el rendimiento de t+1 (sin mirar el futuro).
    n = len(data) - 1
    n_train = int(n * fraction)
    edges = [np.quantile(data[name].to_numpy()[:n_train], np.linspace(0, 1, bins + 1)[1:-1]) for name in state_names]
    codes = np.zeros(len(data), dtype=int)
    for name, cut in zip(state_names, edges):
        codes = codes * bins + np.searchsorted(cut, data[name].to_numpy(), side='right')
    n_states = bins ** len(state_names)
    if n_states > 5000:
        fail('Demasiados estados: reduce variables de estado o intervalos.')
    actions = np.array([-1., 0., 1.])
    rng = np.random.default_rng(seed)
    q = np.zeros((n_states, 3))

    def reward(t, action, previous):
        return actions[action] * returns[t + 1] - cost * abs(actions[action] - actions[previous])

    def best(state):
        # Empate (p. ej. estado sin visitas, Q = 0): quedarse en efectivo, no tomar corto por el orden de las acciones.
        values = q[state]
        return 1 if np.allclose(values, values.max()) else int(np.argmax(values))

    def pick(state, epsilon):
        return int(rng.integers(3)) if rng.random() < epsilon else best(state)

    learning = []
    for episode in range(episodes):
        epsilon = max(eps_end, 1 - episode / max(1, episodes * .8))
        previous, total = 1, 0.
        action = pick(codes[0], epsilon)
        for t in range(n_train - 1):
            r = reward(t, action, previous)
            total += r
            following = pick(codes[t + 1], epsilon)
            target = q[codes[t + 1]].max() if method == 'q_learning' else q[codes[t + 1], following]
            q[codes[t], action] += alpha * (r + gamma * target - q[codes[t], action])
            previous, action = action, following
        learning.append(total)

    def run(start, stop, policy):
        previous, path = 1, []
        for t in range(start, stop):
            action = policy(t)
            path.append(reward(t, action, previous))
            previous = action
        return np.array(path)

    greedy = lambda t: best(codes[t])
    agent_test = run(n_train, n, greedy)
    agent_train = run(0, n_train, greedy)
    hold_test = returns[n_train + 1:n + 1]
    equity_agent, equity_hold = np.cumprod(1 + agent_test), np.cumprod(1 + hold_test)

    def stats(path):
        total = float(np.prod(1 + path) - 1)
        sd = float(np.std(path, ddof=1)) if len(path) > 1 else 0.
        return [total * 100, float(np.mean(path) / sd * np.sqrt(per_year)) if sd > 0 else None, max_drawdown(np.cumprod(1 + path))]

    positions = np.array([actions[greedy(t)] for t in range(n_train, n)])
    labels = ['corto', 'efectivo', 'largo']
    policy_rows = []
    for s in range(n_states):
        parts, rest = [], s
        for name in reversed(state_names):
            parts.append(f'{name}: tramo {rest % bins + 1}/{bins}')
            rest //= bins
        visits = int(np.sum(codes[:n_train] == s))
        policy_rows.append([' · '.join(reversed(parts)), visits, *[float(v) for v in q[s]], labels[best(s)] if visits else 'efectivo (sin visitas)'])
    result = {'kind': 'analysis',
              'interpretation': (f'Agente {method.replace("_", "-")} tabular con {n_states} estados (cuantiles de {", ".join(state_names)} en {bins} tramos) '
                                 f'y acciones corto/efectivo/largo; costo {cost * 10000:.1f} pb por unidad de cambio de posición. '
                                 f'Entrenado en las primeras {n_train} transiciones y evaluado fuera de muestra con la política codiciosa.'),
              'metrics': [{'label': 'retorno_agente_prueba_%', 'value': stats(agent_test)[0]}, {'label': 'retorno_comprar_mantener_%', 'value': stats(hold_test)[0]},
                          {'label': 'sharpe_agente', 'value': stats(agent_test)[1]}, {'label': 'sharpe_comprar_mantener', 'value': stats(hold_test)[1]},
                          {'label': 'retorno_agente_entrenamiento_%', 'value': stats(agent_train)[0]}, {'label': 'cambios_de_posicion_prueba', 'value': int(np.sum(np.abs(np.diff(np.r_[1., positions])) > 0))},
                          {'label': 'tiempo_largo_%', 'value': float(np.mean(positions > 0) * 100)}, {'label': 'tiempo_corto_%', 'value': float(np.mean(positions < 0) * 100)}],
              'tables': [{'title': 'Prueba fuera de muestra', 'columns': ['Estrategia', 'Rendimiento total (%)', 'Sharpe anualizado', 'Caída máxima (%)'],
                          'rows': [['Agente RL', *stats(agent_test)], ['Comprar y mantener', *stats(hold_test)], ['Efectivo', 0., None, 0.]]},
                         {'title': 'Política aprendida (valores Q)', 'columns': ['Estado', 'Visitas en entrenamiento', 'Q corto', 'Q efectivo', 'Q largo', 'Acción'], 'rows': policy_rows[:200]}],
              'series': [{'label': 'Capital del agente (prueba)', 'points': [[i, float(v)] for i, v in enumerate(equity_agent)][:2000]},
                         {'label': 'Capital comprar y mantener (prueba)', 'points': [[i, float(v)] for i, v in enumerate(equity_hold)][:2000]},
                         {'label': 'Recompensa por episodio', 'points': [[i + 1, float(v)] for i, v in enumerate(learning)][-500:]}],
              'limitations': ['Política entrenada con datos pasados: no garantiza rendimientos futuros. Uso educativo, no asesoría financiera.',
                              'Estados discretizados con cuantiles del entrenamiento; con muchos estados poco visitados la política es ruidosa.'],
              'warnings': []}
    if int(np.sum([row[1] == 0 for row in policy_rows])):
        result['warnings'].append('Hay estados sin visitas en el entrenamiento: si aparecen en la prueba, el agente se queda en efectivo.')
    signal = pd.DataFrame({'posicion': positions, 'retorno_agente': agent_test, 'capital_agente': equity_agent}, index=data.index[n_train:n])
    output = frame.loc[signal.index].copy().join(signal)
    return result, {'result': result, 'data': output}


def run_deep_tool(kind, inputs, params):
    if kind == 'nn_input':
        result, spec = nn_input(params)
        return result, {'network': spec, 'result': result}
    if kind == 'nn_layer':
        result, spec = nn_layer(inputs, params)
        return result, {'network': spec, 'result': result}
    if kind == 'nn_output':
        result, spec = nn_output(inputs, params)
        return result, {'network': spec, 'result': result}
    if kind == 'nn_train':
        return nn_train(inputs, params)
    return rl_agent(inputs, params)
