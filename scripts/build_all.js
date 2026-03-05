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
