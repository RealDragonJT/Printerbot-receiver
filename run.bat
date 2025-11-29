@echo off
echo ========================================
echo   PrintsAlot V2
echo ========================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Run the application
echo Starting PrintsAlot V2...
echo.
python -m src.main

pause

