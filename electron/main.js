const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const findFreePort = require('find-free-port');
const fetch = require('node-fetch');
const fs = require('fs');

let mainWindow = null;
let backendProcess = null;
let backendPort = null;

// 日志文件
const logFile = path.join(app.getPath('userData'), 'app.log');
function log(msg) {
  const timestamp = new Date().toISOString();
  const logMsg = `[${timestamp}] ${msg}\n`;
  console.log(msg);
  try {
    fs.appendFileSync(logFile, logMsg);
  } catch (e) {}
}

const isDev = () => !app.isPackaged;

function getBackendPath() {
  if (isDev()) {
    return process.platform === 'win32' ? 'python' : 'python3';
  } else {
    const platform = process.platform;
    let backendName = 'serial-backend';
    if (platform === 'win32') {
      backendName += '.exe';
    }
    return path.join(process.resourcesPath, 'backend', backendName);
  }
}

function getBackendArgs(port) {
  if (isDev()) {
    return ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', port.toString()];
  } else {
    return [port.toString()];
  }
}

async function waitForBackend(port, maxRetries = 30) {
  log(`等待后端启动在端口 ${port}...`);
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/health`, { timeout: 1000 });
      if (response.ok) {
        log('后端已就绪！');
        return true;
      }
    } catch (error) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  throw new Error('后端启动超时');
}

async function startBackend() {
  try {
    const [port] = await findFreePort(8000, 8100);
    backendPort = port;
    log(`启动后端在端口 ${port}...`);

    const backendPath = getBackendPath();
    const args = getBackendArgs(port);
    log(`后端路径: ${backendPath}`);
    log(`启动参数: ${args.join(' ')}`);

    backendProcess = spawn(backendPath, args, {
      cwd: isDev() ? process.cwd() : process.resourcesPath,
      env: { ...process.env }
    });

    backendProcess.stdout.on('data', (data) => {
      log(`[Backend] ${data.toString().trim()}`);
    });

    backendProcess.stderr.on('data', (data) => {
      log(`[Backend Error] ${data.toString().trim()}`);
    });

    backendProcess.on('close', (code) => {
      log(`后端进程退出，代码: ${code}`);
      backendProcess = null;
    });

    await waitForBackend(port);
    return port;
  } catch (error) {
    log('启动后端失败: ' + error.message);
    throw error;
  }
}

function stopBackend() {
  if (backendProcess) {
    log('停止后端进程...');
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  log('创建主窗口...');
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  const indexPath = path.join(__dirname, 'frontend', 'dist', 'index.html');
  log(`加载前端: ${indexPath}`);

  mainWindow.loadFile(indexPath).then(() => {
    log('前端加载成功');
    mainWindow.show();
  }).catch(err => {
    log('前端加载失败: ' + err.message);
  });

  if (isDev()) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

ipcMain.handle('get-backend-port', () => {
  return backendPort;
});

app.on('ready', async () => {
  log('应用启动...');
  log(`日志文件: ${logFile}`);
  log(`资源路径: ${process.resourcesPath}`);
  log(`是否打包: ${!isDev()}`);

  try {
    await startBackend();
    createWindow();

    if (mainWindow) {
      mainWindow.webContents.send('backend-ready', backendPort);
    }
  } catch (error) {
    log('应用启动失败: ' + error.message);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('quit', () => {
  stopBackend();
});

process.on('uncaughtException', (error) => {
  log('未捕获的异常: ' + error.message);
});
