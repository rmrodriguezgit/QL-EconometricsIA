import { BookOpen, Check, ChevronLeft, ChevronRight, Maximize2, Play } from 'lucide-react';
import type { Lesson, Run } from './model';
export default function LessonGuide({lesson,index,run,busy,onChoose,onExecute,onOverview}:{lesson:Lesson;index:number;run:Run|null;busy:boolean;onChoose:(index:number)=>void;onExecute:(id:string)=>void;onOverview:()=>void}) {
  const step=lesson.steps[index];
  if(!step)return null;
  return <section className="lesson-guide" aria-label="Guía paso a paso"><div className="lesson-guide-heading"><span><BookOpen size={14}/>{lesson.module} · Paso {index+1} de {lesson.steps.length}</span><button onClick={onOverview}><Maximize2 size={12}/>Ver flujo completo</button></div>
    <ol className="lesson-progress">{lesson.steps.map((item,i)=><li key={item.node_id}><button disabled={busy} aria-label={`Paso ${i+1}: ${item.title}`} aria-current={i===index?'step':undefined} className={i===index?'active':run?.nodes[item.node_id]?.status==='succeeded'?'done':''} onClick={()=>onChoose(i)} title={item.title}>{run?.nodes[item.node_id]?.status==='succeeded'?<Check size={11}/>:i+1}</button></li>)}</ol>
    <h3>{step.title}</h3><p>{step.instruction}</p><div className="step-expected"><strong>Qué debes observar</strong><p>{step.expected}</p></div><details><summary>Pregunta y herramientas pendientes</summary><p>{step.question}</p><p>{lesson.missing_tools.join(' · ')}</p><small>Referencias: {lesson.references.join(', ')}</small></details>
    <div className="lesson-guide-actions"><button disabled={busy||index===0} onClick={()=>onChoose(index-1)}><ChevronLeft size={13}/>Anterior</button><button className="execute-step" disabled={busy} onClick={()=>onExecute(step.node_id)}><Play size={12}/>{busy?'Calculando…':'Ejecutar hasta este paso'}</button><button disabled={busy||index===lesson.steps.length-1} onClick={()=>onChoose(index+1)}>Siguiente<ChevronRight size={13}/></button></div>
    <small className="step-recalculation">Cada paso recalcula sus dependencias. Inspecciona la salida antes de continuar.</small>
  </section>;
}
