import os
from pyhtmlgui.apps.qt import PyHtmlQtApp, PyHtmlQtTray, PyHtmlQtWindow
from config.config import SHARED_SECRET, PLATFORM, SERVICE_PORT
from config.constants import PLATFORMS
from config.paths import APP_DIR

class MainApp():
    def __init__(self):
        self.icon_path = os.path.join(APP_DIR, "gui", "default", "static", "img", "pp_icon.ico")

        self.app = PyHtmlQtApp(icon_path= self.icon_path)

        self.window = PyHtmlQtWindow(self.app, url="http://127.0.0.1:%s/?token=%s"  % (SERVICE_PORT, SHARED_SECRET), size=[1200, 800], title="Perfect Privacy", icon_path = self.icon_path)
        self.window.addJavascriptFunction("exit_app", self.stop)
        self.window.addJavascriptFunction("copy_to_clipboard", PyHtmlQtApp.clipboard().setText)

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
            #self.app.on_about_to_quit_event.attach_observer(...)
        else:
            self.window.on_minimized_event.attach_observer(self.window.hide)
            self.tray.on_left_clicked.attach_observer(self.window.show)

    def run(self):
        self.window.show()
        self.app.run()

    def stop(self, *args):
        self.app.stop()

if __name__ == '__main__':
    MainApp().run()
    os._exit(0)
