@echo off
REM Quick start script for Paperweight development environment
REM This script starts: Django dev server, Celery worker, and Celery beat

echo.
echo ============================================
echo  Paperweight Development Environment
echo ============================================
echo.

REM Check if venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

echo Starting development services...
echo.

REM Start Django Development Server
echo [1/3] Starting Django Development Server on http://127.0.0.1:8000
start "Django Dev Server" .\.venv\Scripts\python.exe manage.py runserver

REM Give Django a moment to start
timeout /t 3

REM Start Celery Worker
echo [2/3] Starting Celery Worker
start "Celery Worker" .\.venv\Scripts\celery.exe -A paperweight worker -l info

REM Give worker a moment to start
timeout /t 2

REM Start Celery Beat
echo [3/3] Starting Celery Beat Scheduler
start "Celery Beat" .\.venv\Scripts\celery.exe -A paperweight beat -l info

echo.
echo ============================================
echo  All services started!
echo ============================================
echo.
echo Django Dev Server:  http://127.0.0.1:8000
echo Admin Dashboard:    http://127.0.0.1:8000/admin
echo.
echo Services running in separate windows:
echo - Django Dev Server
echo - Celery Worker
echo - Celery Beat Scheduler
echo.
echo To stop everything, close all 3 windows.
echo.
echo Requirements:
echo - Redis must be running on localhost:6379
echo   (Use: redis-server or wsl redis-server)
echo.
pause
