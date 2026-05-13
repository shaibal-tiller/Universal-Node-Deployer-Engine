# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# Detect platform
is_mac = sys.platform == 'darwin'
is_win = sys.platform == 'win32'

added_files = [
    ('README.md', '.'),
    ('assets/icon.png', 'assets'),
]

icon_file = None
if is_mac:
    icon_file = 'assets/icon.icns'
elif is_win:
    icon_file = 'assets/icon.ico'

a = Analysis(
    ['Universal-App-Deployer.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['psutil', 'tkhtmlview', 'markdown2'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    [],
    exclude_binaries=True,
    name='Universal Deployer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Universal Deployer',
)

if is_mac:
    app = BUNDLE(
        coll,
        name='Universal Deployer.app',
        icon='assets/icon.icns',
        bundle_identifier='com.shaibal.universaldeployer',
    )
