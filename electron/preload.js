/**
 * Electron 预加载脚本
 * 在渲染进程中暴露安全的 API
 */

const { contextBridge, ipcRenderer } = require('electron');

// 暴露给渲染进程的 API
contextBridge.exposeInMainWorld('electronAPI', {
  /**
   * 获取后端端口号
   */
  getBackendPort: () => ipcRenderer.invoke('get-backend-port'),
  
  /**
   * 监听后端就绪事件
   */
  onBackendReady: (callback) => {
    ipcRenderer.on('backend-ready', (event, port) => callback(port));
  }
});

// 标记为 Electron 环境
contextBridge.exposeInMainWorld('isElectron', true);
