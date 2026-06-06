# -*- mode: python ; coding: utf-8 -*-
# Configuración PyInstaller para el CRM.
# MODO CARPETA (one-dir), NO one-file: arranque más rápido y muchos menos
# falsos positivos de antivirus.
# Construir SIEMPRE desde un venv limpio, NUNCA desde conda/miniforge.

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'anthropic',
        'webview',
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
    exclude_binaries=True,        # modo carpeta
    name='CRM-Prospectos',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                    # UPX puede aumentar flags de AV; desactivado
    console=False,                # SIN consola: experiencia de app nativa
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/icon.ico',       # añade tu icono aquí (opcional pero recomendado)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CRM-Prospectos',        # salida: dist/CRM-Prospectos/
)
