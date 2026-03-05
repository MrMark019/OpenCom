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
