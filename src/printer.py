from escpos.printer import Usb, Dummy
from escpos.exceptions import USBNotFoundError
from typing import Optional
from escpos.printer import Usb, Dummy
from escpos.exceptions import USBNotFoundError
from typing import Optional
from .config_manager import config_manager
import base64
import io
import requests
from PIL import Image

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
            self.printer = Usb(0x04b8, 0x0202)
            self.connected = True
            print("Printer connected via USB")
        except USBNotFoundError:
            print("Printer not found (USB)")
            self.connected = False
            self.printer = Dummy() # Fallback to dummy for testing UI
        except Exception as e:
            print(f"Error connecting to printer: {e}")
            self.connected = False
            self.printer = Dummy()

    def print_image(self, content: str, auto_cut: bool = True):
        """
        Print an image from a URL or Base64 string.
        """
        print(f"Processing print job. Auto cut: {auto_cut}")
        try:
            # Check Paper / Connection by feeding a line
            if self.connected and not isinstance(self.printer, Dummy):
                try:
                    self.printer.text("\n")
                except Exception as e:
                    print(f"Paper check failed: {e}")
                    raise PaperError("Printer is offline or out of paper")

            img = None
            
            # 1. Try as URL
            if content.startswith('http'):
                print(f"Downloading image from {content}...")
                try:
                    response = requests.get(content, timeout=10)
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        print(f"Image downloaded. Size: {img.size}, Mode: {img.mode}")
                    else:
                        print(f"Failed to download image. Status: {response.status_code}")
                except Exception as e:
                    print(f"Failed to download image: {e}")
            
            # 2. Try as Base64 (Fallback)
            if not img:
                try:
                    # Remove header if present
                    if ',' in content:
                        content = content.split(',')[1]
                    img_data = base64.b64decode(content)
                    img = Image.open(io.BytesIO(img_data))
                    print(f"Image decoded from Base64. Size: {img.size}")
                except Exception as e:
                    print(f"Failed to decode base64: {e}")

            if img:
                # Ensure connected
                if not self.connected or isinstance(self.printer, Dummy):
                    print("Connecting to printer...")
                    self._connect()
                
                # Print
                print("Sending image to printer...")
                self.printer.image(img)
                print("Image sent.")
                
                if auto_cut:
                    print("Cutting paper...")
                    self.printer.cut()
                    print("Cut command sent.")
            else:
                print("No valid image found to print")

        except PaperError:
            raise # Re-raise for client to handle
        except Exception as e:
            print(f"Error printing image: {e}")
            # Try to reconnect for next time
            self.connected = False

printer_wrapper = PrinterWrapper()
