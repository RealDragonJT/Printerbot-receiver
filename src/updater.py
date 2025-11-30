"""
Self-updater module for PrintsAlot.
Handles downloading new versions and restarting the application.
"""
import os
import sys
import tempfile
import subprocess
import asyncio
import aiohttp
import logging
from typing import Callable, Optional

logger = logging.getLogger('PrintsAlot.updater')


class Updater:
    def __init__(self):
        self.download_progress = 0  # 0-100
        self.download_status = "idle"  # idle, downloading, ready, error
        self.error_message = None
        self._progress_callback: Optional[Callable[[int, str], None]] = None
    
    def on_progress(self, callback: Callable[[int, str], None]):
        """Set a callback for progress updates: callback(progress_percent, status)"""
        self._progress_callback = callback
    
    def _update_progress(self, progress: int, status: str):
        self.download_progress = progress
        self.download_status = status
        if self._progress_callback:
            self._progress_callback(progress, status)
    
    async def download_update(self, download_url: str) -> Optional[str]:
        """
        Download the update to a temporary location.
        Returns the path to the downloaded file, or None on failure.
        """
        self._update_progress(0, "downloading")
        logger.info(f"Downloading update from: {download_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status != 200:
                        self.error_message = f"Download failed: HTTP {response.status}"
                        self._update_progress(0, "error")
                        logger.error(self.error_message)
                        return None
                    
                    # Get file size for progress
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    # Create temp file
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, "PrintsAlot_update.exe")
                    
                    with open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                progress = int((downloaded / total_size) * 100)
                                self._update_progress(progress, "downloading")
                    
                    self._update_progress(100, "ready")
                    logger.info(f"Update downloaded to: {temp_path}")
                    return temp_path
                    
        except Exception as e:
            self.error_message = f"Download failed: {e}"
            self._update_progress(0, "error")
            logger.error(self.error_message, exc_info=True)
            return None
    
    def apply_update(self, new_exe_path: str) -> bool:
        """
        Apply the update by creating a batch script that:
        1. Waits for current process to exit
        2. Replaces the old exe with the new one
        3. Starts the new exe
        4. Cleans up the batch script
        
        Returns True if the update script was started successfully.
        """
        if not os.path.exists(new_exe_path):
            logger.error(f"Update file not found: {new_exe_path}")
            return False
        
        # Get current executable path
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
        else:
            # Running as script - for testing
            logger.warning("Running as script, update will not work properly")
            current_exe = sys.executable
        
        logger.info(f"Current exe: {current_exe}")
        logger.info(f"New exe: {new_exe_path}")
        
        # Create batch script in temp directory
        batch_script = os.path.join(tempfile.gettempdir(), "printsalot_update.bat")
        
        # Batch script content
        # Uses taskkill to ensure process is dead, then copies new exe, then starts it
        script_content = f'''@echo off
echo PrintsAlot Updater
echo Waiting for application to close...

REM Wait for the process to fully exit (up to 30 seconds)
set /a count=0
:waitloop
tasklist /FI "PID eq {os.getpid()}" 2>NUL | find /I /N "python">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    set /a count+=1
    if %count% lss 30 goto waitloop
)

REM Also check for PrintsAlot.exe
tasklist /FI "IMAGENAME eq PrintsAlot.exe" 2>NUL | find /I /N "PrintsAlot">NUL
if "%ERRORLEVEL%"=="0" (
    echo Killing PrintsAlot.exe...
    taskkill /F /IM PrintsAlot.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo Applying update...
copy /Y "{new_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo Update failed! Could not copy new file.
    pause
    exit /b 1
)

echo Starting updated application...
start "" "{current_exe}"

REM Clean up
del "{new_exe_path}" >nul 2>&1
del "%~f0" >nul 2>&1
'''
        
        try:
            with open(batch_script, 'w') as f:
                f.write(script_content)
            
            logger.info(f"Created update script: {batch_script}")
            
            # Start the batch script in a new detached process
            # Use CREATE_NO_WINDOW to hide the console window
            CREATE_NO_WINDOW = 0x08000000
            DETACHED_PROCESS = 0x00000008
            
            subprocess.Popen(
                ['cmd', '/c', batch_script],
                creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
                close_fds=True
            )
            
            logger.info("Update script started, exiting application...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create/run update script: {e}", exc_info=True)
            return False
    
    async def download_and_apply(self, download_url: str) -> bool:
        """
        Download the update and apply it, restarting the application.
        Returns True if the update process was initiated successfully.
        """
        # Download
        new_exe_path = await self.download_update(download_url)
        if not new_exe_path:
            return False
        
        # Apply
        if self.apply_update(new_exe_path):
            # Exit the application to let the updater do its work
            # Give a moment for any UI updates to complete
            await asyncio.sleep(0.5)
            os._exit(0)
            return True
        
        return False


# Global updater instance
updater = Updater()

