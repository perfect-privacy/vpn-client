import os, sys
import subprocess
import time
import webbrowser

from core.libs.web.reporter import ReporterInstance

PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))

import psutil
try:
    from PyQt6.QtCore import Qt, QTimer
except:
    from PyQt5.QtCore import Qt, QTimer

from pyhtmlgui.apps.qt import PyHtmlQtApp, PyHtmlQtTray, PyHtmlQtWindow
from config.config import SHARED_SECRET, PLATFORM, SERVICE_PORT
from config.constants import PLATFORMS
from config.paths import APP_DIR, SOFTWARE_UPDATE_DIR
from config.files import SOFTWARE_UPDATE_FILENAME

if PLATFORM == PLATFORMS.windows:
    import win32com.shell.shell as shell


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

class AnimatedTrayIcon():
    def __init__(self, tray):
        self._icon_path = os.path.join(APP_DIR, "gui", "default", "static", "icons")
        self._tray = tray
        self._animation_icons = [
            os.path.join(self._icon_path, "pp_icon_10.ico"),
            os.path.join(self._icon_path, "pp_icon_30.ico"),
            os.path.join(self._icon_path, "pp_icon_50.ico"),
            os.path.join(self._icon_path, "pp_icon_70.ico"),
            os.path.join(self._icon_path, "pp_icon_90.ico"),
            os.path.join(self._icon_path, "pp_icon_110.ico"),
            os.path.join(self._icon_path, "pp_icon_130.ico"),
            os.path.join(self._icon_path, "pp_icon_150.ico"),
            os.path.join(self._icon_path, "pp_icon_170.ico"),
            os.path.join(self._icon_path, "pp_icon_190.ico"),
            os.path.join(self._icon_path, "pp_icon_210.ico"),
        ]
        self._current_index = 0
        self._current_direction = -1
        self._current_state = ""
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate_step)

    def set_state(self, state):
        if self._current_state == state:
            return
        self._timer.stop()
        if state == "connected":
            self._tray.set_icon(os.path.join(self._icon_path, "pp_icon.ico"))
        elif state == "disconnected":
            self._tray.set_icon(os.path.join(self._icon_path, "pp_icon_idle.ico"))
        elif state == "working":
            self._current_direction = -1
            self._current_index = 5 if self._current_state == "connected" else 0
            self._timer.start(130)
        self._current_state = state

    def _animate_step(self):
        self._timer.stop()
        if self._current_state == "working":
            self._tray.set_icon(self._animation_icons[self._current_index])
            if self._current_index == 0 or self._current_index == len(self._animation_icons) -1:
                self._current_direction *= -1
            self._current_index += self._current_direction
            self._timer.start(130)

