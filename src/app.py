"""
Main entry point for PrintsAlot Receiver.
Runs the NiceGUI web interface with system tray icon.
"""
# CRITICAL: Fix stdout/stderr BEFORE any other imports
# uvicorn/logging checks sys.stdout.isatty() which fails if stdout is None
import sys
import os

if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if sys.stdin is None:
    sys.stdin = open(os.devnull, 'r')

# Now safe to import everything else
import threading
import asyncio
import logging

# Set up file logging for debugging (especially useful when running without console)
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'printsalot.log')
if getattr(sys, 'frozen', False):
    # Running as compiled exe - log next to exe
    LOG_FILE = os.path.join(os.path.dirname(sys.executable), 'printsalot.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
    ]
)
logger = logging.getLogger('PrintsAlot')
logger.info("PrintsAlot starting...")

# Add src to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nicegui import ui, app
from src.client import printer_client, CLIENT_VERSION
from src.config_manager import config_manager
from src.tray import TrayIcon, setup_autostart, is_autostart_enabled

# Default port for the web UI
WEB_PORT = 8456

# Global State
connection_status = "Disconnected"
pending_refresh = False
update_info = None


def update_status_label(label):
    label.text = f"Status: {connection_status}"
    if connection_status == "Connected":
        label.classes('text-green-400', remove='text-red-400')
    else:
        label.classes('text-red-400', remove='text-green-400')


@ui.page('/')
async def main_page():
    ui.dark_mode().enable()
    
    # Setup Client Callbacks
    def on_connect():
        global connection_status
        connection_status = "Connected"
        if 'status_label' in globals() and status_label:
            update_status_label(status_label)
        
    def on_disconnect():
        global connection_status
        connection_status = "Disconnected"
        if 'status_label' in globals() and status_label:
            update_status_label(status_label)

    def on_welcome(data):
        code = data.get('code')
        if 'code_label' in globals() and code_label:
            code_label.text = code

    def on_token_issued(data):
        global pending_refresh
        pending_refresh = True
        print("Token issued callback triggered, setting pending_refresh")

    printer_client.on('connect', on_connect)
    printer_client.on('disconnect', on_disconnect)
    printer_client.on('welcome', on_welcome)
    printer_client.on('token_issued', on_token_issued)

    # Check for pending refresh (from token_issued event)
    async def check_refresh():
        global pending_refresh
        if pending_refresh:
            pending_refresh = False
            ui.notify('Linked successfully!', type='positive')
            await asyncio.sleep(1)
            await ui.run_javascript('window.location.reload()')
    
    # Poll for refresh flag every 500ms
    ui.timer(0.5, check_refresh)

    # Initialize state from client
    global connection_status
    connection_status = "Connected" if printer_client.connected else "Disconnected"
    
    # Check for updates on page load
    global update_info
    update_info = await printer_client.check_for_updates()
    
    # UI Layout
    with ui.column().classes('w-full max-w-lg mx-auto mt-10 p-4 gap-4'):
        
        # Update Banner (if available)
        if update_info and update_info.get('update_available'):
            with ui.card().classes('w-full p-3 bg-yellow-900 border border-yellow-600'):
                with ui.row().classes('w-full items-center justify-between'):
                    with ui.column().classes('gap-0'):
                        ui.label('🔄 Update Available!').classes('text-yellow-400 font-bold')
                        ui.label(f"v{update_info.get('current_version', '?')} → v{update_info.get('latest_version', '?')}").classes('text-yellow-200 text-sm')
                    ui.link('Download', update_info.get('download_url', '#')).classes('bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-500')
        
        # Header
        with ui.row().classes('w-full justify-between items-center'):
            with ui.row().classes('items-center gap-2'):
                ui.label('PrintsAlot Receiver').classes('text-2xl font-bold text-primary')
                ui.label(f'v{CLIENT_VERSION}').classes('text-xs text-gray-500')
            global status_label
            status_label = ui.label(f"Status: {connection_status}").classes('text-lg font-bold')
            update_status_label(status_label)

        # Connection Card
        with ui.card().classes('w-full p-4'):
            ui.label('Connection').classes('text-xl font-bold mb-2')
            
            token = config_manager.get('token')
            if not token:
                ui.label('Not Linked').classes('text-red-400 font-bold mb-2')
                
                with ui.row().classes('items-center gap-2 bg-gray-800 p-3 rounded cursor-pointer hover:bg-gray-700 transition-colors') as code_row:
                    ui.icon('content_copy', size='sm')
                    global code_label
                    initial_code = printer_client.pairing_code if printer_client.pairing_code else "XXXX-XXXX"
                    code_label = ui.label(initial_code).classes('text-2xl font-mono font-bold tracking-wider')
                    
                    async def copy_code():
                        code = code_label.text
                        if code and code != "XXXX-XXXX":
                            cmd = f"/printer link {code}"
                            import json
                            safe_cmd = json.dumps(cmd)
                            await ui.run_javascript(f'navigator.clipboard.writeText({safe_cmd})')
                            ui.notify(f'Copied: {cmd}')
                    
                    code_row.on('click', copy_code)
                
                ui.label('Code expires in 15 minutes • Click to copy command').classes('text-xs text-gray-400 mt-1')
            else:
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('Linked').classes('text-green-400 font-bold text-lg')
                    ui.button('Unlink', on_click=lambda: (config_manager.set('token', None), ui.navigate.to('/'))).classes('bg-red-600 text-white')

        # Settings Card
        if token:
            with ui.card().classes('w-full p-4'):
                ui.label('Settings').classes('text-xl font-bold mb-4')
                
                current_settings = config_manager.get('printer_settings', {})
                
                width_input = ui.number(label='Printer Width (px)', value=current_settings.get('width', 384)).classes('w-full')
                ui.label('Max 800px. Warning: < 350px may break layout.').classes('text-xs text-gray-400 mb-2')
                
                max_prints_input = ui.number(label='Max Prints / Day (Total)', value=current_settings.get('max_prints_per_day', 50)).classes('w-full')
                ui.label('-1 for unlimited').classes('text-xs text-gray-400 mb-2')
                
                max_user_prints_input = ui.number(label='Max Prints / User / Day', value=current_settings.get('max_prints_per_user_per_day', 5)).classes('w-full')
                
                max_height_input = ui.number(label='Max Image Height (px)', value=current_settings.get('max_px_height', 2000)).classes('w-full')
                
                auto_cut_input = ui.checkbox('Auto Cut Paper', value=current_settings.get('auto_cut', True)).classes('mt-2')

                async def save_settings():
                    try:
                        width = int(width_input.value)
                        if width > 800:
                            width = 800
                            width_input.value = 800
                            ui.notify('Width capped at 800px', type='warning')
                        if width < 350:
                            ui.notify('Warning: Width < 350px may cause layout issues', type='warning')
                            
                        max_prints = int(max_prints_input.value)
                        
                        new_settings = {
                            'width': width,
                            'max_prints_per_day': max_prints,
                            'max_prints_per_user_per_day': int(max_user_prints_input.value),
                            'max_px_height': int(max_height_input.value),
                            'auto_cut': auto_cut_input.value
                        }
                        
                        config_manager.set('printer_settings', new_settings)
                        await printer_client.update_settings(new_settings)
                        ui.notify('Settings Saved!', type='positive')
                    except Exception as e:
                        ui.notify(f'Error saving settings: {e}', type='negative')

                ui.button('Save Settings', on_click=save_settings).classes('w-full mt-4 bg-primary text-white')
            
            # Autostart toggle
            with ui.card().classes('w-full p-4'):
                ui.label('System').classes('text-xl font-bold mb-4')
                
                autostart_enabled = is_autostart_enabled()
                autostart_checkbox = ui.checkbox('Start with Windows', value=autostart_enabled).classes('w-full')
                
                def toggle_autostart():
                    setup_autostart(autostart_checkbox.value)
                    if autostart_checkbox.value:
                        ui.notify('Autostart enabled', type='positive')
                    else:
                        ui.notify('Autostart disabled', type='info')
                
                autostart_checkbox.on('change', toggle_autostart)

        # Footer
        with ui.row().classes('w-full justify-center gap-4 mt-8 text-gray-500 text-sm'):
            ui.label('Powered by PrinterBot')
            ui.link('Command Guide', 'https://printerbot.dragnai.dev/commands').classes('text-primary hover:underline')
            ui.link('Website', 'https://printerbot.dragnai.dev').classes('text-primary hover:underline')


