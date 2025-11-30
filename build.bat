@echo off
echo ========================================
echo   PrintsAlot Receiver - Build Script
echo ========================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

:: Build the exe
echo.
echo Building executable...
pyinstaller --clean PrintsAlot.spec

echo.
echo ========================================
if exist "dist\PrintsAlot.exe" (
    echo Build successful!
    echo Executable: dist\PrintsAlot.exe
    echo.
    echo To run first-time setup:
    echo   dist\PrintsAlot.exe --setup
) else (
    echo Build failed! Check the output above for errors.
)
echo ========================================

pause


