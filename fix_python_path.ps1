# 修复 Python PATH 环境变量

# 1. 获取当前用户 PATH
$userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
Write-Host "Current PATH length: $($userPath.Length)"

# 2. 移除 KiCad 的 Python 路径
$paths = $userPath -split ';'
$filteredPaths = $paths | Where-Object { 
    $_ -notmatch 'Kicad8' -and 
    $_ -ne '' 
}

# 3. 添加 WindowsApps 路径到最前面
$windowsAppsPath = 'C:\Users\Mr_Mark_qwq\AppData\Local\Microsoft\WindowsApps'
$newPathList = @($windowsAppsPath) + $filteredPaths
$newPath = $newPathList -join ';'

# 4. 设置新的 PATH
[Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
Write-Host "PATH updated successfully!"
Write-Host "New PATH length: $($newPath.Length)"

# 5. 验证 KiCad 路径已被移除
if ($newPath -match 'Kicad8') {
    Write-Warning "Warning: KiCad path still exists in PATH"
} else {
    Write-Host "KiCad path removed successfully"
}
