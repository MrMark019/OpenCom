#!/usr/bin/env python3
"""
构建脚本：打包 Python 后端 + 前端 + Electron
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
ELECTRON_DIR = ROOT_DIR / "electron"
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

def run_command(cmd, cwd=None):
    """运行命令"""
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"错误: 命令失败")
        sys.exit(1)

def build_backend():
    """使用 PyInstaller 打包后端"""
    print("\n=== 打包 Python 后端 ===")

    # 确保 PyInstaller 已安装
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 创建后端打包目录
    backend_build_dir = ELECTRON_DIR / "backend"
    backend_build_dir.mkdir(exist_ok=True)

    # PyInstaller 打包
    spec_file = ROOT_DIR / "backend.spec"
    if spec_file.exists():
        run_command([sys.executable, "-m", "PyInstaller", str(spec_file)], cwd=ROOT_DIR)
    else:
        # 使用默认配置打包
        run_command([
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--name", "serial-backend",
            "--add-data", f"{BACKEND_DIR};backend",
            str(ROOT_DIR / "start.py")
        ], cwd=ROOT_DIR)

    # 复制打包后的可执行文件
    dist_dir = ROOT_DIR / "dist"
    exe_name = "serial-backend.exe" if sys.platform == "win32" else "serial-backend"
    src_exe = dist_dir / exe_name

    if src_exe.exists():
        shutil.copy2(src_exe, backend_build_dir / exe_name)
        print(f"✓ 后端已打包: {backend_build_dir / exe_name}")
    else:
        print(f"错误: 找不到打包的后端文件")
        sys.exit(1)

def build_frontend():
    """构建前端"""
    print("\n=== 构建前端 ===")

    # 安装依赖
    run_command(["npm", "install"], cwd=FRONTEND_DIR)

    # 构建
    run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)

    # 复制到 electron 目录
    frontend_dist = FRONTEND_DIR / "dist"
    electron_frontend = ELECTRON_DIR / "frontend" / "dist"

    if electron_frontend.exists():
        shutil.rmtree(electron_frontend)

    shutil.copytree(frontend_dist, electron_frontend)
    print(f"✓ 前端已构建: {electron_frontend}")

def build_electron():
    """打包 Electron 应用"""
    print("\n=== 打包 Electron 应用 ===")

    # 安装依赖
    run_command(["npm", "install"], cwd=ELECTRON_DIR)

    # 打包
    platform = sys.platform
    if platform == "win32":
        run_command(["npm", "run", "build:win"], cwd=ELECTRON_DIR)
    elif platform == "darwin":
        run_command(["npm", "run", "build:mac"], cwd=ELECTRON_DIR)
    else:
        run_command(["npm", "run", "build:linux"], cwd=ELECTRON_DIR)

    print(f"\n✓ 打包完成！输出目录: {ROOT_DIR / 'release'}")

def main():
    print("开始构建 Serial Debugger 桌面应用...")

    build_backend()
    build_frontend()
    build_electron()

    print("\n=== 构建完成 ===")

if __name__ == "__main__":
    main()
