@echo off
echo ========================================
echo   PrintsAlot Receiver - Installer
echo ========================================
echo.

:: Check if exe exists
if not exist "dist\PrintsAlot.exe" (
    echo ERROR: PrintsAlot.exe not found!
    echo Please run build.bat first.
    pause
    exit /b 1
)

:: Create installation directory
set INSTALL_DIR=%LOCALAPPDATA%\PrintsAlot
echo Installing to: %INSTALL_DIR%
echo.

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy files
echo Copying files...
copy /Y "dist\PrintsAlot.exe" "%INSTALL_DIR%\"

:: Create Start Menu shortcut
echo Creating Start Menu shortcut...
set SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\PrintsAlot Receiver.lnk
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%INSTALL_DIR%\PrintsAlot.exe'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'PrintsAlot Receiver'; $s.Save()"

echo.
echo ========================================
echo Installation complete!
echo.
echo Would you like to run first-time setup now?
echo This will configure autostart with Windows.
echo ========================================
echo.

set /p SETUP="Run setup? (Y/N): "
if /i "%SETUP%"=="Y" (
    echo.
    start "" "%INSTALL_DIR%\PrintsAlot.exe" --setup
) else (
    echo.
    echo You can run setup later with:
    echo   "%INSTALL_DIR%\PrintsAlot.exe" --setup
    echo.
    echo Or start the app normally:
    echo   "%INSTALL_DIR%\PrintsAlot.exe"
)

pause


