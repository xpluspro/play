# 猜东西游戏服务器配置脚本 (Windows)
# PowerShell脚本，支持清华源配置

Write-Host "=== 猜东西游戏服务器配置开始 ===" -ForegroundColor Green

# 检查是否以管理员权限运行
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "请以管理员权限运行此脚本" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查Python是否已安装
Write-Host "1. 检查Python环境..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "Python已安装: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "Python未安装，请先安装Python 3.8+" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/"
    Read-Host "按任意键退出"
    exit 1
}

# 配置pip清华源
Write-Host "2. 配置pip清华源..." -ForegroundColor Yellow
$pipDir = "$env:USERPROFILE\pip"
if (-not (Test-Path $pipDir)) {
    New-Item -ItemType Directory -Path $pipDir -Force | Out-Null
}

$pipConfig = @"
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
"@
$pipConfig | Out-File -FilePath "$pipDir\pip.ini" -Encoding UTF8
Write-Host "pip清华源配置完成" -ForegroundColor Green

# 创建Python虚拟环境
Write-Host "3. 创建Python虚拟环境..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "虚拟环境已存在，跳过创建" -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "虚拟环境创建完成" -ForegroundColor Green
}

# 激活虚拟环境并安装依赖
Write-Host "4. 安装Python依赖包..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt
Write-Host "Python依赖安装完成" -ForegroundColor Green

# 检查Redis
Write-Host "5. 检查Redis服务..." -ForegroundColor Yellow
$redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
if ($redisService) {
    if ($redisService.Status -eq "Running") {
        Write-Host "Redis服务正在运行" -ForegroundColor Green
    } else {
        Start-Service -Name "Redis"
        Write-Host "Redis服务已启动" -ForegroundColor Green
    }
} else {
    Write-Host "Redis未安装，请手动安装Redis" -ForegroundColor Red
    Write-Host "推荐使用: https://github.com/tporadowski/redis/releases"
    Write-Host "或使用Docker: docker run -d -p 6379:6379 redis:alpine"
}

# 创建启动脚本
Write-Host "6. 创建启动脚本..." -ForegroundColor Yellow
$startScript = @"
@echo off
echo Starting Guess Game Server...
cd /d "%~dp0"
call venv\Scripts\activate.bat
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
pause
"@
$startScript | Out-File -FilePath "start_server.bat" -Encoding UTF8

$startScriptPS = @"
Write-Host "启动猜东西游戏服务器..." -ForegroundColor Green
Set-Location `$PSScriptRoot
& ".\venv\Scripts\Activate.ps1"
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"@
$startScriptPS | Out-File -FilePath "start_server.ps1" -Encoding UTF8

Write-Host "启动脚本创建完成" -ForegroundColor Green

# 创建Windows服务配置文件 (可选)
Write-Host "7. 创建服务配置文件..." -ForegroundColor Yellow
$serviceConfig = @"
# 使用NSSM (Non-Sucking Service Manager) 创建Windows服务
# 1. 下载NSSM: https://nssm.cc/download
# 2. 以管理员权限运行:
#    nssm install GuessGameService
# 3. 配置服务:
#    Application Path: $(Get-Location)\venv\Scripts\uvicorn.exe
#    Arguments: main:app --host 0.0.0.0 --port 8000 --workers 4
#    Startup Directory: $(Get-Location)

# 或使用PowerShell直接创建服务 (需要PowerShell 6+):
# New-Service -Name "GuessGameService" -BinaryPathName "$(Get-Location)\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000 --workers 4" -StartupType Automatic
"@
$serviceConfig | Out-File -FilePath "service_setup.txt" -Encoding UTF8

# 配置防火墙规则
Write-Host "8. 配置防火墙规则..." -ForegroundColor Yellow
try {
    New-NetFirewallRule -DisplayName "Guess Game HTTP" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName "Guess Game HTTP Alt" -Direction Inbound -Port 80 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
    Write-Host "防火墙规则配置完成" -ForegroundColor Green
} catch {
    Write-Host "防火墙规则配置失败，请手动配置" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 配置完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "📝 接下来的步骤:" -ForegroundColor Cyan
Write-Host "1. 编辑 .env 文件，设置你的 Qwen API Key:" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 启动服务器:" -ForegroundColor White
Write-Host "   双击 start_server.bat 或运行 .\start_server.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 访问游戏: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "🔧 其他选项:" -ForegroundColor Cyan
Write-Host "- 查看 service_setup.txt 了解如何创建Windows服务" -ForegroundColor White
Write-Host "- Redis连接地址: redis://localhost:6379/0" -ForegroundColor White
Write-Host ""
Write-Host "⚡ 系统配置支持100+并发连接" -ForegroundColor Green

Read-Host "按任意键退出"
