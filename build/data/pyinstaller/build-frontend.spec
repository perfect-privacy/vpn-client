# -*- mode: python ; coding: utf-8 -*-
import sys

try:
    name        = sys.argv[-3]
    root_folder = os.path.abspath(sys.argv[-2])
    script      = os.path.abspath(sys.argv[-1])
except:
    print("args: name, root_folder, script")
    exit(1)

a = Analysis(
    [script],
    pathex          = [root_folder],
    binaries        = [],
    datas           = [],
    hiddenimports   = ["sqlite3"],
    hookspath       = [os.path.join(root_folder, "build", "data", "pyinstaller")],
    runtime_hooks   = [],
    excludes        = [],
    win_no_prefer_redirects = False,
    win_private_assemblies  = False,
    cipher          = None,
    noarchive       = False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher      = None
)

exe = EXE(pyz,
    a.scripts,
    [],
    exclude_binaries = True,
    name        = name,
    debug       = False,
    bootloader_ignore_signals = False,
    strip       = False,
    upx         = False,
    console     = False,
    icon        = os.path.join(root_folder, "gui", "default", "static","img","pp_icons.icns")
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip       = False,
    upx         = False,
    upx_exclude = [],
    name        = name
)
