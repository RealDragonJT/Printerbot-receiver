import socketio
import asyncio
from typing import Optional, Callable
from .config_manager import config_manager

class PrinterClient:
    def __init__(self):
        self.sio = socketio.AsyncClient()
        self.connected = False
        self.callbacks = {}
        
        # Register events
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('print_job', self._on_print_job)
        self.sio.on('token_issued', self._on_token_issued)
        self.sio.on('welcome', self._on_welcome)
        
        self.pairing_code = None

    async def _on_welcome(self, data):
        print(f"Welcome: {data}")
        self.pairing_code = data.get('code')
        if self.callbacks.get('welcome'):
            self.callbacks['welcome'](data)

    async def connect(self):
        if self.sio.connected:
            print("Already connected")
            return

        url = config_manager.get('relay_url')
        token = config_manager.get('token')
        
        auth = {}
        if token:
            auth['token'] = token
            
        # Add settings to auth
        settings = config_manager.get('printer_settings', {})
        # Ensure defaults
        auth.update({
            'width': settings.get('width', 384),
            'max_prints_per_day': settings.get('max_prints_per_day', 50),
            'max_prints_per_user_per_day': settings.get('max_prints_per_user_per_day', 5),
            'max_px_height': settings.get('max_px_height', 2000),
            'max_attachments': settings.get('max_attachments', 1),
            'auto_cut': settings.get('auto_cut', True)
        })
            
        try:
            # Force websocket transport to avoid polling issues
            await self.sio.connect(url, auth=auth, transports=['websocket'])
        except Exception as e:
            print(f"Connection failed: {e}")

    async def disconnect(self):
        if self.sio.connected:
            await self.sio.disconnect()

    async def _on_connect(self):
        self.connected = True
        print("Connected to Relay")
        if self.callbacks.get('connect'):
            self.callbacks['connect']()

    async def _on_disconnect(self):
        self.connected = False
        print("Disconnected from Relay")
        if self.callbacks.get('disconnect'):
            self.callbacks['disconnect']()

    async def _on_print_job(self, data):
        print(f"Received print job: {data}")
        try:
            from .printer import printer_wrapper, PaperError
            content = data.get('content') or data.get('file_url')
            auto_cut = data.get('auto_cut', True)
            job_id = data.get('job_id')
            
            if content:
                # Run in executor to avoid blocking async loop
                await asyncio.get_event_loop().run_in_executor(
                    None, printer_wrapper.print_image, content, auto_cut
                )
                
                # Success
                if job_id:
                    await self.sio.emit('job_update', {
                        'job_id': job_id,
                        'status': 'completed'
                    })

        except PaperError:
            print("Out of paper or printer offline")
            if job_id:
                await self.sio.emit('job_update', {
                    'job_id': job_id,
                    'status': 'failed',
                    'reason': 'out_of_paper'
                })
        except Exception as e:
            print(f"Printing failed: {e}")
            if job_id:
                await self.sio.emit('job_update', {
                    'job_id': job_id,
                    'status': 'failed',
                    'reason': 'error'
                })
            
        if self.callbacks.get('print_job'):
            self.callbacks['print_job'](data)

    async def _on_token_issued(self, data):
        print(f"Token issued: {data}")
        token = data.get('token')
        if token:
            config_manager.set('token', token)
            # Reconnect with new token
            await self.sio.disconnect()
            await self.connect()

    def on(self, event: str, callback: Callable):
        self.callbacks[event] = callback

    async def update_settings(self, settings):
        if self.connected:
            await self.sio.emit('update_settings', settings)

printer_client = PrinterClient()
