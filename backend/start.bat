@echo off
chcp 65001 >nul 2>&1
set PYTHONIOENCODING=utf-8
title AI辅助业务分析培训系统 (Backend)

echo ========================================
echo  AI辅助业务分析个性化培训系统
echo  后端启动脚本
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 Python！
    echo 请从 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  Python 版本: %%i

:: 创建并激活虚拟环境
if not exist "venv\" (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] 创建失败，尝试直接安装依赖...
        goto :no_venv
    )
)

call venv\Scripts\activate.bat
if %errorlevel% neq 0 goto :no_venv

echo [2/3] 安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 安装失败
    pause
    exit /b 1
)
goto :start_server

:no_venv
echo [信息] 使用系统 Python 安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] 安装失败
    pause
    exit /b 1
)

:start_server
:: 创建 .env
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo  已创建默认配置
    )
)

echo [3/3] 启动系统...
echo.
echo ========================================
echo  系统启动中...
echo  访问地址: http://localhost:8000
echo  API文档:  http://localhost:8000/api/docs
echo  提示: 保持此窗口打开
echo ========================================
echo.

python main.py

echo.
echo 服务已停止。
pause
