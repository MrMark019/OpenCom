@echo off
echo === 构建 Serial Debugger 桌面应用 ===

echo.
echo [1/4] 安装 Python 依赖...
pip install pyinstaller

echo.
echo [2/4] 打包 Python 后端...
pyinstaller backend.spec

echo.
echo [3/4] 构建前端...
cd frontend
call npm install
call npm run build
cd ..

echo.
echo [4/4] 复制文件并打包 Electron...
if not exist "electron\backend" mkdir electron\backend
if not exist "electron\frontend" mkdir electron\frontend
xcopy /E /I /Y "dist\serial-backend" "electron\backend"
xcopy /E /I /Y "frontend\dist" "electron\frontend\dist"

cd electron
call npm install
call npm run build:win
cd ..

echo.
echo === 构建完成！===
echo 输出目录: release\
pause
