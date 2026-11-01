import { useEffect, useRef } from 'react';
import { X, Sigma, CircleCheck } from 'lucide-react';
import type { ProjectNode, NodeResult } from './model';

function number(value: number) {
  return new Intl.NumberFormat('es-MX', { maximumFractionDigits: 6 }).format(value);
}

export default function ModelEquation({ node, result, onClose }: { node?: ProjectNode; result?: NodeResult; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const x = String(node?.parameters.x ?? 'x');
  const y = String(node?.parameters.y ?? 'y');
  const model = result?.status === 'succeeded' ? result.result : undefined;
  const coefficients = model?.coefficients as { term: string; estimate: number }[] | undefined;
  const intercept = coefficients?.find(c => c.term === 'const')?.estimate;
  const slope = coefficients?.find(c => c.term === x)?.estimate;
  const estimated = intercept !== undefined && slope !== undefined;
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => { dialog?.close(); };
  }, []);
  return <dialog ref={ref} className="equation-dialog" aria-labelledby="equation-title" onCancel={onClose} onClick={event => { if (event.target === ref.current) onClose(); }}>
    <div className="equation-window">
      <header className="equation-header"><span className="equation-symbol"><Sigma size={22} /></span><div><span className="eyebrow">REGRESIÓN LINEAL SIMPLE</span><h2 id="equation-title">Ecuación del modelo</h2></div><button type="button" aria-label="Cerrar ecuación" className="icon-button" onClick={onClose} autoFocus><X size={19} /></button></header>
      <section className="equation-section"><h3>Modelo poblacional</h3><div className="equation-math" aria-label={`${y} sub i igual beta cero más beta uno por ${x} sub i más error sub i`}><span>{y}<sub>i</sub></span><span>=</span><span>β<sub>0</sub></span><span>+</span><span>β<sub>1</sub> · {x}<sub>i</sub></span><span>+</span><span>ε<sub>i</sub></span></div><p>El modelo relaciona la variable respuesta con el regresor y un término de error no observado.</p></section>
      <section className="equation-estimate"><div className="equation-estimate-heading"><h3>Recta estimada por OLS</h3>{estimated && <span><CircleCheck size={12} />Calculada con tu muestra</span>}</div>{estimated ? <><div className="equation-fitted" aria-label={`${y} estimado igual ${intercept} ${slope < 0 ? 'menos' : 'más'} ${Math.abs(slope)} por ${x}`}><span>ŷ<span className="equation-variable">({y})</span></span><span>=</span><strong>{number(intercept)}</strong><span>{slope < 0 ? '−' : '+'}</span><strong>{number(Math.abs(slope))}</strong><span>· {x}</span></div><p>{number(Number(model?.n))} observaciones · R² = {number(Number(model?.r_squared))} · Covarianza {String(model?.covariance)}</p></> : <><div className="equation-fitted"><span>ŷ</span><span>=</span><span>β̂<sub>0</sub> + β̂<sub>1</sub> · {x}</span></div><p>Ejecuta el flujo para sustituir los parámetros por los coeficientes estimados.</p></>}</section>
      <dl className="equation-definitions"><div><dt>{y}</dt><dd>Variable respuesta</dd></div><div><dt>{x}</dt><dd>Variable explicativa</dd></div><div><dt>β₀</dt><dd>Intercepto poblacional</dd></div><div><dt>β₁</dt><dd>Pendiente poblacional</dd></div><div><dt>εᵢ</dt><dd>Error no observado</dd></div><div><dt>ŷ</dt><dd>Valor ajustado de la respuesta</dd></div></dl>
      <footer className="equation-note">Los coeficientes estiman una asociación. Interpretarla como causal requiere supuestos adicionales. El error εᵢ pertenece al modelo poblacional; la recta ajustada muestra el valor predicho.</footer>
    </div>
  </dialog>;
}
