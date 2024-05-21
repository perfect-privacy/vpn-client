import os, sys, platform
from config.config import PLATFORM

if getattr( sys, 'frozen', False ) == True:  # check if we are bundled by pyinstaller
    APP_DIR            = sys._MEIPASS
    APP_THIRDPARTY_DIR = os.path.join(APP_DIR, "thirdparty")
else:
    APP_DIR            = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
    APP_THIRDPARTY_DIR = os.path.join(APP_DIR, "thirdparty", PLATFORM)

APP_VAR_DIR         = os.path.join(APP_DIR, "var")
CONFIG_DIR          = os.path.join(APP_VAR_DIR, "configs")
SOFTWARE_UPDATE_DIR = os.path.join(APP_VAR_DIR, "software_update")
CONFIG_UPDATE_DIR   = os.path.join(APP_VAR_DIR, "config_update")

if not os.path.exists(APP_VAR_DIR):
    os.mkdir(APP_VAR_DIR)

if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)

if not os.path.exists(SOFTWARE_UPDATE_DIR):
    os.mkdir(SOFTWARE_UPDATE_DIR)

if not os.path.exists(CONFIG_UPDATE_DIR):
    os.mkdir(CONFIG_UPDATE_DIR)