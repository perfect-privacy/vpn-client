from core.libs.logger import Logger
from gui import getPyHtmlGuiInstance
from core.core import Core
from config.config import FRONTEND
import signal

class MacOS_Service():
    def __init__(self ):
        self.logger = Logger(quiet=True)
        self.core = Core(self.logger)
        signal.signal(signal.SIGINT, self._on_exit_signal)
        signal.signal(signal.SIGTERM, self._on_exit_signal)
        self.gui = None

    def start(self):
        self.gui = getPyHtmlGuiInstance(
            frontend          = FRONTEND,
            appInstance       = self.core,
            on_frontend_ready = self.core.on_frontend_ready,
            on_frontend_exit  = self.core.on_frontend_exit,
        )
        self.gui.start(show_frontend=False, block=True)

    def _on_exit_signal(self,signum, frame):
        self.core.quit()
        self.gui.stop()
