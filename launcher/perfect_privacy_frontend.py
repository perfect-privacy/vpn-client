import os, sys
import subprocess

import psutil
from PyQt6.QtCore import Qt
from pyhtmlgui.apps.qt import PyHtmlQtApp, PyHtmlQtTray, PyHtmlQtWindow
from config.config import SHARED_SECRET, PLATFORM, SERVICE_PORT
from config.constants import PLATFORMS
from config.paths import APP_DIR

PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))
CRASHLOG = os.path.join(PROJECT_ROOT_DIRECTORY, "crash.log")


ERROR_PAGE = '''
    <div style="text-align:center;color:gray">
        <h3>
            <br><br>
            Failed to connect to VPN background service  <br><br>
            :( <br><br>
            %s<br><br>
            <button style="cursor: pointer;webkit-user-select: none;user-select: none;border: 1px solid;border-radius: 6px;line-height: 20px;font-size:14px;" 
                onclick="pyhtmlapp.__default_exit_qtapp()">EXIT NOW
            </button><br>
            Retrying in a few seconds <br> <br>            
        </h3>
    </div>
'''

class MainApp():
    def __init__(self):
        errormsg = ""
        if PLATFORM == PLATFORMS.windows:
            success, msg = StartupCheckerWin().check()
            if success is False:
                errormsg = msg
        error_page = ERROR_PAGE % errormsg

        self.icon_path = os.path.join(APP_DIR, "gui", "default", "static", "img", "pp_icon.ico")

        self.app = PyHtmlQtApp(icon_path= self.icon_path)

        self.window = PyHtmlQtWindow(self.app, url="http://127.0.0.1:%s/?token=%s"  % (SERVICE_PORT, SHARED_SECRET), size=[1200, 800], title="Perfect Privacy", icon_path = self.icon_path, error_page=error_page)
        self.window.addJavascriptFunction("exit_app", self.stop)
        self.window.addJavascriptFunction("copy_to_clipboard", PyHtmlQtApp.clipboard().setText)
        self.window.addJavascriptFunction("open_crashlog", self.open_crashlog)

        self.tray = PyHtmlQtTray(self.app, url="http://127.0.0.1:%s/tray?token=%s"  % (SERVICE_PORT, SHARED_SECRET), size=[300,400], icon_path = self.icon_path)
        self.tray.addJavascriptFunction("exit_app", self.stop)
        self.tray.addJavascriptFunction("show_app", self.window.show)

        if PLATFORM == PLATFORMS.macos:
            def confirm_exit():
                self.window.show()
                self.window.runJavascript("confirm_exit()")
            self.window.addMenuButton(["File", "Exit"], confirm_exit)
            self.window.addMenuButton(["File", "Preferences"], lambda x:self.window.runJavascript("eval('window.location.href = \"#preferences\";')"))
            self.window.on_closed_event.attach_observer(self.app.hide_osx_dock)
            self.window.on_show_event.attach_observer(self.app.show_osx_dock)
            self.app.on_activated_event.attach_observer(self.window.show)
        else:
            self.window.on_minimized_event.attach_observer(self.window.hide)
            self.tray.on_left_clicked.attach_observer(self.window.show)
        self.window._webWidget.web.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.tray._webWidget.web.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def run(self):
        self.window.show()
        self.app.run()

    def stop(self, *args):
        self.app.stop()

    def open_crashlog(self, *args):
        crashlog = os.path.join(PROJECT_ROOT_DIRECTORY, "crash.log")
        if PLATFORM == PLATFORMS.macos:  # macOS
            subprocess.call(('open', crashlog))
        elif PLATFORM == PLATFORMS.windows:  # Windows
            os.startfile(crashlog)
        else:  # linux variants
            subprocess.call(('xdg-open', crashlog))

class StartupCheckerWin():

    def check(self):
        msg = self.get_error_msg()
        if msg is None:
            return True, None
        return False, msg

    def check_service_exe(self):
        print(os.path.join(PROJECT_ROOT_DIRECTORY, "perfect-privacy-service.exe"))
        return os.path.exists(os.path.join(PROJECT_ROOT_DIRECTORY, "perfect-privacy-service.exe"))

    def check_service_installed(self):
        try:
            return "status" in psutil.win_service_get("Perfect Privacy VPN").as_dict()
        except:
            return False

    def check_service_running(self):
        try:
            return psutil.win_service_get("Perfect Privacy VPN").as_dict()["status"] == "running"
        except:
            return False

    def get_error_msg(self):
        errormsg = None
        if self.check_service_exe() == False:
            errormsg = "Some installation files are missing, make sure they have not been quarantined by your anti virus software.<br> Please reinstall Perfect Privacy"
        elif self.check_service_installed() == False:
            errormsg = "The VPN background service is not installed, make sure it has not been blocked by your anti virus software.<br> Please reinstall Perfect Privacy"
        elif self.check_service_running() == False:
            if os.path.exists(os.path.join(PROJECT_ROOT_DIRECTORY, "crash.log")):
                errormsg = 'The VPN background service apparently crashed, and left a crash log.<br>' \
                           '<button style="cursor: pointer;webkit-user-select: none;user-select: none;border: 1px solid;border-radius: 6px;line-height: 20px;font-size:14px;" ' \
                           'onclick="pyhtmlapp.open_crashlog()">Open crash.log</button>'

            else:
                errormsg = "The VPN background service is not running, but no reason is apparent. <br>" \
                           "Please try restarting your computer, or reinstall Perfect Privacy.<br>" \
                           "If all else fails, please contact Perfect Privacy support"
        return errormsg


if __name__ == '__main__':
    MainApp().run()
    os._exit(0)
