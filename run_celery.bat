@echo off
REM Start Celery Worker and Beat Scheduler for Paperweight
REM Make sure Redis is running before starting this script

echo Starting Celery Worker and Beat Scheduler...
echo.

REM Start Celery Worker in a new window
start "Celery Worker" .\.venv\Scripts\celery.exe -A paperweight worker -l info

REM Give the worker a moment to start
timeout /t 2

REM Start Celery Beat in a new window
start "Celery Beat" .\.venv\Scripts\celery.exe -A paperweight beat -l info

echo.
echo Celery Worker and Beat are now running!
echo.
echo To stop:
echo 1. Close the Celery Worker window
echo 2. Close the Celery Beat window
echo.
pause
