@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
title AI辅助业务分析培训系统

echo ========================================
echo  AI辅助业务分析个性化培训系统
echo  基于多智能体协同的AI培训平台
echo ========================================
echo.

:: 切换到脚本所在目录的 backend 子目录
cd /d "%~dp0backend"
if %errorlevel% neq 0 (
    echo [ERROR] 无法进入 backend 目录
    echo 当前路径: %~dp0
    pause
    exit /b 1
)

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 Python！
    echo 请从 https://www.python.org/downloads/ 下载安装 Python 3.10+
    echo.
    echo 安装后，请确保勾选 "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  Python 版本: %%i

:: 创建并激活虚拟环境（关键修复：确保 venv 可用）
if not exist "venv\" (
    echo [1/3] 首次运行，正在创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] 虚拟环境创建失败！
        echo 请尝试: python -m venv venv --without-pip
        pause
        exit /b 1
    )
) else (
    echo [1/3] 虚拟环境已存在
)

:: 激活虚拟环境
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] 虚拟环境激活失败
    pause
    exit /b 1
)

:: 安装依赖
echo [2/3] 安装/检查依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 依赖安装失败
    echo 请尝试手动运行: pip install -r requirements.txt
    pause
    exit /b 1
)

:: 创建 .env（如果不存在）
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo  已创建默认配置文件 .env
    )
)

:: 获取本机IP
set IP=localhost
for /f "tokens=2 delims=:" %%a in ('ipconfig 2^>nul ^| findstr /c:"IPv4" 2^>nul') do (
    set IP=%%a
    goto :ipfound
)
:ipfound
set IP=%IP: =%

:: 清理之前的端口占用（安全）
echo [3/3] 启动系统...
echo.
echo ========================================
echo  系统启动中，请稍候...
echo  本地访问:  http://localhost:8000
echo  局域网访问: http://%IP%:8000
echo  API文档:    http://localhost:8000/api/docs
echo ========================================
echo  提示: 保持此窗口打开，按 Ctrl+C 停止服务
echo.

:: 启动服务
python main.py

:: 如果 main.py 退出（用户按了 Ctrl+C），暂停以便查看
echo.
echo 服务已停止。
pause
