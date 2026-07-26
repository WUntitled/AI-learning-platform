@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
title AI培训系统 (快速启动)

echo ========================================
echo  AI辅助业务分析培训系统
echo  快速启动（不创建虚拟环境）
echo ========================================
echo.

cd /d "%~dp0backend"

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 Python！
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  版本: %%i

:: 直接安装依赖到系统（不创建虚拟环境）
echo 安装依赖...
pip install -r requirements.txt

:: 创建 .env
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
    )
)

echo.
echo ========================================
echo  启动中...
echo  访问: http://localhost:8000
echo  按 Ctrl+C 停止
echo ========================================
echo.

python main.py

pause
