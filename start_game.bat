@echo off
chcp 65001 >nul
echo 启动猜东西游戏服务器...
echo ============================
echo.
echo 🎮 游戏服务器正在启动...
echo 📝 使用内存存储（适合开发测试）
echo 🌐 游戏地址: http://localhost:8000
echo.
echo 按 Ctrl+C 停止服务器
echo ============================
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe main_simple.py

echo.
echo 服务器已停止
pause
