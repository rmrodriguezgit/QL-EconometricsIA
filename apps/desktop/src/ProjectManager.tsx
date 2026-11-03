import normalityLesson from '../../../examples/normalidad-interes-consumo-usa.json';
import { useEffect, useRef, useState } from 'react';
import { BookOpen, Braces, Check, Copy, Download, FileJson, FolderOpen, LoaderCircle, Play, Plus, Save, Search, ShieldCheck, Trash2, Undo2, Upload, X } from 'lucide-react';
import { download, parseProject, rpc, version, type Project } from './model';

export type SavedProject = { id: string; title: string; revision: string; created_at: string; updated_at: string; project: Project };
type FileItem = Omit<SavedProject, 'project'>;
type Example = { id: string; title: string; topics: string; references: string[]; phase: string; objective: string; question: string; scope: string; steps?: number; tools?: string[] };
const normalityExample:Example={id:'N01',title:'Normalidad · interés y consumo USA',topics:'Normalidad, media, varianza, faltantes, unión temporal y residuos OLS',references:normalityLesson.lesson.references,phase:'Complementario',objective:normalityLesson.lesson.objective,question:'¿Cómo cambia la distribución al imputar y por qué no exige OLS variables normales?',scope:'Ejercicio guiado con datos anuales externos; no acredita supuestos causales ni completa C11.',steps:normalityLesson.nodes.length,tools:[...new Set(normalityLesson.nodes.map(node=>node.type))]};
type AuditCheck = { id: string; title: string; status: string; detail: string };
const normalize = (text: string) => text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();

