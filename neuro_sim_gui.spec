# -*- mode: python ; coding: utf-8 -*-
"""Specyfikacja PyInstaller dla aplikacji NeuroSim GUI.

Buduje paczkę w trybie katalogu (--onedir), co zapewnia szybszy start
i pełną kompatybilność z bibliotekami Qt/PySide6.

Budowanie:
    python scripts/build_exe.py

lub bezpośrednio:
    pyinstaller --clean --noconfirm neuro_sim_gui.spec

Wyniki trafiają do katalogu dist/NeuroSim/.
"""

block_cipher = None

a = Analysis(
    ["main_gui.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("configs", "configs"),
        ("assets/svg", "assets/svg"),
        ("data/atlases", "data/atlases"),
        ("data/connectomes", "data/connectomes"),
        ("data/validation", "data/validation"),
    ],
    hiddenimports=[
        "brain_model",
        "brain_model.gui",
        "brain_model.qt_app",
        "brain_model.qt_config",
        "brain_model.qt_plotting",
        "brain_model.qt_results",
        "brain_model.qt_runner",
        "brain_model.qt_sections",
        "brain_model.qt_state",
        "brain_model.qt_styles",
        "brain_model.scenarios",
        "brain_model.scenarios.library",
        "brain_model.scenarios.types",
        "brain_core",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtSvg",
        "matplotlib.backends.backend_qtagg",
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
    name="NeuroSim",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="NeuroSim",
)
