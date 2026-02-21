@echo off
echo ========================================
echo Emergency Response System - Quick Start
echo ========================================
echo.

REM Navigate to the project directory
cd /d "%~dp0"

echo Current directory: %CD%
echo.

echo Step 1: Installing dependencies...
pip install -r requirements.txt
echo.

echo Step 2: Testing database connection...
python test_connection.py
echo.

echo Step 3: Starting Flask server...
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
