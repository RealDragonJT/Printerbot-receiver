# PrintsAlot V2 Receiver

The desktop receiver application for PrinterBot V2. This app connects your local thermal printer to the PrinterBot Relay server, allowing you to print from Discord.

## Quick Start (Pre-built Executable)

1. Download the latest `PrintsAlot.exe` from [Releases](https://github.com/RealDragonJT/Printerbot-receiver/releases)
2. Run the installer or extract to a folder
3. Run `PrintsAlot.exe --setup` for first-time setup
4. The app will run in the background (check system tray)

## Features

- **System Tray**: Runs quietly in background, accessible from system tray
- **Auto-Start**: Optional Windows startup integration
- **Auto-Reconnect**: Automatically reconnects if server restarts
- **Update Checker**: Notifies you when updates are available

## Prerequisites (For Building)

*   **Python 3.10+**
*   **Thermal Printer** (USB)
*   **Zadig** (for installing WinUSB driver)

## Building from Source

### Option 1: Build Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/RealDragonJT/Printerbot-receiver.git
cd Printerbot-receiver

# Run the build script
build.bat
```

This will create `dist/PrintsAlot.exe`.

### Option 2: Manual Build

```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create icon (optional)
python create_icon.py

# Build exe
pyinstaller PrintsAlot.spec
```

## Installation

### From Pre-built Executable

1. Run `install.bat` after building, or manually:
2. Copy `PrintsAlot.exe` to a permanent location
3. Run `PrintsAlot.exe --setup` to configure autostart

### Development Mode

```bash
# Activate venv
.\venv\Scripts\activate

# Run with visible console (for debugging)
python -m src.app --no-tray

# Or run the original main.py
python -m src.main
```

## Driver Setup (Zadig)

1. Download and run [Zadig](https://zadig.akeo.ie/)
2. Options > List All Devices
3. Select your printer from the dropdown
4. Ensure the target driver is **LibUsbK**
5. Click "Replace Driver" or "Install Driver"

## Configuration

### Config File

Settings are stored in `config.json`:
```json
{
    "token": "your-printer-token",
    "printer_settings": {
        "width": 384,
        "max_prints_per_day": 50,
        "max_prints_per_user_per_day": 5,
        "max_px_height": 2000,
        "auto_cut": true
    },
    "relay_url": "https://printerbot.dragnai.dev"
}
```

## Usage

1. The app runs in the system tray (hidden icons area)
2. **Left-click** the tray icon to open the web UI
3. **Right-click** for menu: Open, Restart, Quit
4. If not linked, copy the **Pairing Code** from the UI
5. In Discord, run: `!printer link <code>` or `/printer link <code>`
6. Configure your printer settings in the web UI

## Command Line Options

```
PrintsAlot.exe [options]

Options:
  --setup     Run first-time setup (configure autostart)
  --no-tray   Run without system tray (shows browser)
  --port N    Use custom port for web UI (default: 8456)
```

## Troubleshooting

*   **"Printer not found"**: Ensure the printer is on, connected via USB, and the WinUSB driver is installed via Zadig.
*   **"Connection failed"**: Check your internet connection and ensure the relay URL is correct.
*   **App not in tray**: Check "Show hidden icons" in taskbar. The app might be running but hidden.
*   **Autostart not working**: Run the app with `--setup` again or toggle it in the Settings UI.

## Version History

- **v2.0.1**: Added system tray, autostart, update checker, reconnection logic
- **v2.0.0**: Initial v2 release with NiceGUI interface
