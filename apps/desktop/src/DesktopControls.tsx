import {useState} from 'react';
import {RefreshCw,Power,Download,RotateCcw,X} from 'lucide-react';
export type UpdateInfo={current:string;latest:string|null;available:boolean;message?:string;url?:string};
declare global {interface Window {quantlabsDesktop?:{request:(value:unknown)=>Promise<any>;action:(action:'reload'|'restart'|'quit')=>Promise<void>;checkUpdates:()=>Promise<UpdateInfo>;openReleases:()=>Promise<void>}}}
export default function DesktopControls(){
  const [message,setMessage]=useState('');const [checking,setChecking]=useState(false);
  const native=window.quantlabsDesktop;
  async function check(){setChecking(true);try{
    if(!native){setMessage('Estás en el navegador. Ejecuta npm run desktop para abrir Electron. Las versiones publicadas se consultan en GitHub Releases.');return;}
    const info=await native.checkUpdates();setMessage(info.message??(info.available?`Disponible ${info.latest}; instalada ${info.current}. Descarga la versión desde GitHub Releases.`:`Versión instalada ${info.current}. No hay una versión publicada más reciente.`));
  }catch(reason){setMessage(reason instanceof Error?reason.message:String(reason));}finally{setChecking(false);}}
  return <><div className="desktop-controls"><button aria-label="Recargar interfaz" title="Recargar interfaz · conserva el proyecto en esta sesión" onClick={()=>native?void native.action('reload'):window.location.reload()}><RefreshCw size={14}/><span>Recargar</span></button><button aria-label="Buscar actualizaciones" title="Buscar actualizaciones" disabled={checking} onClick={()=>void check()}><Download size={14}/><span>{checking?'Consultando…':'Actualizaciones'}</span></button>{native&&<><button aria-label="Reiniciar aplicación" title="Reiniciar aplicación" onClick={()=>void native.action('restart')}><RotateCcw size={14}/></button><button className="quit-button" aria-label="Salir por completo" title="Cerrar ventanas y procesos de Python" onClick={()=>void native.action('quit')}><Power size={14}/></button></>}</div>{message&&<div className="desktop-notice" role="status"><p>{message}</p><a href="https://github.com/rmrodriguezgit/Quantlabs-Econometrics/releases" target="_blank" rel="noreferrer" onClick={native?event=>{event.preventDefault();void native.openReleases();}:undefined}>Ver versiones publicadas</a><button aria-label="Cerrar aviso de actualización" onClick={()=>setMessage('')}><X size={14}/></button></div>}</>;
}
