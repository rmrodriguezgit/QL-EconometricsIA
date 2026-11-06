import { Component, type ErrorInfo, type ReactNode } from 'react';
import { CircleAlert, RotateCcw } from 'lucide-react';

type Props = { area: string; resetKey?: unknown; children: ReactNode; compact?: boolean };
type State = { error: Error | null };

/** Aísla un fallo de render: muestra un aviso con «Reintentar» en lugar de dejar toda la aplicación en negro. */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[Quantlabs] Fallo en ${this.props.area}:`, error, info.componentStack);
  }

  componentDidUpdate(previous: Props) {
    // Al cambiar de nodo seleccionado (u otra clave) se vuelve a intentar automáticamente.
    if (this.state.error && previous.resetKey !== this.props.resetKey) this.setState({ error: null });
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return <div role="alert" className="node-error" style={{ margin: this.props.compact ? '4px 0' : '12px 0' }}>
      <strong><CircleAlert size={13} /> No se pudo mostrar {this.props.area}</strong>
      <p>{error.message || String(error)}</p>
      <p className="subtle">El resto de la aplicación sigue funcionando; tu flujo no se ha modificado.</p>
      <button className="repair-button" type="button" onClick={() => this.setState({ error: null })}><RotateCcw size={12} />Reintentar</button>
    </div>;
  }
}
