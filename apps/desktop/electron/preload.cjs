const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('quantlabsDesktop',Object.freeze({
  request:request=>ipcRenderer.invoke('engine:request',request),
  action:action=>ipcRenderer.invoke('desktop:action',action),
  checkUpdates:()=>ipcRenderer.invoke('desktop:updates'),
  openReleases:()=>ipcRenderer.invoke('desktop:releases'),
}));
