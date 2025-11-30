"""
System tray icon for PrintsAlot Receiver.
Handles background running with tray icon, menu, and auto-start.
"""
import pystray
from pystray import MenuItem as Item
from PIL import Image, ImageDraw
import threading
import webbrowser
import sys
import os

class TrayIcon:
    def __init__(self, port: int = 8080):
        self.port = port
        self.icon = None
        self._stop_event = threading.Event()
        
    def _create_icon_image(self, color='#4CAF50'):
        """Create a simple printer icon."""
        # Create a 64x64 image
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a simple printer shape
        # Main body
        draw.rounded_rectangle([8, 20, 56, 48], radius=4, fill=color)
        # Paper tray (top)
        draw.rectangle([16, 8, 48, 22], fill='#FFFFFF')
        # Paper output (bottom)
        draw.rectangle([16, 46, 48, 58], fill='#FFFFFF')
        # Paper lines
        draw.line([20, 50, 44, 50], fill='#CCCCCC', width=1)
        draw.line([20, 54, 40, 54], fill='#CCCCCC', width=1)
        
        return image
    
    def _open_ui(self, icon=None, item=None):
        """Open the web UI in default browser."""
        webbrowser.open(f'http://localhost:{self.port}')
    
    def _restart_app(self, icon=None, item=None):
        """Restart the application."""
        icon.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    def _quit_app(self, icon=None, item=None):
        """Quit the application."""
        self._stop_event.set()
        icon.stop()
    
    def _on_click(self, icon, item):
        """Handle left-click on tray icon."""
        self._open_ui()
    
    def create_menu(self):
        """Create the right-click context menu."""
        return pystray.Menu(
            Item('Open PrintsAlot', self._open_ui, default=True),
            Item('Restart', self._restart_app),
            pystray.Menu.SEPARATOR,
            Item('Quit', self._quit_app)
        )
    
    def run(self):
        """Run the tray icon (blocking)."""
        self.icon = pystray.Icon(
            'PrintsAlot',
            self._create_icon_image(),
            'PrintsAlot Receiver',
            menu=self.create_menu()
        )
        
        # Set up left-click action
        self.icon.run()
    
    def stop(self):
        """Stop the tray icon."""
        if self.icon:
            self.icon.stop()


def setup_autostart(enable: bool = True):
    """
    Set up or remove Windows autostart registry entry.
    """
    if sys.platform != 'win32':
        print("Autostart is only supported on Windows")
        return False
    
    import winreg
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "PrintsAlotReceiver"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        
        if enable:
            # Get the path to the executable
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                exe_path = sys.executable
            else:
                # Running as script - use pythonw to hide console
                exe_path = f'pythonw "{os.path.abspath(sys.argv[0])}"'
            
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            print(f"Autostart enabled: {exe_path}")
        else:
            try:
                winreg.DeleteValue(key, app_name)
                print("Autostart disabled")
            except FileNotFoundError:
                pass  # Key doesn't exist, nothing to remove
        
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"Failed to modify autostart: {e}")
        return False


def is_autostart_enabled():
    """Check if autostart is currently enabled."""
    if sys.platform != 'win32':
        return False
    
    import winreg
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "PrintsAlotReceiver"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, app_name)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


