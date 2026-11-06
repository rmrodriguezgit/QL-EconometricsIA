// Etiquetas del inspector para las capas de la red multicapa y el agente de refuerzo.
const LABELS: Record<string, Record<string, string>> = {
  nn_input: { features: 'Variables de entrada (separadas por coma)', standardize: 'Estandarización de entradas' },
  nn_layer: { layer_type: 'Tipo de capa', units: 'Neuronas', activation: 'Función de activación', rate: 'Tasa de dropout (solo capas dropout)' },
  nn_output: { y: 'Variable respuesta (y)', task: 'Tarea y activación de salida' },
  nn_train: { epochs: 'Épocas máximas', batch_size: 'Tamaño del mini-lote', learning_rate: 'Tasa de aprendizaje', optimizer: 'Optimizador', l2: 'Penalización L2', validation: 'Fracción final para validación', patience: 'Paciencia (parada temprana)', seed: 'Semilla aleatoria' },
  rl_agent: { returns: 'Columna de rendimientos', state: 'Variables de estado (separadas por coma)', unit: 'Unidad de los rendimientos', method: 'Algoritmo', bins: 'Tramos por variable de estado', episodes: 'Episodios de entrenamiento', alpha: 'Tasa de aprendizaje (α)', gamma: 'Factor de descuento (γ)', epsilon: 'Exploración final (ε)', cost_bps: 'Costo por cambio de posición (pb)', fraction: 'Fracción de entrenamiento', periods_per_year: 'Períodos por año (para Sharpe)', seed: 'Semilla aleatoria' },
};
export const deepLabel = (type: string, key: string): string | undefined => LABELS[type]?.[key];
