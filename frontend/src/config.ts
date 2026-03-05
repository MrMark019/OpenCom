// 检测是否在 Electron 环境
declare global {
  interface Window {
    electronAPI?: {
      getBackendPort: () => Promise<number>;
      onBackendReady: (callback: (port: number) => void) => void;
    };
    isElectron?: boolean;
  }
}

export const isElectron = (): boolean => {
  return window.isElectron === true;
};

export const getApiBase = async (): Promise<string> => {
  if (isElectron() && window.electronAPI) {
    const port = await window.electronAPI.getBackendPort();
    return `http://127.0.0.1:${port}/api`;
  }
  return 'http://localhost:8000/api';
};

export const getWsUrl = async (): Promise<string> => {
  if (isElectron() && window.electronAPI) {
    const port = await window.electronAPI.getBackendPort();
    return `ws://127.0.0.1:${port}/api/ws`;
  }
  return 'ws://localhost:8000/api/ws';
};
