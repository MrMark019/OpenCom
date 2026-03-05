# 打包说明

## 快速打包

### Windows
```bash
build.bat
```

### 手动打包步骤

1. **打包 Python 后端**
```bash
pip install pyinstaller
pyinstaller backend.spec
```

2. **构建前端**
```bash
cd frontend
npm install
npm run build
cd ..
```

3. **复制文件到 Electron**
```bash
xcopy /E /I /Y dist\serial-backend electron\backend
xcopy /E /I /Y frontend\dist electron\frontend\dist
```

4. **打包 Electron**
```bash
cd electron
npm install
npm run build:win
```

## 输出

打包完成后，可执行文件在 `release/` 目录中。

## 注意事项

- 首次打包需要下载依赖，可能需要较长时间
- 确保已安装 Node.js 和 Python
- Windows 需要安装 Visual C++ 构建工具
