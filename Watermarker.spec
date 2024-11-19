# -*- mode: python ; coding: utf-8 -*-

import sys

block_cipher = None

if sys.platform == 'darwin':
    icon = 'logo.icns'
else:
    icon = 'logo.ico'


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('./fonts', './fonts'), ('./logos', './logos'), ('./exiftool', './exiftool')],
    hiddenimports=[],
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
    name='Watermarker',
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
    icon=[icon]
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Watermarker',
)
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Watermarker.app',
        icon='logo.icns',
        bundle_identifier='dev.fming.watermarker',
    )
