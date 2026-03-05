# 关键配置文件示例

本文档包含实施 Electron 打包所需的所有关键配置文件示例。

---

## 1. PyInstaller 配置文件

**文件路径：** `backend.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - 用于打包 Python 后端
使用方法: pyinstaller backend.spec
"""

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
root_dir = Path('.').absolute()

a = Analysis(
    ['backend/main.py'],  # 入口文件
    pathex=[str(root_dir)],
    binaries=[],
    datas=[],
    hiddenimports=[
        # FastAPI 相关
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # pyserial 相关
        'serial.tools',
        'serial.tools.list_ports',
        'serial.tools.list_ports_windows',
        'serial.tools.list_ports_posix',
        'serial.tools.list_ports_osx',
        # 其他模块
        'click',
        'websockets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'PIL', 'tkinter', 'pytest', 'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='serial-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='serial-backend',
)
```

---

## 2. 后端入口文件修改

**文件路径：** `backend/electron_entry.py`

```python
"""
Electron 环境专用入口文件
支持命令行参数指定端口
"""

import sys
import uvicorn
from backend.main import app

if __name__ == "__main__":
    # 从命令行参数获取端口，默认 8000
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    # 启动服务器
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        access_log=False  # 减少日志输出
    )
```

---

## 3. Electron 主进程

**文件路径：** `electron/main.js`

```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const findFreePort = require('find-free-port');
const fetch = require('node-fetch');

let mainWindow = null;
let backendProcess = null;
let backendPort = null;

const isDev = !app.isPackaged;

function getBackendPath() {
  if (isDev) {
    return process.platform === 'win32' ? 'python' : 'python3';
  } else {
    const platform = process.platform;
    let backendName = 'serial-backend';
    if (platform === 'win32') backendName += '.exe';
    return path.join(process.resourcesPath, 'backend', backendName);
  }
}

function getBackendArgs(port) {
  if (isDev) {
    return ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', port.toString()];
  } else {
    return [port.toString()];
  }
}

async function waitForBackend(port, maxRetries = 30) {
  console.log(`等待后端启动在端口 ${port}...`);
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/health`, { timeout: 1000 });
      if (response.ok) {
        console.log('后端已就绪！');
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
    
    const backendPath = getBackendPath();
    const args = getBackendArgs(port);
    
    backendProcess = spawn(backendPath, args, {
      cwd: isDev ? process.cwd() : process.resourcesPath,
      env: { ...process.env }
    });
    
    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data.toString().trim()}`);
    });
    
    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data.toString().trim()}`);
    });
    
    backendProcess.on('close', (code) => {
      console.log(`后端进程退出，代码: ${code}`);
      backendProcess = null;
    });
    
    await waitForBackend(port);
    return port;
  } catch (error) {
    console.error('启动后端失败:', error);
    throw error;
  }
}

function stopBackend() {
  if (backendProcess) {
    console.log('停止后端进程...');
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  });
  
  const indexPath = path.join(__dirname, 'frontend', 'dist', 'index.html');
  mainWindow.loadFile(indexPath);
  
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

ipcMain.handle('get-backend-port', () => backendPort);

