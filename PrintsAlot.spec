# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PrintsAlot Receiver.
Builds a single exe that runs in background with system tray.
"""
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Collect escpos data files (capabilities.json)
escpos_datas = collect_data_files('escpos')

a = Analysis(
    ['src/app.py'],
    pathex=[],
    binaries=[],
    datas=escpos_datas,
    hiddenimports=[
        'nicegui',
        'socketio',
        'engineio',
        'pystray',
        'PIL',
        'aiohttp',
        'escpos',
        'usb',
        'usb.core',
        'usb.util',
        'usb.backend',
        'usb.backend.libusb1',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_stdio.py'],  # Fix stdout/stderr FIRST
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PrintsAlot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window!
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

