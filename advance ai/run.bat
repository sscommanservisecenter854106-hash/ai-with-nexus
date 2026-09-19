@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title Nexus-AI Platform Launcher
cd /d "%~dp0"
echo ==========================================================
echo        NEXUS-AI: Autonomous Multimodal Platform
echo ==========================================================
echo Checking Python environment...
python --version >nul 2>&1
if not errorlevel 1 (
    echo Starting Nexus-AI server with Python...
    python run.py
    pause
    exit /b
)

py --version >nul 2>&1
if not errorlevel 1 (
    echo Starting Nexus-AI server with Py launcher...
    py -3 run.py
    pause
    exit /b
)

echo [ERROR] Python is not installed or not in PATH!
echo Please install Python 3.10+ from python.org and check "Add Python to PATH"
pause