class MainApp():
    def __init__(self):
        try:
            self.minimized = sys.argv[1] == "minimized"
        except:
            self.minimized = False

        errormsg = ""
        self.restart = False
        self.update_on_exit = False

        if PLATFORM == PLATFORMS.windows:
            if StartupCheckerWin().check_service_exe() == False:
                ReporterInstance.report("service_exe_missing", {"was_run_once": SHARED_SECRET != "REPLACE_TOKEN_ON_POST_INSTALL"})
            elif StartupCheckerWin().check_service_installed() == False:
                ReporterInstance.report("service_not_installed", {"was_run_once": SHARED_SECRET != "REPLACE_TOKEN_ON_POST_INSTALL"})
            elif StartupCheckerWin().check_service_running() == False:
                ReporterInstance.report("service_not_running", {"was_run_once": SHARED_SECRET != "REPLACE_TOKEN_ON_POST_INSTALL"})
            success, msg = StartupCheckerWin().check()
            if success is False:
                errormsg = msg
        error_page = ERROR_PAGE % errormsg

        self.icon_path = os.path.join(APP_DIR, "gui", "default", "static", "icons", "pp_icon.ico")

        self.app = PyHtmlQtApp(icon_path= self.icon_path)

        self.window = PyHtmlQtWindow(self.app, url="http://127.0.0.1:%s/?token=%s"  % (SERVICE_PORT, SHARED_SECRET), size=[1200, 800], title="Perfect Privacy", icon_path = self.icon_path, error_page=error_page)
        self.window.addJavascriptFunction("exit_app", self.stop)
        self.window.addJavascriptFunction("exit_app_for_update", self.exit_and_update)
        self.window.addJavascriptFunction("copy_to_clipboard", PyHtmlQtApp.clipboard().setText)
        self.window.addJavascriptFunction("fix_service_as_admin", self.fix_service_as_admin)
        self.window.addJavascriptFunction("open_url", self.open_url)

        self.tray = PyHtmlQtTray(self.app, url="http://127.0.0.1:%s/tray?token=%s"  % (SERVICE_PORT, SHARED_SECRET), size=[300,400], icon_path = self.icon_path, keep_connected_on_close=True)
        self.animatedTrayIcon = AnimatedTrayIcon(self.tray)
        self.tray.addJavascriptFunction("exit_app", self.stop)
        self.tray.addJavascriptFunction("show_app", self.window.show)
        self.tray.addJavascriptFunction("hide_app", self.window.hide)
        self.tray.addJavascriptFunction("set_icon_state", self.animatedTrayIcon.set_state)

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
            #self.window.on_minimized_event.attach_observer(self.window.hide)
            self.tray.on_left_clicked.attach_observer(self.window.show)
        self.window._webWidget.web.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.tray._webWidget.web.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)


    def open_url(self, url):
        webbrowser.open(url)

    def run(self):
        if self.minimized is True:
            self.window.hide()
        else:
            self.window.show()
        self.app.run()
        if self.restart is True:
            os.execv(sys.executable, sys.argv)
        if self.update_on_exit is True:
            update_file = os.path.join(SOFTWARE_UPDATE_DIR, SOFTWARE_UPDATE_FILENAME)
            if os.path.exists(update_file):
                if PLATFORM == PLATFORMS.windows:
                    flags = 0
                    flags |= 0x00000008  # DETACHED_PROCESS
                    flags |= 0x00000200  # CREATE_NEW_PROCESS_GROUP
                    flags |= 0x08000000  # CREATE_NO_WINDOW
                    subprocess.Popen([update_file], close_fds=True, creationflags=flags)
                if PLATFORM == PLATFORMS.macos:
                    os.system("open '%s' & " % update_file)

    def stop(self, *args):
        self.app.stop()

    def exit_and_update(self, *args):
        self.update_on_exit = True
        self.stop()

    def fix_service_as_admin(self, *args):
        if PLATFORM == PLATFORMS.windows:
            if StartupCheckerWin().check_service_installed() == False:
                shell.ShellExecuteEx(lpVerb='runas', lpFile=os.path.join(APP_DIR, "perfect-privacy-service.exe"), lpParameters='--startup auto install')
            shell.ShellExecuteEx(lpVerb='runas', lpFile=os.path.join(APP_DIR, "perfect-privacy-service.exe"), lpParameters='start')
            for _ in range(10):
                if StartupCheckerWin().check_service_running() is True:
                    break
                time.sleep(1)
            if StartupCheckerWin().check_service_installed() == False:
                ReporterInstance.report("service_fix_not_installed","")
            elif StartupCheckerWin().check_service_running() == False:
                ReporterInstance.report("service_fix_not_running", "")
            if SHARED_SECRET == "REPLACE_TOKEN_ON_POST_INSTALL":
                self.restart = True
                self.stop()

class StartupCheckerWin():

    def check(self):
        msg = self.get_error_msg()
        if msg is None:
            return True, None
        return False, msg

    def check_service_exe(self):
        return os.path.exists(os.path.join(APP_DIR, "perfect-privacy-service.exe"))

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
        msg = "If this happens repeatedly, make sure no other security software is blocking our service.<br><br>" \
            '<button style="background-image:linear-gradient(to bottom,#5cb85c 0,#419641 100%);  border-color: #3e8f3e; cursor: pointer;webkit-user-select: none;user-select: none;border: 1px solid;border-radius: 6px;line-height: 20px;font-size:14px;" onclick="pyhtmlapp.fix_service_as_admin()">Repair Background Service (as Admin)</button><br><br>' \
            'If you repair the service, it might take up to 30 seconds to load.<br>'\
            "If all else fails, please contact Perfect Privacy support<br>"
        if self.check_service_exe() == False:
            errormsg = "Some installation files are missing, make sure they have not been quarantined by your anti virus software.<br> Please reinstall Perfect Privacy"
        elif self.check_service_installed() == False:
            errormsg = "The VPN background service is not installed<br>" + msg
        elif self.check_service_running() == False:
            errormsg = "The VPN background service is not running, but no reason is apparent. <br>" + msg
        return errormsg

if __name__ == '__main__':
    MainApp().run()
    os._exit(0)
