# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('M:/Dev/Workspaces/FileManager/assets', 'assets'), ('M:/Dev/Workspaces/FileManager/nexus_file_manager/nexus/assets/icons', 'nexus/assets/icons'), ('M:/Dev/Workspaces/FileManager/nexus_file_manager/nexus', 'nexus'), ('M:/Dev/Workspaces/FileManager/nexus_file_manager', 'nexus_file_manager'), ('M:/Dev/Workspaces/FileManager/src', 'src')]
binaries = []
hiddenimports = ['nexus', 'nexus_file_manager', 'nexus_file_manager.main', 'nexus.components.splash_screen', 'nexus.core', 'nexus.styles', 'nexus.tokens', 'nexus.views', 'nexus.dialogs', 'psutil', 'cryptography', 'send2trash', 'docx', 'openpyxl', 'win32com', 'win32com.client', 'win32api']
tmp_ret = collect_all('nexus')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('nexus_file_manager')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('docx')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('openpyxl')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['M:/Dev/Workspaces/FileManager/run.py'],
    pathex=['M:/Dev/Workspaces/FileManager', 'M:/Dev/Workspaces/FileManager/nexus_file_manager'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Nexus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['M:/Dev/Workspaces/FileManager/assets/icon.ico'],
)
