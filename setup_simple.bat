@echo off
chcp 65001 >nul
echo 猜东西游戏服务器配置 (简化版)
echo ===========================

echo 1. 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python未安装，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python环境检查通过

echo.
echo 2. 配置pip清华源...
if not exist "%USERPROFILE%\pip" mkdir "%USERPROFILE%\pip"
(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple
echo trusted-host = pypi.tuna.tsinghua.edu.cn
) > "%USERPROFILE%\pip\pip.ini"
echo pip清华源配置完成

echo.
echo 3. 创建虚拟环境...
if exist venv (
    echo 虚拟环境已存在
) else (
    python -m venv venv
    echo 虚拟环境创建完成
)

echo.
echo 4. 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 5. 创建启动脚本...
(
echo @echo off
echo echo 启动猜东西游戏服务器...
echo cd /d "%%~dp0"
echo call venv\Scripts\activate.bat
echo uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
echo pause
) > start_server.bat

echo.
echo 配置完成！
echo.
echo 接下来的步骤:
echo 1. 编辑 .env 文件，设置你的 Qwen API Key
echo 2. 安装Redis (推荐使用Docker: docker run -d -p 6379:6379 redis:alpine)
echo 3. 双击 start_server.bat 启动服务器
echo 4. 访问: http://localhost:8000
echo.
pause