def run_tray(port: int):
    """Run the system tray icon in a separate thread."""
    tray = TrayIcon(port=port)
    tray.run()


def run_setup_dialog():
    """Show a GUI dialog for first-time setup."""
    import ctypes
    
    # Use Windows MessageBox for setup dialog
    MB_YESNO = 0x04
    MB_ICONQUESTION = 0x20
    IDYES = 6
    
    result = ctypes.windll.user32.MessageBoxW(
        0,
        "Would you like PrintsAlot to start automatically when Windows starts?\n\n"
        "You can change this later in the app settings.",
        "PrintsAlot Setup",
        MB_YESNO | MB_ICONQUESTION
    )
    
    if result == IDYES:
        if setup_autostart(True):
            ctypes.windll.user32.MessageBoxW(
                0,
                "Autostart enabled!\n\nPrintsAlot will now start with Windows.",
                "Setup Complete",
                0x40  # MB_ICONINFORMATION
            )
        else:
            ctypes.windll.user32.MessageBoxW(
                0,
                "Failed to enable autostart.\n\nYou can try again from the app settings.",
                "Setup Error",
                0x10  # MB_ICONERROR
            )
    else:
        ctypes.windll.user32.MessageBoxW(
            0,
            "Autostart not enabled.\n\nYou can enable it later in the app settings.",
            "Setup Complete",
            0x40  # MB_ICONINFORMATION
        )


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='PrintsAlot Receiver')
    parser.add_argument('--setup', action='store_true', help='Run first-time setup')
    parser.add_argument('--no-tray', action='store_true', help='Run without system tray')
    parser.add_argument('--port', type=int, default=WEB_PORT, help=f'Web UI port (default: {WEB_PORT})')
    args = parser.parse_args()
    
    # First-time setup (uses GUI dialog, works without console)
    if args.setup:
        run_setup_dialog()
    
    # Start printer client connection
    app.on_startup(printer_client.connect)
    app.on_shutdown(printer_client.disconnect)
    
    # Start tray icon in background thread (unless disabled)
    if not args.no_tray:
        tray_thread = threading.Thread(target=run_tray, args=(args.port,), daemon=True)
        tray_thread.start()
    
    # Run NiceGUI (this blocks)
    ui.run(
        title="PrintsAlot Receiver",
        port=args.port,
        reload=False,
        dark=True,
        show=False,  # Don't auto-open browser (tray handles this)
    )


if __name__ == "__main__":
    main()

