from nicegui import ui, app
from .client import printer_client
from .config_manager import config_manager
import asyncio

# Global State
connection_status = "Disconnected"

def update_status_label(label):
    label.text = f"Status: {connection_status}"
    if connection_status == "Connected":
        label.classes('text-green-400')
    else:
        label.classes('text-red-400')

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
        ui.notify('Linked! Refreshing...')
        ui.navigate.to('/')

    printer_client.on('connect', on_connect)
    printer_client.on('disconnect', on_disconnect)
    printer_client.on('welcome', on_welcome)
    printer_client.on('token_issued', on_token_issued)

    # Initialize state from client
    global connection_status
    connection_status = "Connected" if printer_client.connected else "Disconnected"
    
    # UI Layout
    with ui.column().classes('w-full max-w-lg mx-auto mt-10 p-4 gap-4'):
        
        # Header
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('PrintsAlot Receiver').classes('text-2xl font-bold text-primary')
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
                    initial_code = printer_client.pairing_code if printer_client.pairing_code else "Waiting..."
                    code_label = ui.label(initial_code).classes('text-xl font-mono font-bold')
                    
                    async def copy_code():
                        code = code_label.text
                        if code and code != "Waiting...":
                            cmd = f"/printer link {code}"
                            # Use JS for clipboard as it's more reliable in some contexts
                            await ui.run_javascript(f'navigator.clipboard.writeText("{cmd}")')
                            ui.notify(f'Copied: {cmd}')
                    
                    code_row.on('click', copy_code)
                
                ui.label('Click code to copy command').classes('text-xs text-gray-400 mt-1')
            else:
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('Linked').classes('text-green-400 font-bold text-lg')
                    ui.button('Unlink', on_click=lambda: (config_manager.set('token', None), ui.navigate.to('/'))).classes('bg-red-600 text-white')

        # Settings Card
        if token:
            with ui.card().classes('w-full p-4'):
                ui.label('Settings').classes('text-xl font-bold mb-4')
                
                current_settings = config_manager.get('printer_settings', {})
                
                # Inputs
                width_input = ui.number(label='Printer Width (px)', value=current_settings.get('width', 384)).classes('w-full')
                ui.label('Max 800px. Warning: < 350px may break layout.').classes('text-xs text-gray-400 mb-2')
                
                max_prints_input = ui.number(label='Max Prints / Day (Total)', value=current_settings.get('max_prints_per_day', 50)).classes('w-full')
                ui.label('-1 for unlimited').classes('text-xs text-gray-400 mb-2')
                
                max_user_prints_input = ui.number(label='Max Prints / User / Day', value=current_settings.get('max_prints_per_user_per_day', 5)).classes('w-full')
                
                max_height_input = ui.number(label='Max Image Height (px)', value=current_settings.get('max_px_height', 2000)).classes('w-full')
                
                auto_cut_input = ui.checkbox('Auto Cut Paper', value=current_settings.get('auto_cut', True)).classes('mt-2')

                async def save_settings():
                    # Validation
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
                
            ui.separator().classes('my-4')
            ui.button('Launch Zadig (Driver Setup)', on_click=lambda: ui.notify('Launching Zadig...')).classes('w-full bg-gray-700')

        # Footer
        with ui.row().classes('w-full justify-center gap-4 mt-8 text-gray-500 text-sm'):
            ui.label('Powered by PrinterBot')
            ui.link('Command Guide', 'https://printerbot.dragnai.dev/commands').classes('text-primary hover:underline')
            ui.link('Website', 'https://printerbot.dragnai.dev').classes('text-primary hover:underline')

# Start Client in background
app.on_startup(printer_client.connect)
app.on_shutdown(printer_client.disconnect)

ui.run(title="PrintsAlot Receiver", reload=False, dark=True)
