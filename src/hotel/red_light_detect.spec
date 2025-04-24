# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['red_light_detect.py'],
    pathex=['C:\\Users\\garyh\\PycharmProjects\\test_tool\\venv\\Lib\\site-packages\\cv2', 'C:\\Users\\garyh\\PycharmProjects\\test_tool\\src\\hotel', 'C:\\Users\\garyh\\PycharmProjects\\test_tool\\venv\\lib\\site-packages',
             'C:\\Users\\garyh\\PycharmProjects\\test_tool\\venv\\Lib\\site-packages'],
    binaries=[],
    datas=[],
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
    name='red_light_detect',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    upx=True,
    upx_exclude=[],
    name='red_light_detect',
)
