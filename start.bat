@echo off
chcp 65001 >nul
title SparkKeeper - 抖音自动续火花

echo ========================================
echo   SparkKeeper - 抖音自动续火花
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
echo [1/3] 正在安装依赖...
pip install pyautogui pywinauto pyperclip apscheduler >nul 2>&1
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo       依赖安装完成

:: 检查是否已校准
if not exist config.json (
    echo.
    echo [2/3] 首次使用，需要校准坐标
    python douyin_spark.py --setup
) else (
    echo [2/3] 已有配置，跳过校准
    echo       如需重新校准: python douyin_spark.py --setup
)

:: 启动
echo.
echo [3/3] 启动定时任务...
echo.
python douyin_spark.py

pause
