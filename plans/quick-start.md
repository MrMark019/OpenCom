# 快速开始指南

本指南帮助你快速将 OpenCom 串口调试工具打包成 Electron 桌面应用。

---

## 前置要求

- Python 3.9+
- Node.js 16+
- npm 或 yarn
- Git

---

## 第一步：项目准备

### 1. 安装 Python 依赖

```bash
# 安装项目依赖
pip install -r requirements.txt

# 安装打包工具
pip install pyinstaller
```

### 2. 测试后端运行

```bash
python start.py
```

访问 http://localhost:8000 确认后端正常运行。

### 3. 构建前端

```bash
cd frontend
npm install
npm run build
```

确认 `frontend/dist` 目录生成成功。

---

## 第二步：创建 Electron 项目

### 1. 创建目录结构

```bash
# 在项目根目录执行
mkdir electron
cd electron
```

### 2. 初始化 package.json

```bash
npm init -y
```

### 3. 安装依赖

```bash
npm install electron electron-builder find-free-port node-fetch --save
```

### 4. 创建必要文件

从 [`plans/config-examples.md`](plans/config-examples.md) 复制以下文件内容：

- `electron/main.js` - 主进程代码
- `electron/preload.js` - 预加载脚本
- 更新 `electron/package.json` - 添加构建配置

---

## 第三步：配置 PyInstaller

### 1. 创建 spec 文件

在项目根目录创建 `backend.spec`，内容参考 [`plans/config-examples.md`](plans/config-examples.md) 第 1 节。

### 2. 测试打包

```bash
pyinstaller backend.spec --clean
```

检查 `dist/serial-backend` 目录是否生成成功。

### 3. 测试可执行文件

```bash
# Windows
dist\serial-backend\serial-backend.exe 8000

# macOS/Linux
./dist/serial-backend/serial-backend 8000
```

访问 http://localhost:8000/api/health 确认后端正常。

---

## 第四步：适配前端

### 1. 创建配置文件

在 `frontend/src/` 创建 `config.ts`，内容参考 [`plans/config-examples.md`](plans/config-examples.md) 第 6 节。

### 2. 修改 App.tsx

```typescript
// 在文件顶部添加
import { getApiBase, getWsUrl } from './config';

// 在 App 组件中添加状态
const [apiBase, setApiBase] = useState('');
const [wsUrl, setWsUrl] = useState('');

// 添加初始化 effect
useEffect(() => {
  const initConfig = async () => {
    setApiBase(await getApiBase());
    setWsUrl(await getWsUrl());
  };
  initConfig();
}, []);

// 替换所有硬编码的 URL
// 将 'http://localhost:8000/api' 替换为 apiBase
// 将 'ws://localhost:8000/api/ws' 替换为 wsUrl
```

### 3. 重新构建前端

```bash
cd frontend
npm run build
```

---

## 第五步：集成测试

### 1. 准备 Electron 资源

```bash
# 在项目根目录执行
# 复制前端
cp -r frontend/dist electron/frontend/dist

# 复制后端
cp -r dist/serial-backend electron/backend
```

### 2. 启动 Electron（开发模式）

```bash
cd electron
npm start
```

应该看到应用窗口打开，并且能正常使用所有串口功能。

---

## 第六步：构建发布版本

### 1. 创建构建脚本

在 `scripts/` 目录创建 `build_all.js`，内容参考 [`plans/config-examples.md`](plans/config-examples.md) 第 7 节。

### 2. 执行完整构建

```bash
node scripts/build_all.js
```

### 3. 查看输出

构建完成后，在 `release/` 目录查看生成的安装包：

- Windows: `.exe` 安装程序和便携版
- macOS: `.dmg` 和 `.zip`
- Linux: `.AppImage` 和 `.deb`

---

## 常见问题

### Q1: PyInstaller 打包失败

**症状：** 提示找不到某些模块

**解决：**
```bash
# 在 backend.spec 的 hiddenimports 中添加缺失的模块
hiddenimports=[
    'missing_module_name',
    # ...
]
```

### Q2: Electron 启动后端失败

**症状：** 控制台显示 "后端启动超时"

**解决：**
1. 检查后端可执行文件路径是否正确
2. 手动运行后端测试：`./electron/backend/serial-backend 8000`
3. 查看后端日志输出

### Q3: 前端无法连接后端

**症状：** API 请求失败

**解决：**
1. 打开开发者工具查看实际请求的 URL
2. 确认 `config.ts` 正确实现
3. 检查 `preload.js` 是否正确加载

### Q4: 串口权限被拒绝

**Windows:**
- 以管理员身份运行应用

**macOS:**
- 系统偏好设置 → 安全性与隐私 → 授权应用访问

**Linux:**
```bash
# 将用户添加到 dialout 组
sudo usermod -a -G dialout $USER
# 重新登录生效
```

### Q5: 打包体积过大

**优化方法：**
1. 在 `backend.spec` 中添加更多 `excludes`
2. 使用 UPX 压缩（已在配置中启用）
3. 移除不必要的依赖

---

## 开发工作流

### 日常开发

```bash
# 方式 1: 分别启动（推荐）
# 终端 1: 后端
python start.py

# 终端 2: 前端
cd frontend && npm run dev

# 终端 3: Electron
cd electron && npm start

# 方式 2: 使用开发脚本
node scripts/dev.js
```

### 测试打包

```bash
# 仅测试后端打包
python scripts/build_backend.py

# 仅测试前端构建
cd frontend && npm run build

# 测试 Electron 打包（不构建安装包）
cd electron && npm start
```

### 完整构建

```bash
# 构建所有平台
node scripts/build_all.js

# 构建特定平台
cd electron
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

---

## 下一步

完成基础打包后，可以考虑以下增强功能：

1. **自动更新**
   - 集成 `electron-updater`
   - 配置更新服务器

2. **应用图标**
   - 准备不同尺寸的图标
   - Windows: `.ico`
   - macOS: `.icns`
   - Linux: `.png`

3. **代码签名**
   - Windows: 购买代码签名证书
   - macOS: 使用 Apple Developer 账号签名

4. **安装程序定制**
   - 自定义安装向导
   - 添加许可协议
   - 配置快捷方式

5. **性能优化**
   - 启用 V8 快照
   - 优化启动时间
   - 减少内存占用

---

## 参考文档

- [完整方案文档](plans/electron-packaging-plan.md)
- [配置文件示例](plans/config-examples.md)
- [Electron 官方文档](https://www.electronjs.org/docs)
- [PyInstaller 文档](https://pyinstaller.org/)
- [electron-builder 文档](https://www.electron.build/)
