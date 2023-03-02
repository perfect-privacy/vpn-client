import traceback
import sys
import signal

from core.libs.logger import Logger
from core.libs.web.reporter import ReporterInstance
from gui import getPyHtmlGuiInstance
from core.core import Core
from config.config import FRONTEND


class MacOS_Service():
    def __init__(self ):
        self.gui = None
        self.core = None

    def start(self):
        try:
            self.logger = Logger(quiet=True)
            self.core = Core(self.logger)
            signal.signal(signal.SIGINT, self._on_exit_signal)
            signal.signal(signal.SIGTERM, self._on_exit_signal)
            self.gui = getPyHtmlGuiInstance(
                frontend          = FRONTEND,
                appInstance       = self.core,
                on_frontend_ready = self.core.on_frontend_connected,
                on_frontend_exit  = self.core.on_frontend_disconnected,
            )
            self.gui.start(show_frontend=False, block=True)
        except Exception as e:
            ReporterInstance.report("service_start_crash", "%s" % traceback.format_exception(*sys.exc_info()))
            self.stop()

    def _on_exit_signal(self,signum, frame):
        self.stop()

    def stop(self):
        if self.core is not None:
            self.core.quit()
        if self.gui is not None:
            self.gui.stop()
