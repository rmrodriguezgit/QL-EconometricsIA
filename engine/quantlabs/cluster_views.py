"""Vistas del modelo k-means: datos para los gráficos de grupos, silueta, codo y perfil de centroides.

Todo se calcula con la misma tabla y la misma escala que usó el ajuste. Con más de dos variables los puntos se proyectan
en los dos primeros componentes principales de las variables estandarizadas (solo para dibujar; los grupos no cambian).
"""
import numpy as np

MAX_POINTS = 2500
MAX_SILHOUETTE = 2000


def _rows(rng, n, limit):
    return np.sort(rng.choice(n, limit, replace=False)) if n > limit else np.arange(n)


def kmeans_views(data, names, fit, seed):
    from sklearn.cluster import KMeans
    from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_samples
    X = data.to_numpy(dtype=float)
    labels = fit.labels_
    k = int(fit.n_clusters)
    n = len(X)
    rng = np.random.default_rng(seed)
    centers = fit.cluster_centers_

    # Plano de dibujo: variables originales con 2 columnas; PCA de las estandarizadas con más.
    if len(names) == 2:
        plane, cplane, axes, explained = X, centers, list(names), None
    else:
        mu, sd = X.mean(axis=0), X.std(axis=0, ddof=0)
        sd[sd == 0] = 1
        Z = (X - mu) / sd
        _, s, vt = np.linalg.svd(Z - Z.mean(axis=0), full_matrices=False)
        comps = vt[:2]
        # Signo estable: la mayor carga de cada componente es positiva.
        comps *= np.sign(comps[np.arange(2), np.abs(comps).argmax(axis=1)])[:, None]
        plane, cplane = Z @ comps.T, ((centers - mu) / sd) @ comps.T
        share = s ** 2 / np.sum(s ** 2)
        explained = [float(share[0]) * 100, float(share[1]) * 100]
        axes = [f'Componente 1 ({explained[0]:.1f} %)', f'Componente 2 ({explained[1]:.1f} %)']

    # Silueta por observación (muestra si la tabla es grande).
    idx = _rows(rng, n, MAX_SILHOUETTE)
    sil = silhouette_samples(X[idx], labels[idx]) if len(set(labels[idx])) > 1 else np.zeros(len(idx))
    groups = []
    for g in range(k):
        mask = labels == g
        inside = X[mask]
        sil_g = sil[labels[idx] == g]
        groups.append({'group': g, 'n': int(mask.sum()), 'share': float(mask.mean()) * 100,
                       'sse': float(np.sum((inside - centers[g]) ** 2)), 'silhouette': float(sil_g.mean()) if len(sil_g) else None,
                       'negative': int(np.sum(sil_g < 0)), 'values': sorted((float(v) for v in sil_g), reverse=True)})

    # Codo y silueta media para k = 2 … 8 (misma semilla; silueta en la misma muestra).
    curve = []
    for kk in range(2, min(8, n - 1) + 1):
        model = fit if kk == k else KMeans(n_clusters=kk, n_init=10, random_state=seed).fit(X)
        lab = model.labels_[idx]
        score = float(silhouette_samples(X[idx], lab).mean()) if len(set(lab)) > 1 else None
        curve.append({'k': kk, 'inertia': float(model.inertia_), 'silhouette': score})

    # Perfil: centroides en desviaciones estándar respecto de la media de cada variable.
    mean, std = X.mean(axis=0), X.std(axis=0, ddof=1)
    std[std == 0] = 1
    profile = [[float(v) for v in (centers[g] - mean) / std] for g in range(k)]

    pts = _rows(rng, n, MAX_POINTS)
    plot = {'features': list(names), 'axes': axes, 'explained': explained, 'k': k, 'n': n,
            'points': [[float(plane[i, 0]), float(plane[i, 1]), int(labels[i])] for i in pts],
            'centroids': [[float(c[0]), float(c[1])] for c in cplane],
            'centers': [[float(v) for v in c] for c in centers], 'profile': profile,
            'groups': groups, 'curve': curve, 'silhouette_mean': float(sil.mean()),
            'sampled_points': len(pts) < n, 'sampled_silhouette': len(idx) < n}
    metrics = {'silueta_media': float(sil.mean()),
               'calinski_harabasz': float(calinski_harabasz_score(X, labels)),
               'davies_bouldin': float(davies_bouldin_score(X, labels))}
    spread = X.std(axis=0, ddof=1)
    spread = spread[spread > 0]
    warnings = []
    if len(spread) > 1 and spread.max() / spread.min() > 10:
        warnings.append('Las variables tienen escalas muy distintas (desviaciones que difieren más de 10 veces): la distancia la dominan las de mayor escala. '
                        'Estandariza antes de agrupar.')
    best = max((c for c in curve if c['silhouette'] is not None), key=lambda c: c['silhouette'], default=None)
    if best and best['k'] != k:
        warnings.append(f'Con estos datos la silueta media es mayor con k = {best["k"]} ({best["silhouette"]:.3f}) que con k = {k} ({sil.mean():.3f}).')
    return plot, metrics, warnings
