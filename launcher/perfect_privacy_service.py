import os, sys
import subprocess
import traceback

from config.config import APP_VERSION

PROJECT_ROOT_DIRECTORY = os.path.abspath(os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0]))))
sys.path.insert(0, PROJECT_ROOT_DIRECTORY)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT_DIRECTORY))
try:
    from config.files import PLATFORMS,PLATFORM, SOFTWARE_UPDATE_FILENAME
    from config.paths import SOFTWARE_UPDATE_DIR
    from gui import getPyHtmlGuiInstance
except:
    if getattr(sys, 'frozen', False) == True:  # check if we are bundled by pyinstaller
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
        open("crash.log", "w").write("%s" % tb)
        os._exit(1)


def _compare_version_numbers(new_version_number, old_version_number):
    new_split = new_version_number.split(".")
    old_split = old_version_number.split(".")
    if len(old_split) != len(new_split):
        return 1
    for i, new_part in enumerate(new_split):
        if new_part == old_split[i]:
            continue
        elif new_part > old_split[i]:
            return 1
        elif new_part < old_split[i]:
            return -1
        else:
            raise Exception()
    return 0

def check_install_autoupdate():
    update_executable = os.path.join(SOFTWARE_UPDATE_DIR, SOFTWARE_UPDATE_FILENAME)
    update_executable_version = os.path.join(SOFTWARE_UPDATE_DIR, "%s.version" % SOFTWARE_UPDATE_FILENAME)

    if os.path.exists(update_executable) != os.path.exists(update_executable_version):
        if os.path.exists(update_executable):
            os.remove(update_executable)
        if os.path.exists(update_executable_version):
            os.remove(update_executable_version)

    if not os.path.exists(update_executable):
        return

    VERSION = open(update_executable_version, "r").read().strip()

    if _compare_version_numbers(VERSION, APP_VERSION) <= 0: # update already installed
        if os.path.exists(update_executable):
            os.remove(update_executable)
        if os.path.exists(update_executable_version):
            os.remove(update_executable_version)

    if os.path.exists(update_executable):
        kwargs = {}
        if PLATFORM == PLATFORMS.windows:
            CREATE_NEW_PROCESS_GROUP = 0x00000200  # note: could get it from subprocess
            DETACHED_PROCESS = 0x00000008  # 0x8 | 0x200 == 0x208
            kwargs.update(creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
            p = subprocess.Popen([update_executable, "/S"], start_new_session=True,  close_fds=True)
        elif sys.version_info < (3, 2):  # assume posix
            kwargs.update(preexec_fn=os.setsid)
        else:  # Python 3.2+ and Unix
            kwargs.update(start_new_session=True)
        os._exit(0)


if __name__ == "__main__":
    try:
        if os.path.exists("crash.log"):
            os.remove("crash.log")

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
        if getattr(sys, 'frozen', False) == True:  # check if we are bundled by pyinstaller
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
            open("crash.log","a").write("%s" % tb)
        else:
            raise e
