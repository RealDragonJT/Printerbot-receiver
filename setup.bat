@echo off
echo ========================================
echo   PrintsAlot V2 - Initial Setup
echo ========================================
echo.

:: Create virtual environment
echo Creating virtual environment...
py -m venv venv
if errorlevel 1 (
    echo Failed to create virtual environment!
    pause
    exit /b 1
)
echo Virtual environment created successfully.
echo.

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment!
    pause
    exit /b 1
)
echo Virtual environment activated.
echo.

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements!
    pause
    exit /b 1
)
echo Requirements installed successfully.
echo.

:: Run the application
echo ========================================
echo   Starting PrintsAlot V2...
echo ========================================
echo.
py -m src.main

pause