app.on('ready', async () => {
  try {
    await startBackend();
    createWindow();
    if (mainWindow) {
      mainWindow.webContents.send('backend-ready', backendPort);
    }
  } catch (error) {
    console.error('应用启动失败:', error);
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
```

---

## 4. Electron 预加载脚本

**文件路径：** `electron/preload.js`

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getBackendPort: () => ipcRenderer.invoke('get-backend-port'),
  onBackendReady: (callback) => {
    ipcRenderer.on('backend-ready', (event, port) => callback(port));
  }
});

contextBridge.exposeInMainWorld('isElectron', true);
```

---

## 5. Electron package.json

**文件路径：** `electron/package.json`

```json
{
  "name": "serial-debugger",
  "version": "0.1.0",
  "description": "XCOM V2.6 compatible serial debugger",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "build:win": "electron-builder --win",
    "build:mac": "electron-builder --mac",
    "build:linux": "electron-builder --linux"
  },
  "dependencies": {
    "find-free-port": "^2.0.0",
    "node-fetch": "^2.7.0"
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.0.0"
  },
  "build": {
    "appId": "com.opencom.serial-debugger",
    "productName": "Serial Debugger",
    "directories": {
      "output": "../release"
    },
    "files": [
      "**/*",
      "!node_modules",
      "frontend/dist/**/*",
      "backend/**/*"
    ],
    "extraResources": [
      {
        "from": "backend",
        "to": "backend",
        "filter": ["**/*"]
      }
    ],
    "win": {
      "target": ["nsis", "portable"],
      "icon": "assets/icon.ico"
    },
    "mac": {
      "target": ["dmg", "zip"],
      "icon": "assets/icon.icns",
      "category": "public.app-category.developer-tools"
    },
    "linux": {
      "target": ["AppImage", "deb"],
      "icon": "assets/icon.png",
      "category": "Development"
    }
  }
}
```

---

## 6. 前端配置适配

**文件路径：** `frontend/src/config.ts`（新建）

```typescript
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
```

**修改：** `frontend/src/App.tsx`（部分代码）

```typescript
import { getApiBase, getWsUrl } from './config';

function App() {
  const [apiBase, setApiBase] = useState('');
  const [wsUrl, setWsUrl] = useState('');

  useEffect(() => {
    const initConfig = async () => {
      setApiBase(await getApiBase());
      setWsUrl(await getWsUrl());
    };
    initConfig();
  }, []);

  // 使用 apiBase 和 wsUrl 替代硬编码的 URL
  // ...
}
```

---

## 7. 构建脚本

**文件路径：** `scripts/build_backend.py`

```python
#!/usr/bin/env python3
"""
构建 Python 后端可执行文件
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def main():
    print("🐍 开始构建 Python 后端...")
    
    # 确保在项目根目录
    root_dir = Path(__file__).parent.parent
    os.chdir(root_dir)
    
    # 检查 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("安装 PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 执行构建
    spec_file = root_dir / "backend.spec"
    
    if not spec_file.exists():
        print(f"错误: 找不到 {spec_file}")
        sys.exit(1)
    
    print(f"使用配置文件: {spec_file}")
    subprocess.check_call(["pyinstaller", str(spec_file), "--clean"])
    
    # 检查输出
    dist_dir = root_dir / "dist" / "serial-backend"
    if dist_dir.exists():
        print(f"✅ 构建成功！输出目录: {dist_dir}")
    else:
        print("❌ 构建失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**文件路径：** `scripts/build_all.js`

```javascript
#!/usr/bin/env node
/**
 * 完整构建脚本
 */

const { execSync } = require('child_process');
const fs = require('fs-extra');
const path = require('path');

const rootDir = path.join(__dirname, '..');

async function buildAll() {
  console.log('🔨 开始完整构建...\n');
  
  try {
    // 1. 构建前端
    console.log('📦 步骤 1/4: 构建前端...');
    execSync('npm run build', {
      cwd: path.join(rootDir, 'frontend'),
      stdio: 'inherit'
    });
    
    // 2. 打包 Python 后端
    console.log('\n🐍 步骤 2/4: 打包 Python 后端...');
    execSync('python scripts/build_backend.py', {
      cwd: rootDir,
      stdio: 'inherit'
    });
    
    // 3. 准备 Electron 资源
    console.log('\n📋 步骤 3/4: 准备 Electron 资源...');
    
    const electronDir = path.join(rootDir, 'electron');
    
    // 复制前端
    fs.copySync(
      path.join(rootDir, 'frontend', 'dist'),
      path.join(electronDir, 'frontend', 'dist')
    );
    
    // 复制后端
    fs.copySync(
      path.join(rootDir, 'dist', 'serial-backend'),
      path.join(electronDir, 'backend')
    );
    
    // 4. 构建 Electron 应用
    console.log('\n⚡ 步骤 4/4: 构建 Electron 应用...');
    execSync('npm run build', {
      cwd: electronDir,
      stdio: 'inherit'
    });
    
    console.log('\n✅ 构建完成！');
    console.log(`📦 输出目录: ${path.join(rootDir, 'release')}`);
    
  } catch (error) {
    console.error('\n❌ 构建失败:', error.message);
    process.exit(1);
  }
}

buildAll();
```

---

## 8. 开发脚本

**文件路径：** `scripts/dev.js`

```javascript
#!/usr/bin/env node
/**
 * 开发模式启动脚本
 */

const { spawn } = require('child_process');
const path = require('path');

const rootDir = path.join(__dirname, '..');

console.log('🚀 启动开发环境...\n');

// 启动 Python 后端
console.log('启动 Python 后端...');
const backend = spawn('python', ['start.py'], {
  cwd: rootDir,
  stdio: 'inherit'
});

// 等待 2 秒后启动前端
setTimeout(() => {
  console.log('\n启动前端开发服务器...');
  const frontend = spawn('npm', ['run', 'dev'], {
    cwd: path.join(rootDir, 'frontend'),
    stdio: 'inherit',
    shell: true
  });
  
  frontend.on('close', () => {
    backend.kill();
  });
}, 2000);

// 等待 5 秒后启动 Electron
setTimeout(() => {
  console.log('\n启动 Electron...');
  const electron = spawn('npm', ['start'], {
    cwd: path.join(rootDir, 'electron'),
    stdio: 'inherit',
    shell: true
  });
  
  electron.on('close', () => {
    backend.kill();
  });
}, 5000);

process.on('SIGINT', () => {
  console.log('\n停止所有进程...');
  backend.kill();
  process.exit();
});
```

---

## 使用说明

### 初次设置

1. **安装 Python 依赖**
```bash
pip install -r requirements.txt
pip install pyinstaller
```

2. **安装前端依赖**
```bash
cd frontend
npm install
```

3. **创建 Electron 目录并安装依赖**
```bash
mkdir electron
cd electron
npm init -y
npm install electron electron-builder find-free-port node-fetch
```

### 开发模式

```bash
# 方式 1: 使用开发脚本
node scripts/dev.js

# 方式 2: 手动启动
# 终端 1
python start.py

# 终端 2
cd frontend && npm run dev

# 终端 3
cd electron && npm start
```

### 生产构建

```bash
# 完整构建
node scripts/build_all.js

# 或分步构建
cd frontend && npm run build
python scripts/build_backend.py
cd electron && npm run build
```

### 平台特定构建

```bash
cd electron

# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux
```
