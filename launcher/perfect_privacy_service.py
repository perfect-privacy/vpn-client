import os, sys, threading
import traceback
PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))
sys.path.insert(0, PROJECT_ROOT_DIRECTORY)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT_DIRECTORY))
try:
    from core.libs.web.reporter import ReporterInstance
except:
    ReporterInstance = None

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


try:
    from config.config import APP_VERSION
    from config.files import PLATFORMS,PLATFORM, SOFTWARE_UPDATE_FILENAME
    from config.paths import SOFTWARE_UPDATE_DIR
    from gui import getPyHtmlGuiInstance
except:
    ReporterInstance.report("service_import_crash", "%s" % traceback.format_exception(*sys.exc_info()))
    ReporterInstance.shutdown()
    os._exit(1)


if __name__ == "__main__":
    try:
        try:
            option = sys.argv[1]
        except:
            option = None

        if option == "uninstall":   # run silent uninstall, disable firewall, dns, network stuff we installed
            from core.leakprotection import LeakProtection
            LeakProtection(core=None).reset()
            if PLATFORM == PLATFORMS.windows:
                from core.devicemanager import DeviceManager
                DeviceManager(None).uninstall()
                shortcut_path = os.path.join("c:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp", "Perfect Privacy.lnk")
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
        else:
            if PLATFORM == PLATFORMS.macos:
                from launcher.services.macos_service import MacOS_Service
                service = MacOS_Service()
                service.start()

            if PLATFORM == PLATFORMS.linux and option == "daemon":
                from launcher.services.linux_daemon import LinuxDaemon
                del sys.argv[1]  # remove "deamon" from comandline args
                linuxDaemon  = LinuxDaemon()
                linuxDaemon.from_commandline()

            if PLATFORM == PLATFORMS.windows: # if we are launched on windows, without parameters we asume we are the windows service
                from launcher.services.windows_service import Windows_Service
                import servicemanager
                import win32serviceutil
                if len(sys.argv) == 1:
                    servicemanager.Initialize()
                    servicemanager.PrepareToHostSingle(Windows_Service)
                    servicemanager.StartServiceCtrlDispatcher()
                else:
                    win32serviceutil.HandleCommandLine(Windows_Service)
    except Exception as e:
        if ReporterInstance is not None:
            ReporterInstance.report("service_crash", "%s" % traceback.format_exception(*sys.exc_info()))
            ReporterInstance.shutdown()