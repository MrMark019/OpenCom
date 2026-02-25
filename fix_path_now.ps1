# 立即修复当前会话的 PATH

# 获取当前 PATH
$currentPath = $env:PATH
Write-Host "Current PATH contains KiCad: $($currentPath -match 'Kicad8')"

# 移除所有包含 Kicad8 的路径
$pathParts = $currentPath -split ';'
$cleanedParts = $pathParts | Where-Object { $_ -notmatch 'Kicad8' }
$newPath = $cleanedParts -join ';'

# 设置新的 PATH
$env:PATH = $newPath
Write-Host "PATH updated!"
Write-Host "New PATH contains KiCad: $($env:PATH -match 'Kicad8')"

# 验证
Write-Host "`nVerifying python..."
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
Write-Host "Python path: $pythonPath"

# 尝试运行 python --version
Write-Host "`nPython version:"
python --version
