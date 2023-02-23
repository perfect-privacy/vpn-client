import os, sys
import traceback
import threading
PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.insert(0, PROJECT_ROOT_DIRECTORY)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT_DIRECTORY))
try:
    from core.libs.web.reporter import ReporterInstance
except:
    ReporterInstance = None
try:
    from gui import getPyHtmlGuiInstance
    from core.libs.logger import Logger
    from core.core import Core
    from launcher.perfect_privacy_frontend import MainApp
except:
    if ReporterInstance is not None:
        ReporterInstance.report("standalone_import_crash", "%s" % traceback.format_exception(*sys.exc_info()))
        ReporterInstance.shutdown()
    os._exit(1)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    if ReporterInstance is not None:
        ReporterInstance.report("unhandled_exception", "%s" % traceback.format_exception(exc_type, exc_value, exc_traceback))

def handle_thread_exception(args):
    handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

sys.excepthook = handle_exception
threading.excepthook = handle_thread_exception

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
        if ReporterInstance is not None:
            ReporterInstance.shutdown()
        os._exit(0)

if __name__ == '__main__':
    Standalone().run()
    if ReporterInstance is not None:
        ReporterInstance.shutdown()

