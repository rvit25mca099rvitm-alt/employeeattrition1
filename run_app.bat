@echo off
title Employee Attrition & XAI Predictor - Flask Server
echo ========================================================
echo   Starting Employee Attrition & Explainable AI System
echo ========================================================
echo.
echo Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b %errorlevel%
)
echo.
echo Running Flask Application on Port 5001...
echo Open your browser at: http://127.0.0.1:5001
echo.
python app.py
pause
