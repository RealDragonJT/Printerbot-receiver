from escpos.printer import Usb, Dummy
from escpos.exceptions import USBNotFoundError
from typing import Optional
from .config_manager import config_manager
import base64
import io
import requests
import logging
from PIL import Image

logger = logging.getLogger('PrintsAlot.printer')

class PaperError(Exception):
    pass

class PrinterWrapper:
    def __init__(self):
        self.connected = False
        self.printer = None
        self._connect()

    def _connect(self):
        try:
            # TODO: Make VID/PID configurable
            # Default to TM-T88IV (0x04b8, 0x0202)
            logger.info("Attempting to connect to printer (VID=0x04b8, PID=0x0202)")
            self.printer = Usb(0x04b8, 0x0202)
            self.connected = True
            logger.info("Printer connected via USB")
        except USBNotFoundError:
            logger.warning("Printer not found (USB) - using Dummy printer")
            self.connected = False
            self.printer = Dummy() # Fallback to dummy for testing UI
        except Exception as e:
            logger.error(f"Error connecting to printer: {e}", exc_info=True)
            self.connected = False
            self.printer = Dummy()

    def print_image(self, content: str, auto_cut: bool = True):
        """
        Print an image from a URL or Base64 string.
        """
        logger.info(f"Processing print job. Auto cut: {auto_cut}")
        try:
            # Check Paper / Connection by feeding a line
            if self.connected and not isinstance(self.printer, Dummy):
                try:
                    logger.debug("Checking printer connection...")
                    self.printer.text("\n")
                except Exception as e:
                    logger.error(f"Paper check failed: {e}")
                    raise PaperError("Printer is offline or out of paper")

            img = None
            
            # 1. Try as URL
            if content.startswith('http'):
                logger.info(f"Downloading image from {content}...")
                try:
                    response = requests.get(content, timeout=10)
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        logger.info(f"Image downloaded. Size: {img.size}, Mode: {img.mode}")
                    else:
                        logger.error(f"Failed to download image. Status: {response.status_code}")
                except Exception as e:
                    logger.error(f"Failed to download image: {e}", exc_info=True)
            
            # 2. Try as Base64 (Fallback)
            if not img:
                try:
                    logger.info("Trying to decode as Base64...")
                    # Remove header if present
                    if ',' in content:
                        content = content.split(',')[1]
                    img_data = base64.b64decode(content)
                    img = Image.open(io.BytesIO(img_data))
                    logger.info(f"Image decoded from Base64. Size: {img.size}")
                except Exception as e:
                    logger.error(f"Failed to decode base64: {e}", exc_info=True)

            if img:
                # Ensure connected
                if not self.connected or isinstance(self.printer, Dummy):
                    logger.info("Reconnecting to printer...")
                    self._connect()
                
                # Print
                logger.info("Sending image to printer...")
                self.printer.image(img)
                logger.info("Image sent successfully.")
                
                if auto_cut:
                    logger.info("Cutting paper...")
                    self.printer.cut()
                    logger.info("Cut command sent.")
            else:
                logger.error("No valid image found to print")

        except PaperError:
            raise # Re-raise for client to handle
        except Exception as e:
            logger.error(f"Error printing image: {e}", exc_info=True)
            # Try to reconnect for next time
            self.connected = False

printer_wrapper = PrinterWrapper()
