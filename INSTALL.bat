@echo off
echo ========================================
echo Installing Dependencies
echo ========================================
echo.

REM Navigate to the project directory
cd /d "%~dp0"

echo Installing packages from requirements.txt...
pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Installation completed successfully!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Run: python test_connection.py
    echo 2. Run: python app.py
) else (
    echo.
    echo ========================================
    echo Installation failed!
    echo ========================================
    echo.
    echo Try running: pip install --user -r requirements.txt
)

pause
