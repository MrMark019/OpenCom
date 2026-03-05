# Electron 桌面应用打包方案

## 项目概述

将 OpenCom 串口调试工具（Python FastAPI + React）打包成 Electron 原生桌面应用。

**当前技术栈：**
- 后端：Python 3.9+, FastAPI, pyserial, uvicorn, websockets
- 前端：React 18, TypeScript, Vite, Zustand
- 通信：WebSocket 实时数据流，REST API

**目标：**
- 单一可执行文件，无需用户安装 Python 环境
- 跨平台支持（Windows, macOS, Linux）
- 保留所有串口调试功能
- 体积控制在 150MB 以内

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────┐
│         Electron 主进程 (Node.js)            │
│  - 窗口管理                                  │
│  - Python 后端进程管理                       │
│  - 系统托盘                                  │
│  - 自动更新                                  │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌─────▼──────────────────┐
│ 渲染进程     │  │  Python 后端子进程      │
│ (React UI)  │  │  - FastAPI Server      │
│             │◄─┤  - Serial Manager      │
│             │  │  - WebSocket           │
└─────────────┘  └────────────────────────┘
   HTTP/WS 通信
   localhost:随机端口
```

### 关键设计决策

1. **Python 后端打包方式：PyInstaller**
   - 将整个 Python 环境和依赖打包成单一可执行文件
   - 支持 Windows (.exe), macOS (.app), Linux (binary)

2. **进程管理策略**
   - Electron 主进程启动时自动启动 Python 后端子进程
   - 使用随机端口避免冲突
   - 健康检查机制确保后端就绪
   - 应用退出时优雅关闭后端进程

3. **前端集成方式**
   - 使用 Vite 构建前端静态资源
   - Electron 加载本地 HTML 文件
   - 动态配置 API 端点（通过环境变量或配置文件）

---

## 实施步骤

### 第一阶段：Python 后端打包

#### 1.1 创建 PyInstaller 配置

**文件：`backend.spec`**
- 指定入口文件：`backend/main.py`
- 包含所有依赖：pyserial, fastapi, uvicorn
- 打包模式：`--onefile`（单文件）或 `--onedir`（目录模式，推荐）
- 隐藏导入：处理动态导入的模块
- 数据文件：无需额外数据文件

#### 1.2 修改后端启动逻辑

**需要修改的文件：**
- `backend/main.py`：添加命令行参数支持（端口号）
- 创建 `backend/electron_entry.py`：专门用于 Electron 环境的入口

**关键功能：**
```python
# 支持动态端口
if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
```

#### 1.3 构建脚本

**文件：`scripts/build_backend.py`**
- 自动检测操作系统
- 执行 PyInstaller 构建
- 输出到 `dist/backend/` 目录
- 验证构建产物

---

### 第二阶段：Electron 应用搭建

#### 2.1 初始化 Electron 项目

**目录结构：**
```
electron/
├── main.js              # 主进程入口
├── preload.js           # 预加载脚本
├── package.json         # Electron 依赖
├── backend-manager.js   # Python 后端管理器
└── config.js            # 配置管理
```

**核心依赖：**
```json
{
  "dependencies": {
    "electron": "^28.0.0",
    "electron-builder": "^24.0.0",
    "find-free-port": "^2.0.0"
  }
}
```

#### 2.2 主进程实现（main.js）

**核心功能：**

1. **窗口创建**
```javascript
function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  
  // 加载前端
  win.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
}
```

2. **后端进程管理**
```javascript
let backendProcess = null;
let backendPort = null;

async function startBackend() {
  // 1. 查找空闲端口
  backendPort = await findFreePort(8000);
  
  // 2. 确定后端可执行文件路径
  const backendPath = getBackendPath();
  
  // 3. 启动子进程
  backendProcess = spawn(backendPath, [backendPort.toString()]);
  
  // 4. 等待后端就绪
  await waitForBackend(backendPort);
  
  // 5. 将端口信息传递给渲染进程
  return backendPort;
}
```

3. **生命周期管理**
```javascript
app.on('ready', async () => {
  await startBackend();
  createWindow();
});

