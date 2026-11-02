const {app,BrowserWindow,ipcMain,Menu,dialog,protocol,net,shell}=require('electron');
const {resolve,join,sep}=require('node:path');
const {pathToFileURL}=require('node:url');
const {createEngine,releaseInfo}=require('./runtime.cjs');
const root=resolve(__dirname,'../../..');
const engine=createEngine(root);
const dev=process.argv.includes('--dev');
const origin=dev?'http://127.0.0.1:1420':'quantlabs://studio';
let win,quitting=false,restarting=false;
app.setName('Quantlabs Econometrics');
protocol.registerSchemesAsPrivileged([{scheme:'quantlabs',privileges:{standard:true,secure:true,supportFetchAPI:true}}]);
if(!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance',()=>{if(win){if(win.isMinimized())win.restore();win.focus();}});
  const trusted=event=>{if(!win || event.sender!==win.webContents || event.senderFrame!==win.webContents.mainFrame || !event.senderFrame.url.startsWith(origin+'/'))throw new Error('Origen IPC no permitido.');};
  ipcMain.handle('engine:request',(event,value)=>{trusted(event);return engine.request(value);});
  ipcMain.handle('desktop:action',async(event,action)=>{
    trusted(event);
    if(action==='reload'){win.webContents.reload();return;}
    if(action==='restart'){restarting=true;app.quit();return;}
    if(action==='quit'){app.quit();return;}
    throw new Error('Acción desconocida.');
  });
  ipcMain.handle('desktop:updates',async event=>{
    trusted(event);
    const current=require('../package.json').version;
    const response=await net.fetch('https://api.github.com/repos/rmrodriguezgit/Quantlabs-Econometrics/releases/latest',{headers:{Accept:'application/vnd.github+json'},signal:AbortSignal.timeout(10000)});
    if(response.status===404)return {current,latest:null,available:false,message:'Todavía no hay versiones empaquetadas publicadas. Usa git pull --ff-only y npm ci para actualizar este checkout.'};
    if(!response.ok)throw new Error('No se pudieron consultar las versiones publicadas.');
    return releaseInfo(await response.json(),current);
  });
  ipcMain.handle('desktop:releases',event=>{trusted(event);return shell.openExternal('https://github.com/rmrodriguezgit/Quantlabs-Econometrics/releases');});
  app.whenReady().then(()=>{
    protocol.handle('quantlabs',request=>{
      const url=new URL(request.url);
      const dist=resolve(__dirname,'../dist');
      const path=resolve(dist,'.'+decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname));
      if(url.host!=='studio' || !path.startsWith(dist+sep))return new Response('No permitido',{status:403});
      return net.fetch(pathToFileURL(path).href);
    });
    win=new BrowserWindow({width:1500,height:980,minWidth:850,minHeight:640,title:'Quantlabs · Econometrics',backgroundColor:'#0d1118',webPreferences:{preload:join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
    if(!dev)win.webContents.session.webRequest.onHeadersReceived((details,callback)=>callback({responseHeaders:{...details.responseHeaders,'Content-Security-Policy':["default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'"]}}));
    win.webContents.setWindowOpenHandler(()=>({action:'deny'}));
    win.webContents.on('will-navigate',(event,url)=>{if(!url.startsWith(origin+'/'))event.preventDefault();});
    win.webContents.session.setPermissionRequestHandler((_contents,_permission,callback)=>callback(false));
    win.webContents.on('will-prevent-unload',event=>{
      const choice=dialog.showMessageBoxSync(win,{type:'question',buttons:['Conservar cambios','Descartar y continuar'],defaultId:0,cancelId:0,message:'Hay cambios sin guardar. ¿Quieres descartarlos?'});
      if(choice===1)event.preventDefault();else restarting=false;
    });
    Menu.setApplicationMenu(Menu.buildFromTemplate([
      {label:'Quantlabs',submenu:[{label:'Recargar interfaz',accelerator:'CmdOrCtrl+R',click:()=>win.webContents.reload()},{label:'Reiniciar aplicación',click:()=>{restarting=true;app.quit();}},{type:'separator'},{label:'Salir por completo',accelerator:'CmdOrCtrl+Q',click:()=>app.quit()}]},
      {role:'editMenu'},{label:'Vista',submenu:[{role:'toggleDevTools'},{role:'resetZoom'},{role:'zoomIn'},{role:'zoomOut'},{role:'togglefullscreen'}]},
    ]));
    void win.loadURL(origin+'/');
  });
  app.on('window-all-closed',()=>app.quit());
  app.on('will-quit',event=>{
    if(quitting)return;
    event.preventDefault();quitting=true;
    void engine.stop().finally(()=>{if(restarting)app.relaunch();app.exit(0);});
  });
}
