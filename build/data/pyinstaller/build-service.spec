# -*- mode: python ; coding: utf-8 -*-
import sys
import pyhtmlgui
try:
    name        = sys.argv[-3]
    root_folder = os.path.abspath(sys.argv[-2])
    script      = os.path.abspath(sys.argv[-1])
except:
    print("args: name, root_folder, script")
    exit(1)


datas = [
    ( os.path.join(root_folder, "gui"       , "default" , "templates"            ) , os.path.join("gui", "default", "templates")),
    ( os.path.join(root_folder, "gui"       , "default" , "static"               ) , os.path.join("gui", "default", "static")),
    ( os.path.join(os.path.split(pyhtmlgui.__file__)[0], "templates")                 , "pyhtmlgui/templates")
]
for locale in ["de", "en"]:
    datas.append(( os.path.join(root_folder, "locales", locale, "LC_MESSAGES") , os.path.join("locales", locale, "LC_MESSAGES")))


a = Analysis(
    [script],
    pathex          = [root_folder],
    binaries        = [],
    datas           = datas,
    hiddenimports   = ["sqlite3"],
    hookspath       = [],
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
    console     = True
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
