"""Segundo cerebro de Quantlabs: convierte un enunciado en un blueprint verificable.

El cerebro nunca ejecuta código generado. Solo propone grafos compuestos por
herramientas registradas en ``packages/contracts/nodeCatalog.json``; el grafo
se valida con el mismo validador DAG del motor y, opcionalmente, se ejecuta para
reparar columnas antes de entregarlo. Las herramientas inexistentes se registran
como fichas pendientes (``brain.gaps``) para implementarlas con pruebas.
"""

BRAIN_VERSION = '1.0.0'