export default function ProjectManager({ project, active, onOpen, onRun, onDeleted, onClose }: { project: Project; active: SavedProject | null; onOpen: (project: Project, file?: SavedProject) => void; onRun: (project: Project, file?: SavedProject) => void; onDeleted: (id: string) => void; onClose: () => void }) {
  const [view, setView] = useState<'examples' | 'files' | 'trash' | 'audit'>('examples');
  const [examples, setExamples] = useState<Example[]>([]);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [checks, setChecks] = useState<AuditCheck[]>([]);
  const [query, setQuery] = useState('');
  const [raw, setRaw] = useState(JSON.stringify(project, null, 2));
  const [base, setBase] = useState(JSON.stringify(project, null, 2));
  const [loaded, setLoaded] = useState<SavedProject | null>(active);
  const [example, setExample] = useState<Example | null>(null);
  const [pending, setPending] = useState(false);
  const [status, setStatus] = useState('El JSON del canvas está listo para editar.');
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const dialog = useRef<HTMLDialogElement>(null);
  const upload = useRef<HTMLInputElement>(null);
  const dirty = raw !== base;
  const canReplace = () => !dirty || window.confirm('Hay cambios de JSON sin guardar. ¿Quieres descartarlos y continuar?');
  const close = () => { if (!pending && canReplace()) onClose(); };
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);
  useEffect(() => { const d = dialog.current; d?.showModal(); return () => d?.close(); }, []);
  useEffect(() => {
    let live = true;
    setError('');
    const request = view === 'examples' ? rpc<{items: Example[]}>('examples.list') : view === 'audit' ? rpc<{checks: AuditCheck[]}>('system.audit') : rpc<{items: FileItem[]; unreadable: string[]}>('projects.list', { trash: view === 'trash' });
    request.then(result => {
      if (!live) return;
      if ('checks' in result) setChecks(result.checks);
      else if (view === 'examples') setExamples([...(result.items as Example[]),normalityExample]);
      else { setFiles(result.items as FileItem[]); if ('unreadable' in result && result.unreadable.length) setError(`${result.unreadable.length} archivos no se pudieron leer. Se conservaron sin modificar.`); }
    }).catch(reason => { if (live) setError(String(reason.message ?? reason)); });
    return () => { live = false; };
  }, [view, refresh]);
  async function act(action: () => Promise<void>) {
    if (pending) return;
    setPending(true); setError('');
    try { await action(); } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo completar la operación.'); }
    finally { setPending(false); }
  }
  function replace(next: Project, file: SavedProject | null, lesson: Example | null) {
    const text = JSON.stringify(next, null, 2); setRaw(text); setBase(text); setLoaded(file); setExample(lesson);
  }
  async function openExample(item: Example) {
    if (!canReplace()) return;
    await act(async () => { const result = item.id==='N01'?{project:parseProject(JSON.stringify(normalityLesson)),example:normalityExample}:await rpc<{ project: Project; example: Example }>('examples.read', { id: item.id }); replace(result.project, null, result.example); setStatus(`${item.id}: ejemplo cargado en el editor. Puedes ejecutarlo o guardarlo como proyecto propio.`); });
  }
  async function openFile(item: FileItem) {
    if (!canReplace()) return;
    await act(async () => { const result = await rpc<SavedProject>('projects.read', { id: item.id }); replace(result.project, result, null); setStatus(`Abierto: ${item.title}.`); });
  }
  async function save(copy = false) {
    await act(async () => {
      const next = { ...parseProject(raw), app_version: version };
      const saved = await rpc<SavedProject>('projects.save', { project: next, ...(loaded && !copy ? { id: loaded.id, expected_revision: loaded.revision } : {}) });
      replace(saved.project, saved, example); onOpen(saved.project, saved); setView('files'); setRefresh(n => n + 1); setStatus(`Guardado en Mis proyectos: ${saved.title}.`);
    });
  }
  async function validate() {
    await act(async () => { const next = parseProject(raw); await rpc('project.validate', { project: next, draft: true }); setStatus('JSON y estructura válidos. Se permite guardar nodos todavía sin conectar. Ejecutar comprueba también las conexiones.'); });
  }
  async function apply(execute = false) {
    await act(async () => {
      const next = parseProject(raw); await rpc('project.validate', { project: next, draft: !execute });
      const file = loaded ?? undefined;
      if (execute) onRun(next, file); else onOpen(next, file);
      onClose();
    });
  }
  const filteredExamples = examples.filter(item => normalize(`${item.id} ${item.title} ${item.topics} ${item.references.join(' ')}`).includes(normalize(query)));
  const filteredFiles = files.filter(item => normalize(item.title).includes(normalize(query)));
  return <dialog ref={dialog} className="manager-dialog" aria-labelledby="manager-title" onCancel={event => { event.preventDefault(); close(); }}>
    <header className="manager-header"><span className="manager-emblem"><FolderOpen size={22} /></span><div><span className="eyebrow">TU BIBLIOTECA LOCAL</span><h2 id="manager-title">Proyectos y ejemplos</h2></div><button className="icon-button" aria-label="Cerrar administrador" onClick={close} disabled={pending}><X size={20} /></button></header>
    <div className="manager-layout"><aside className="manager-sidebar"><nav>{([['examples', BookOpen, 'Ejemplos'], ['files', FolderOpen, 'Mis proyectos'], ['trash', Trash2, 'Papelera'], ['audit', ShieldCheck, 'Auditoría']] as const).map(([id, Icon, label]) => <button key={id} className={view === id ? 'active' : ''} disabled={pending} onClick={() => { setView(id); setQuery(''); }}><Icon size={15} />{label}{id === 'examples' && <span>{examples.length || 28}</span>}</button>)}</nav>
      {view !== 'audit' && <div className="manager-search"><Search size={14} /><input aria-label="Buscar archivos o ejemplos" placeholder="Tema, nombre o referencia…" value={query} onChange={event => setQuery(event.target.value)} /></div>}
      <div className="manager-list">{view === 'examples' ? filteredExamples.map(item => <button className={`example-entry ${example?.id === item.id ? 'selected' : ''}`} key={item.id} disabled={pending} onClick={() => void openExample(item)}><span>{item.id} · {item.phase}</span><strong>{item.title}</strong><small>{item.steps?`${item.steps} pasos · `:'Ejecutable · '}{item.references.join(' / ')}</small></button>) : view === 'audit' ? <p className="manager-sidebar-note">Comprobaciones reales del catálogo y almacenamiento. Los pendientes permanecen visibles.</p> : <>{filteredFiles.map(item => <div className="file-entry" key={item.id}><button disabled={pending || view === 'trash'} onClick={() => void openFile(item)}><FileJson size={16} /><span><strong>{item.title}</strong><small>{new Date(item.updated_at).toLocaleString('es-MX')}</small></span></button>{view === 'trash' ? <button aria-label={`Restaurar ${item.title}`} title="Restaurar" disabled={pending} onClick={() => void act(async () => { await rpc('projects.restore', { id: item.id, expected_revision: item.revision }); setRefresh(n => n + 1); setStatus('Proyecto restaurado. Está disponible en Mis proyectos.'); })}><Undo2 size={14} /></button> : <button aria-label={`Borrar ${item.title}`} title="Mover a la papelera" disabled={pending} onClick={() => void act(async () => { await rpc('projects.delete', { id: item.id, expected_revision: item.revision }); if (loaded?.id === item.id) setLoaded(null); onDeleted(item.id); setRefresh(n => n + 1); setStatus('Proyecto movido a la papelera. Se puede restaurar.'); })}><Trash2 size={14} /></button>}</div>)}{!filteredFiles.length && <p className="manager-sidebar-note">{view === 'trash' ? 'La papelera está vacía.' : 'Todavía no hay proyectos guardados. Guarda el JSON del editor para crear uno.'}</p>}</>}</div>
      <div className="manager-local-note">Los proyectos se guardan en este equipo. Borrar los mueve a la papelera; los ejemplos originales se conservan.</div>
    </aside><section className="manager-main">{view === 'audit' ? <div className="system-audit"><h3>Auditoría del sistema</h3><p>Estado comprobado por el motor, sin alterar tus proyectos.</p>{checks.map(check => <article key={check.id} className={`audit-check ${check.status}`}><span>{check.status === 'ok' ? '✓' : '○'}</span><div><h4>{check.title}</h4><p>{check.detail}</p><small>{check.status === 'ok' ? 'Verificado' : 'Pendiente'}</small></div></article>)}<button className="manager-secondary" onClick={() => setRefresh(n => n + 1)}>Volver a comprobar</button></div> : <>
      <div className="editor-heading"><div><Braces size={17} /><strong>Editor JSON</strong><span className={dirty ? 'modified' : ''}>{dirty ? 'Cambios sin guardar' : loaded ? 'Proyecto guardado' : 'Borrador'}</span></div><div><button className="icon-button" title="Nuevo proyecto vacío" aria-label="Nuevo proyecto vacío" disabled={pending} onClick={() => { if (canReplace()) { replace({ schema_version: '1.0.0', app_version: version, title: 'Nuevo proyecto', nodes: [], edges: [] }, null, null); setStatus('Borrador vacío creado. Puedes guardarlo o añadir nodos desde el canvas.'); } }}><Plus size={16} /></button><button className="icon-button" title="Importar JSON" aria-label="Importar JSON" disabled={pending} onClick={() => { if (canReplace()) upload.current?.click(); }}><Upload size={16} /></button><button className="icon-button" title="Exportar JSON" aria-label="Exportar JSON" disabled={pending} onClick={() => void act(async () => { const next = parseProject(raw); download('quantlabs-proyecto.json', next); setStatus('JSON exportado.'); })}><Download size={16} /></button></div></div>
      <input ref={upload} type="file" accept=".json,application/json" hidden onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; if (!file) return; void act(async () => { if (file.size > 3_000_000) throw new Error('El JSON supera 3 MB.'); const text = await file.text(); setRaw(text); setBase(text); setLoaded(null); setExample(null); setStatus('Archivo importado en el editor. Valida y guarda para incorporarlo a Mis proyectos.'); const next = parseProject(text); await rpc('project.validate', { project: next, draft: true }); }); }} />
      {example && <section className="example-context"><span>{example.id} · EXPERIMENTO REPRODUCIBLE</span><h3>{example.title}</h3><p>{example.objective}</p>{example.steps&&<p>{example.steps} pasos con {example.tools?.length} herramientas. Abre en el canvas para seguirlos y ejecutar cada salida.</p>}<details><summary>Temas, referencias y pregunta de trabajo</summary><p>{example.topics}</p><p>{example.question}</p><p>{example.scope}</p><small>Referencias: {example.references.join(', ')}</small></details></section>}
      <textarea className="json-editor" aria-label="JSON del proyecto" spellCheck={false} disabled={pending} value={raw} onChange={event => setRaw(event.target.value)} onKeyDown={event => { if ((event.ctrlKey || event.metaKey) && event.key === 's') { event.preventDefault(); void save(); } }} />
      <div className="manager-actions"><button className="manager-secondary" disabled={pending} onClick={() => void validate()}><Check size={14} />Validar</button><button className="manager-secondary" disabled={pending} onClick={() => void apply()}><FolderOpen size={14} />Abrir en canvas</button><button className="manager-secondary" disabled={pending} onClick={() => void save(true)}><Copy size={14} />Guardar copia</button><button className="manager-secondary" disabled={pending} onClick={() => void save()}><Save size={14} />Guardar</button><button className="manager-primary" disabled={pending} onClick={() => void apply(true)}>{pending ? <LoaderCircle className="spin" size={14} /> : <Play size={14} />}Ejecutar</button></div>
    </>}
      <div className={`manager-status ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}>{pending ? 'Procesando…' : error || status}</div>
    </section></div>
  </dialog>;
}
