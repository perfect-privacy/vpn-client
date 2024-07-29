import os, sys
import platform
import subprocess
import time
import webbrowser
from shlex import quote
import socket
import threading


PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.insert(0, PROJECT_ROOT_DIRECTORY)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT_DIRECTORY))

from core.libs.web.reporter import ReporterInstance

import psutil
try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6 import QtCore
    from PyQt6.QtGui import QAction
except:
    from PyQt5 import QtWidgets, QtCore
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *




from pyhtmlgui.apps.qt import PyHtmlQtApp, PyHtmlQtTray, PyHtmlQtWindow, PyHtmlQtSimpleTray
from config.config import SHARED_SECRET, PLATFORM, SERVICE_PORT, FRONTEND_PORT
from config.constants import PLATFORMS
from config.paths import APP_DIR, SOFTWARE_UPDATE_DIR
from config.files import SOFTWARE_UPDATE_FILENAME

if PLATFORM == PLATFORMS.windows:
    import win32com.shell.shell as shell


ERROR_PAGE = '''
    <div style="text-align:center;color:gray">
        <h3>
            <br><br>
            Verbindung zum VPN-Hintergrunddienst fehlgeschlagen  <br><br>
            :( <br><br>
            %s<br><br>
            <button style="cursor: pointer;webkit-user-select: none;user-select: none;border: 1px solid;border-radius: 6px;line-height: 20px;font-size:14px;" 
                onclick="pyhtmlapp.__default_exit_qtapp()">EXIT NOW
            </button><br>
            Erneuter Versuch in ein paar Sekunden <br> <br>            
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
        last_state = self._current_state
        self._current_state = state
        if state == "connected":
            self._tray.set_icon(os.path.join(self._icon_path, "pp_icon.ico"))
        elif state == "disconnected":
            self._tray.set_icon(os.path.join(self._icon_path, "pp_icon_idle.ico"))
        elif state == "working":
            self._current_direction = -1
            self._current_index = 5 if last_state == "connected" else 0
            self._timer.start(150)

    def _animate_step(self):
        self._timer.stop()
        if self._current_state == "working":
            self._tray.set_icon(self._animation_icons[self._current_index])
            if self._current_index == 0 or self._current_index == len(self._animation_icons) -1:
                self._current_direction *= -1
            self._current_index += self._current_direction
            if self._current_state == "working":
                self._timer.start(150)

class FrontendLock(QtCore.QThread):
    signal = QtCore.pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lock_thread = threading.Thread(target=self._start_lock_server, daemon=True)

    def aquire(self):
        try:
            self.server.bind(('localhost', FRONTEND_PORT))
            self.server.listen(5)
            self.lock_thread.start()
            return True
        except Exception as e:
            print("Failed to aquire", e)
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.connect(('localhost', FRONTEND_PORT))
                client.send(("%s:show_main_window" % SHARED_SECRET).encode("utf-8"))
                client.close()
            except:
                pass
            return False

    def release(self):
        try:
            self.lock_thread = None
            self.server.close()
        except:
            pass

    def _start_lock_server(self):
        while self.lock_thread is not None:
            try:
                client_socket, addr = self.server.accept()
                request = client_socket.recv(1024)
                client_socket.close()
                request = request.decode("utf-8")
                print("received,", request)
                if request.startswith(SHARED_SECRET):
                    secret, command = request.split(":",1)
                    self.signal.emit(command)
            except:
                pass


class MainApp():
    def __init__(self):

        try:
            self.minimized = sys.argv[1] == "minimized"
        except:
            self.minimized = False

        errormsg = '<button style="background-image:linear-gradient(to bottom,#5cb85c 0,#419641 100%);  border-color: #3e8f3e; cursor: pointer;webkit-user-select: none;user-select: none;border: 1px solid;border-radius: 6px;line-height: 20px;font-size:14px;" onclick="pyhtmlapp.fix_service_as_admin()">Versuche, den Hintergrunddienst zu reparieren (als Admin)</button><br>'
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

        self.app = PyHtmlQtApp(icon_path= self.icon_path, arg=sys.argv)

        self.window = PyHtmlQtWindow(self.app, url="http://127.0.0.1:%s/?token=%s"  % (SERVICE_PORT, SHARED_SECRET), size=[1200, 800], title="Perfect Privacy", icon_path = self.icon_path, error_page=error_page)
        self.window.addJavascriptFunction("exit_app", self.stop)
        self.window.addJavascriptFunction("exit_app_for_update", self.exit_and_update)
        self.window.addJavascriptFunction("copy_to_clipboard", PyHtmlQtApp.clipboard().setText)
        self.window.addJavascriptFunction("fix_service_as_admin", self.fix_service_as_admin)
        self.window.addJavascriptFunction("open_url", self.open_url)

        if PLATFORM == PLATFORMS.linux:
            self.tray = PyHtmlQtSimpleTray(self.app, icon_path=self.icon_path)
            submenu = self.tray._get_submenu([])
            action = QAction(parent=submenu, text="Show Perfect Privacy")
            action.triggered.connect(self.window.show)
            submenu.addAction(action)
            action1 = QAction(parent=submenu, text="Exit App")
            action1.triggered.connect(self.confirm_exit)
            submenu.addAction(action1)
        else:
            self.tray = PyHtmlQtTray(self.app, url="http://127.0.0.1:%s/tray?token=%s"  % (SERVICE_PORT, SHARED_SECRET), size=[300,400], icon_path = self.icon_path, keep_connected_on_close=True)

        self.animatedTrayIcon = AnimatedTrayIcon(self.tray)
        if PLATFORM != PLATFORMS.linux:
            self.tray.addJavascriptFunction("exit_app", self.stop)
            self.tray.addJavascriptFunction("show_app", self.window.show)
            self.tray.addJavascriptFunction("hide_app", self.window.hide)

        if PLATFORM == PLATFORMS.macos:
            self.window.addMenuButton(["File", "Exit"], self.confirm_exit)
            self.window.addMenuButton(["File", "Preferences"], lambda x:self.window.runJavascript("eval('window.location.href = \"#preferences\";')"))
            self.window.on_closed_event.attach_observer(self.app.hide_osx_dock)
            self.window.on_show_event.attach_observer(self.app.show_osx_dock)
            self.app.on_activated_event.attach_observer(self.window.show)
            if platform.processor() == "arm": # just fixes for flickering webview
                self.window.on_show_event.attach_observer(self.hide_tray_menu)  # on osx arm hide tray menu if window is show, because for some reason the webview will flicker white if its visible more than once
                self.window.on_closed_event.attach_observer(self.load_tray_page) # load tray page if main window is hidden so tray icon stays updated
                self.tray.on_show_event.attach_observer(self.tray._webWidget.load_page)
                self.tray.on_closed_event.attach_observer(self.on_tray_close)
        else:
            self.tray.on_left_clicked.attach_observer(self.window.show)

        self.window._webWidget.web.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        if PLATFORM != PLATFORMS.linux:
            self.tray._webWidget.web.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

    def confirm_exit(self):
        try:
            self.window.on_show_event.detach_observer(self._confirm_exit_js)
        except:
            pass
        if self.window._qMainWindow.isVisible():
            self.window.runJavascript("confirm_exit()")
        else:
            self.window.on_show_event.attach_observer(self._confirm_exit_js)
        self.window.show()

    def _confirm_exit_js(self):
        try:
            self.window.on_show_event.detach_observer(self._confirm_exit_js)
        except:
            pass
        QTimer().singleShot(750, lambda:self.window.runJavascript("confirm_exit()"))


    def on_signal_received(self, command):
        if command == "show_main_window":
            self.window.show()
        elif command.startswith("set_icon_state"):
            command, state = command.split(":", 1)
            self.animatedTrayIcon.set_state(state)

    # on osx arm hide tray menu if window is show, because for some reason the webview will flicker white if its visible more than once
    def hide_tray_menu(self, *args):
        if self.tray._menu_is_open is True:
            self.tray._trayAction.trigger()
        self.tray._webWidget.unload_page()

    def show(self):
        self.window.show()

    def load_tray_page(self, *args):
        if self.tray._menu_is_open is False:
            self.tray._webWidget.load_page()
    def on_tray_close(self, *args):
        if self.window._qMainWindow.isVisible():
            self.tray._webWidget.unload_page() # unload page while main window is visible to prevent flickering on arm mac

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

        elif PLATFORM == PLATFORMS.macos:
            try:
                cmd = [ "launchctl","load","/Library/LaunchDaemons/perfect-privacy-service.plist"]
                subprocess.Popen(["osascript", "-e","do shell script %s with administrator privileges without altering line endings" % self.quote_applescript(self.quote_shell(cmd))])
            except OSError as e:
                print(e)

    def quote_shell(self, args):
        return " ".join(quote(arg) for arg in args)

    def quote_applescript(self, string):
        charmap = { "\n": "\\n", "\r": "\\r", "\t": "\\t", "\"": "\\\"", "\\": "\\\\", }
        return '"%s"' % "".join(charmap.get(char, char) for char in string)



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
        msg = "Wenn dies wiederholt passiert, stelle sicher, dass keine andere Sicherheitssoftware unseren Dienst blockiert.<br><br>" \
            '<button style="background-image:linear-gradient(to bottom,#5cb85c 0,#419641 100%);  border-color: #3e8f3e; cursor: pointer;webkit-user-select: none;user-select: none;border: 1px solid;border-radius: 6px;line-height: 20px;font-size:14px;" onclick="pyhtmlapp.fix_service_as_admin()">Reparatur-Hintergrunddienst (als Admin)</button><br><br>' \
            'Wenn du den Dienst reparierst, kann es bis zu 30 Sekunden dauern, bis er geladen ist.<br>'\
            "Wenn alles andere fehlschlägt, kontaktiere bitte den Perfect Privacy Support<br>"
        if self.check_service_exe() == False:
            errormsg = "Einige Installationsdateien fehlen. Vergewissere dich, dass sie nicht von deiner Antivirensoftware unter Quarantäne gestellt wurden.<br> Bitte installiere Perfect Privacy neu"
        elif self.check_service_installed() == False:
            errormsg = "Der VPN-Hintergrunddienst ist nicht installiert<br>" + msg
        elif self.check_service_running() == False:
            errormsg = "Der VPN-Hintergrunddienst läuft nicht, aber es ist kein Grund ersichtlich. <br>" + msg
        return errormsg

if __name__ == '__main__':
    lock = FrontendLock()
    if lock.aquire() == False:
        os._exit(1)

    mainapp = MainApp()
    lock.signal.connect(mainapp.on_signal_received)
    try:
        mainapp.run()
    finally:
        lock.release()
    os._exit(0)