app.on('quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
```

#### 2.3 预加载脚本（preload.js）

**暴露安全的 API 给渲染进程：**
```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getBackendPort: () => ipcRenderer.invoke('get-backend-port'),
  onBackendReady: (callback) => ipcRenderer.on('backend-ready', callback)
});
```

---

### 第三阶段：前端适配

#### 3.1 修改 API 配置

**文件：`frontend/src/config.ts`（新建）**
```typescript
// 检测是否在 Electron 环境
const isElectron = () => {
  return window.electronAPI !== undefined;
};

// 动态获取 API 基础 URL
export const getApiBase = async () => {
  if (isElectron()) {
    const port = await window.electronAPI.getBackendPort();
    return `http://127.0.0.1:${port}/api`;
  }
  return 'http://localhost:8000/api';
};

export const getWsUrl = async () => {
  if (isElectron()) {
    const port = await window.electronAPI.getBackendPort();
    return `ws://127.0.0.1:${port}/api/ws`;
  }
  return 'ws://localhost:8000/api/ws';
};
```

**修改：`frontend/src/App.tsx`**
```typescript
// 替换硬编码的 URL
const [apiBase, setApiBase] = useState('');
const [wsUrl, setWsUrl] = useState('');

useEffect(() => {
  const initConfig = async () => {
    setApiBase(await getApiBase());
    setWsUrl(await getWsUrl());
  };
  initConfig();
}, []);
```

#### 3.2 构建配置调整

**修改：`frontend/vite.config.ts`**
```typescript
export default defineConfig({
  base: './',  // 使用相对路径
  build: {
    outDir: 'dist',
    sourcemap: false,  // 生产环境关闭
    rollupOptions: {
      output: {
        manualChunks: undefined  // 避免过多分块
      }
    }
  }
});
```

---

### 第四阶段：构建和打包

#### 4.1 统一构建脚本

**文件：`scripts/build_all.js`**

```javascript
const { execSync } = require('child_process');
const fs = require('fs-extra');

async function buildAll() {
  console.log('🔨 开始构建...');
  
  // 1. 构建前端
  console.log('📦 构建前端...');
  execSync('cd frontend && npm run build', { stdio: 'inherit' });
  
  // 2. 打包 Python 后端
  console.log('🐍 打包 Python 后端...');
  execSync('python scripts/build_backend.py', { stdio: 'inherit' });
  
  // 3. 复制资源到 Electron 目录
  console.log('📋 复制资源...');
  fs.copySync('frontend/dist', 'electron/frontend/dist');
  fs.copySync('dist/backend', 'electron/backend');
  
  // 4. 构建 Electron 应用
  console.log('⚡ 构建 Electron 应用...');
  execSync('cd electron && npm run build', { stdio: 'inherit' });
  
  console.log('✅ 构建完成！');
}

buildAll().catch(console.error);
```

#### 4.2 Electron Builder 配置

**文件：`electron/package.json`**
```json
{
  "name": "serial-debugger",
  "version": "0.1.0",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "build:win": "electron-builder --win",
    "build:mac": "electron-builder --mac",
    "build:linux": "electron-builder --linux"
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

## 关键技术细节

### 1. 端口管理

**问题：** 避免端口冲突
**解决方案：**
```javascript
const findFreePort = require('find-free-port');

async function getAvailablePort(startPort = 8000) {
  const [port] = await findFreePort(startPort, startPort + 100);
  return port;
}
```

### 2. 后端健康检查

**问题：** 确保后端启动完成再加载前端
**解决方案：**
```javascript
async function waitForBackend(port, maxRetries = 30) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/api/health`);
      if (response.ok) return true;
    } catch (e) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  throw new Error('Backend failed to start');
}
```

### 3. 资源路径处理

**开发环境 vs 生产环境：**
```javascript
const isDev = !app.isPackaged;

