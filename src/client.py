import socketio
import asyncio
import aiohttp
import logging
from typing import Optional, Callable
from .config_manager import config_manager

# Current client version
CLIENT_VERSION = "2.0.2"

logger = logging.getLogger('PrintsAlot.client')

class PrinterClient:
    def __init__(self):
        self.sio = socketio.AsyncClient()
        self.connected = False
        self.callbacks = {}
        self._should_reconnect = True
        self._reconnect_task = None
        self._reconnect_delay = 1  # Start with 1 second
        self._max_reconnect_delay = 30  # Max 30 seconds between attempts
        
        # Register events
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('print_job', self._on_print_job)
        self.sio.on('token_issued', self._on_token_issued)
        self.sio.on('token_rotated', self._on_token_rotated)
        self.sio.on('welcome', self._on_welcome)
        
        self.pairing_code = None
        self.is_linked = False

    async def _on_welcome(self, data):
        print(f"Welcome: {data}")
        self.pairing_code = data.get('code')
        self.is_linked = data.get('linked', False)
        if self.callbacks.get('welcome'):
            self.callbacks['welcome'](data)

    async def connect(self):
        if self.sio.connected:
            print("Already connected")
            return

        url = config_manager.get('relay_url')
        token = config_manager.get('token')
        
        # Warn if using HTTP with non-localhost URL
        if url and url.startswith('http://') and 'localhost' not in url and '127.0.0.1' not in url:
            print("⚠️  WARNING: Using HTTP (not HTTPS) for relay URL. Your connection token may be transmitted insecurely!")
        
        auth = {}
        if token:
            auth['token'] = token
            
        # Add settings to auth
        settings = config_manager.get('printer_settings', {})
        # Ensure defaults
        auth.update({
            'timezone': settings.get('timezone', 'UTC'),
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
        """Disconnect and stop reconnection attempts."""
        self._should_reconnect = False
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        if self.sio.connected:
            await self.sio.disconnect()

    async def _on_connect(self):
        self.connected = True
        self._reconnect_delay = 1  # Reset delay on successful connection
        print("Connected to Relay")
        if self.callbacks.get('connect'):
            self.callbacks['connect']()

    async def _on_disconnect(self):
        self.connected = False
        print("Disconnected from Relay")
        if self.callbacks.get('disconnect'):
            self.callbacks['disconnect']()
        
        # Start reconnection if we should
        if self._should_reconnect:
            self._schedule_reconnect()
    
    def _schedule_reconnect(self):
        """Schedule a reconnection attempt with exponential backoff."""
        if self._reconnect_task and not self._reconnect_task.done():
            return  # Already have a pending reconnect
        
        async def reconnect_loop():
            while self._should_reconnect and not self.connected:
                print(f"Attempting to reconnect in {self._reconnect_delay} seconds...")
                await asyncio.sleep(self._reconnect_delay)
                
                if not self._should_reconnect:
                    break
                    
                try:
                    await self.connect()
                    if self.connected:
                        print("Reconnection successful!")
                        break
                except Exception as e:
                    print(f"Reconnection failed: {e}")
                
                # Exponential backoff
                self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
        
        self._reconnect_task = asyncio.create_task(reconnect_loop())

    async def _on_print_job(self, data):
        logger.info(f"Received print job: {data}")
        job_id = data.get('job_id')
        try:
            from .printer import printer_wrapper, PaperError
        except Exception as import_error:
            logger.error(f"Failed to import printer module: {import_error}", exc_info=True)
            if job_id:
                await self.sio.emit('job_update', {
                    'job_id': job_id,
                    'status': 'failed',
                    'reason': 'error'
                })
            return
        
        try:
            content = data.get('content') or data.get('file_url')
            auto_cut = data.get('auto_cut', True)
            
            logger.info(f"Processing job {job_id}, content: {content}, auto_cut: {auto_cut}")
            
            if content:
                # Run in executor to avoid blocking async loop
                logger.info("Sending to printer...")
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, printer_wrapper.print_image, content, auto_cut
                )
                logger.info("Print completed successfully")
                
                # Success
                if job_id:
                    logger.info(f"Sending job_update completed for {job_id}")
                    await self.sio.emit('job_update', {
                        'job_id': job_id,
                        'status': 'completed'
                    })

        except PaperError as e:
            logger.error(f"Paper error: {e}")
            if job_id:
                await self.sio.emit('job_update', {
                    'job_id': job_id,
                    'status': 'failed',
                    'reason': 'out_of_paper'
                })
        except Exception as e:
            logger.error(f"Printing failed: {e}", exc_info=True)
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
            # Trigger callback for UI refresh before reconnecting
            if self.callbacks.get('token_issued'):
                self.callbacks['token_issued'](data)
            # Reconnect with new token
            await self.sio.disconnect()
            await self.connect()
    
    async def _on_token_rotated(self, data):
        """Handle automatic token rotation from server."""
        print(f"Token rotated")
        token = data.get('token')
        if token:
            config_manager.set('token', token)
            # No need to reconnect - just save the new token for next connection

    def on(self, event: str, callback: Callable):
        self.callbacks[event] = callback

    async def update_settings(self, settings):
        if self.connected:
            await self.sio.emit('update_settings', settings)
    
    async def check_for_updates(self) -> dict:
        """
        Check for client updates from the relay server.
        Returns dict with 'update_available', 'latest_version', 'download_url'
        """
        url = config_manager.get('relay_url')
        if not url:
            return {'update_available': False}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/api/version", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        latest = data.get('latest_version', CLIENT_VERSION)
                        download_url = data.get('download_url', '')
                        
                        # Simple version comparison
                        update_available = self._compare_versions(CLIENT_VERSION, latest)
                        is_prerelease = self._compare_versions(latest, CLIENT_VERSION)  # True if current > latest
                        github_url = data.get('github_url', '')
                        
                        return {
                            'update_available': update_available,
                            'is_prerelease': is_prerelease,
                            'current_version': CLIENT_VERSION,
                            'latest_version': latest,
                            'download_url': download_url,
                            'github_url': github_url
                        }
        except Exception as e:
            print(f"Update check failed: {e}")
        
        return {'update_available': False, 'current_version': CLIENT_VERSION}
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """Compare version strings. Returns True if latest > current."""
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            # Pad with zeros if needed
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            
            return latest_parts > current_parts
        except:
            return False

printer_client = PrinterClient()
