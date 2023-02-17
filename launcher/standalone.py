import os, sys
PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.insert(0, PROJECT_ROOT_DIRECTORY)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT_DIRECTORY))
from gui import getPyHtmlGuiInstance
from core.libs.logger import Logger
from core.core import Core

from launcher.perfect_privacy_frontend import MainApp

class Standalone():
    def __init__(self):
        self.logger = Logger()
        self.core = Core(self.logger)
        self.guiservice = getPyHtmlGuiInstance(
            appInstance       = self.core,
            on_frontend_ready = self.core.on_frontend_ready,
            on_frontend_exit  = self.core.on_frontend_exit,
        )
        self.core.on_exited.attach_observer(self._on_core_exited)

    def run(self):
        self.guiservice.start(show_frontend=False, block=False)
        self.mainApp = MainApp()
        self.mainApp.run()
        self.core.quit()
        self.guiservice.join() # core exit stops gui service, so wait for what

    def _on_core_exited(self):
        self.mainApp.stop()
        self.guiservice.stop()
        os._exit(0)

if __name__ == '__main__':
    Standalone().run()

