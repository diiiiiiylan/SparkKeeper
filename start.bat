@echo off
chcp 65001 >nul
title SparkKeeper

echo ========================================
echo   SparkKeeper - 自动续火花
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时记得勾选 "Add Python to PATH"
    pause
    exit /b 1
)

:: 安装依赖
echo 正在检查依赖...
pip install pyautogui pywinauto pyperclip apscheduler >nul 2>&1
echo 依赖就绪

:: 启动 GUI
echo 启动中...
python app.py

pause