function getBackendPath() {
  if (isDev) {
    // 开发环境：使用 Python 直接运行
    return 'python';
  } else {
    // 生产环境：使用打包的可执行文件
    const platform = process.platform;
    const ext = platform === 'win32' ? '.exe' : '';
    return path.join(process.resourcesPath, 'backend', `backend${ext}`);
  }
}
```

### 4. 串口权限处理

**macOS/Linux：** 需要串口访问权限
**解决方案：**
- macOS: 在 `Info.plist` 中声明权限
- Linux: 将用户添加到 `dialout` 组（安装后提示）

---

## 跨平台兼容性

### Windows
- ✅ PyInstaller 支持良好
- ✅ COM 端口扫描正常
- ⚠️ 需要管理员权限访问某些串口
- 📦 打包格式：NSIS 安装包 + 便携版

### macOS
- ✅ PyInstaller 支持（需要 codesign）
- ✅ cu.* 端口扫描正常
- ⚠️ 需要在系统偏好设置中授权串口访问
- 📦 打包格式：DMG + ZIP

### Linux
- ✅ PyInstaller 支持
- ✅ ttyUSB*/ttyACM* 扫描正常
- ⚠️ 需要 udev 规则或用户组权限
- 📦 打包格式：AppImage + DEB

---

## 体积优化

### 预期体积分析
```
总体积：~120-150MB
├── Electron 运行时：~80MB
├── Python 后端：~30-40MB
│   ├── Python 解释器：~15MB
│   ├── 依赖库：~15-25MB
│   └── 应用代码：~1MB
└── 前端资源：~5-10MB
```

### 优化策略

1. **Python 后端优化**
   - 使用 `--exclude-module` 排除不需要的库
   - 移除测试和开发依赖
   - 使用 UPX 压缩可执行文件

2. **前端优化**
   - 启用代码分割和 Tree Shaking
   - 压缩图片和静态资源
   - 移除 source maps

3. **Electron 优化**
   - 使用 `asar` 打包应用代码
   - 排除开发依赖

---

## 开发和测试流程

### 开发模式

**启动方式：**
```bash
# 终端 1：启动 Python 后端
python start.py

# 终端 2：启动前端开发服务器
cd frontend && npm run dev

# 终端 3：启动 Electron（开发模式）
cd electron && npm start
```

### 测试流程

1. **单元测试**
   - Python 后端：`pytest`
   - 前端：`npm test`

2. **集成测试**
   - 测试 Electron 与后端通信
   - 测试串口功能

3. **打包测试**
   - 在目标平台上测试打包后的应用
   - 验证所有功能正常

---

## 发布策略

### 版本管理
- 使用语义化版本：`v0.1.0`
- 同步更新 `package.json` 和 `pyproject.toml`

### 自动更新（可选）
- 使用 `electron-updater`
- 配置更新服务器
- 支持增量更新

### 发布渠道
- GitHub Releases
- 官网下载
- 可选：Microsoft Store, Mac App Store

---

## 潜在问题和解决方案

### 问题 1：PyInstaller 打包失败
**原因：** 隐藏导入或动态加载的模块
**解决：** 在 `.spec` 文件中显式声明 `hiddenimports`

### 问题 2：串口权限被拒绝
**原因：** 操作系统权限限制
**解决：** 
- Windows: 以管理员身份运行
- macOS: 请求系统权限
- Linux: 提供 udev 规则文件

### 问题 3：WebSocket 连接失败
**原因：** 端口未就绪或防火墙阻止
**解决：** 
- 增加健康检查重试次数
- 使用 127.0.0.1 而非 localhost

### 问题 4：打包体积过大
**原因：** 包含了不必要的依赖
**解决：** 
- 使用虚拟环境隔离依赖
- 排除测试和文档文件

---

## 时间线和里程碑

### 阶段 1：基础搭建（第 1-2 天）
- ✅ 创建 Electron 项目结构
- ✅ 实现基本的主进程和渲染进程
- ✅ 配置 PyInstaller

### 阶段 2：集成开发（第 3-5 天）
- ✅ 实现后端进程管理
- ✅ 前端 API 配置适配
- ✅ 开发模式调试

### 阶段 3：打包测试（第 6-7 天）
- ✅ 完成构建脚本
- ✅ 在各平台测试打包
- ✅ 功能验证

### 阶段 4：优化发布（第 8-10 天）
- ✅ 体积优化
- ✅ 性能优化
- ✅ 准备发布材料

---

## 下一步行动

1. **立即开始：** 创建 Electron 项目结构
2. **配置 PyInstaller：** 编写 backend.spec
3. **修改前端配置：** 支持动态 API 端点
4. **实现主进程：** 后端进程管理逻辑
5. **测试集成：** 确保所有功能正常

---

## 参考资源

- [Electron 官方文档](https://www.electronjs.org/docs)
- [PyInstaller 文档](https://pyinstaller.org/en/stable/)
- [electron-builder 文档](https://www.electron.build/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
