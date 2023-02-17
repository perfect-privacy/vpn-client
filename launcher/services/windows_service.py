import time, os, sys
import traceback

from core.core import Core
import win32serviceutil
import servicemanager
import win32event
import win32service

from config.config import FRONTEND
from core.libs.logger import Logger

from gui import getPyHtmlGuiInstance

service_name = "Perfect Privacy VPN"
service_displayname = service_name + " core"
service_description = service_name + " core service"

PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))
CRASHLOG = os.path.join(PROJECT_ROOT_DIRECTORY, "crash.log")


class Windows_Service(win32serviceutil.ServiceFramework):
    _svc_name_ = service_name
    _svc_display_name_ = service_displayname
    _svc_description_ = service_description
    logger = None  # set by caller after import to global logger

    @classmethod
    def parse_command_line(cls):
        win32serviceutil.HandleCommandLine(cls)

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        #socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        self.start()
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        self.main()

    def start(self):
        try:
            self.logger = Logger(quiet=True)
            self.core = Core(self.logger)
            self.gui = getPyHtmlGuiInstance(
                frontend = FRONTEND,
                appInstance = self.core,
                on_frontend_ready = self.core.on_frontend_ready,
                on_frontend_exit  = self.core.on_frontend_exit,
            )
            self.gui.start(show_frontend=False, block=False)
            self.isrunning = True
        except Exception as e:
            self.isrunning = False
            self.gui.stop()
            if getattr(sys, 'frozen', False) == True:  # check if we are bundled by pyinstaller
                exc_type, exc_value, exc_traceback = sys.exc_info()
                tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
                with open(CRASHLOG, "a") as f:
                    f.write("%s" % tb)
            else:
                raise e

    def stop(self):
        try:
            self.core.quit()
            for endpoint in self.gui._endpoints.values():
                for instance in endpoint._gui_instances:
                    instance.call_javascript("exit_app()", args=[], skip_results=True)
        except:
            pass
        self.gui.stop()
        self.isrunning = False

    def main(self):
        self.gui.join()
        while self.isrunning is True:
            time.sleep(1)


