# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['oneko.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('theme_orange_cat', 'theme_orange_cat'),
        ('oneko.icns', '.'),
        ('oneko.ico', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'PyQt6.QtSvg',
    ],
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
    name='oneko',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression - can cause issues with Qt
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX compression
    upx_exclude=[],
    name='oneko',
)

app = BUNDLE(
    coll,
    name='Oneko.app',
    icon='oneko.icns',
    bundle_identifier='com.yourname.oneko',
    info_plist={
        'CFBundleName': 'Oneko',
        'CFBundleDisplayName': 'Oneko',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': False,  # Set to False so it appears in dock initially
        'NSHighResolutionCapable': True,
        'LSBackgroundOnly': False,
    },
)