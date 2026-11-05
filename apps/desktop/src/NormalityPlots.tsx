import HistogramPlot from './HistogramPlot';
import {axisScale,useAxis} from './axisFormat';
type QQ={points:[number,number][];mean:number;std:number;n:number;shown:number};
type Diagnostic={column:string;histogram:Parameters<typeof HistogramPlot>[0]['data'];qq:QQ};
function QQPlot({data,column}:{data:QQ;column:string}){
 const xs=data.points.map(point=>point[0]),ys=data.points.map(point=>point[1]),xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys,data.mean+data.std*xmin),ymax=Math.max(...ys,data.mean+data.std*xmax);
 const sy=axisScale([ymin,ymax],useAxis().y,v=>v.toPrecision(3));
 const x=(v:number)=>75+(v-xmin)/(xmax-xmin||1)*490,y=(v:number)=>220-(v-ymin)/(ymax-ymin||1)*175;
 return <section className="normality-qq"><h3>Q–Q normal · {column}</h3><svg viewBox="0 0 620 285" role="img" aria-label={`Q–Q normal de ${column}. Compara cuantiles observados y teóricos; alejarse de la recta sugiere desviaciones de normalidad.`}><line x1="75" x2="565" y1="220" y2="220" stroke="#52677b"/><line x1="75" x2="75" y1="45" y2="220" stroke="#52677b"/><line x1={x(xmin)} y1={y(data.mean+data.std*xmin)} x2={x(xmax)} y2={y(data.mean+data.std*xmax)} stroke="#ffce6d" strokeWidth="2"/>{data.points.map(([a,b],i)=><circle key={i} cx={x(a)} cy={y(b)} r="2.5" fill="#75b9ff"><title>{a.toPrecision(4)} → {b.toPrecision(5)}</title></circle>)}{[xmin,0,xmax].map((v,i)=><text key={i} x={x(v)} y="240" textAnchor="middle">{v.toFixed(2)}</text>)}<text x="65" y="52" textAnchor="end">{sy.tick(ymax)}</text><text x="65" y="220" textAnchor="end">{sy.tick(ymin)}</text><text x="320" y="269" textAnchor="middle">Cuantiles teóricos N(0,1)</text><text transform="translate(17,135) rotate(-90)" textAnchor="middle">{sy.label('Valores ordenados')}</text></svg><p>Recta de referencia: media + desviación muestral × cuantil normal. Se muestran {data.shown} de {data.n} cuantiles; las pruebas usan toda la muestra observada.</p></section>;
}
export default function NormalityPlots({data}:{data:Diagnostic[]}){return <div className="normality-plots">{data.map(item=><section key={item.column}><HistogramPlot data={item.histogram}/><QQPlot column={item.column} data={item.qq}/></section>)}</div>;}
