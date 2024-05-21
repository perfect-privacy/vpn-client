from config.config import SHARED_SECRET, FRONTEND_AUTORELOAD, SERVICE_PORT
from pyhtmlgui import PyHtmlGui
from pyhtmlgui import PyHtmlView
import os, sys

from gui.default.views.trayview import TrayView


def getPyHtmlGuiInstance( appInstance, frontend = "default", on_frontend_exit = None, on_frontend_ready = None, listen_port=SERVICE_PORT):
    if frontend == "default":
        from gui.default import MainView
    elif frontend == "privacypi":
        from gui.privacypi import MainView
    else:
        raise Exception("unknown frontend '%s'" % frontend)

    if getattr(sys, 'frozen', False) == True:  # check if we are bundled by pyinstaller
        gui_dir = os.path.join(sys._MEIPASS, "gui")
    else:
        gui_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))

    gui =  PyHtmlGui(
        view_class        = MainView,
        app_instance      = appInstance,
        static_dir        = os.path.join(gui_dir, frontend, "static"),
        template_dir      = os.path.join(gui_dir, frontend, "templates"),
        base_template     = "main.html",
        shared_secret     = SHARED_SECRET,
        listen_port       = listen_port,
        auto_reload       = FRONTEND_AUTORELOAD,
        on_view_disconnected  = on_frontend_exit,
        on_view_connected = on_frontend_ready,
        single_instance   = True,
    )

    gui.add_endpoint(
        app_instance    = appInstance,
        view_class      = TrayView,
        name            = "tray",
        base_template   = "tray.html",
        single_instance = True,
        on_view_connected=on_frontend_ready,
    )
    return gui
