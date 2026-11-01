# Plan por versiones

Fecha: 2026-11-01. No se asignan fechas de entrega sin estimación y validación del equipo.

| Fase | Versión objetivo | Entregable | Condición de cierre |
|---|---|---|---|
| P0 | 0.1.0 | Arquitectura, inventario bibliográfico, cobertura y automatización Git | Documentos verificables y primer push |
| P1 | 0.2.0 | Tauri/React/Python, contratos, guardar/cargar, CSV, simulación, World Bank, descriptivos y gráficos C01-C04 | Flujo local completo y ejemplo offline; locks y builds por plataforma |
| P2 | 0.3.0 | Probabilidad, muestreo, inferencia, OLS y diagnósticos C05-C11 | Resultados contrastados, lecciones y pruebas numéricas |
| P3 | 0.4.0 | Categóricas, formas funcionales y series C12-C15 | Forecast temporal reproducible y validación sin fuga |
| P4 | 0.5.0 | Cointegración, volatilidad, robustez, IV/GMM y selección C16-C19/C21-C22 | Validación científica; multivariado condicionado a motor validado |
| P5 | 0.6.0 | PCA/factores, HMM, clustering, redes y Monte Carlo C20/C24-C27 | Baselines, métricas y lecciones verificadas |
| P6 | 0.7.0 | SEM y estrategias C23/C28 | Supuestos, identificación y backtests reproducibles |
| Estabilización | 1.0.0 | Cobertura revisada, accesibilidad, migraciones, instaladores y firma | Todas las filas aceptadas, pruebas en OS destino y sin dependencias externas de usuario |

## Primer flujo de aplicación

Datos sintéticos o consulta World Bank → revisar tipos/unidades → limpieza explícita → OLS simple → diagnóstico → tabla/gráfico → guardar proyecto y manifiesto → reabrir y reproducir. Usar niveles positivos cuando una transformación logarítmica lo requiera; evitar el ejemplo de log del crecimiento del PIB sin validar dominio.

## Riesgos y decisiones abiertas

- Dependencias científicas y PyInstaller deben disponer de binarios para cada target; Python 3.15 observado no es el runtime elegido para distribuir.
- GARCH multivariado, SEM e IV/GMM necesitan selección y verificación de bibliotecas específicas.
- Las APIs externas pueden revisar datos o fallar; usar snapshots y fixtures offline.
- Firma/notarización y actualizaciones requieren infraestructura y credenciales específicas.
- La revisión inicial es por esquemas y objetivos. Antes de cerrar cada módulo se auditan secciones y ejercicios, sin reproducir contenido protegido.
