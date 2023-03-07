import threading
import logging
import time
from config.files import WINTUN_INF, TAPWINDOW_LATEST_INF, TAPWINDOW_9_00_00_9_INF, TAPWINDOW_9_00_00_21_INF, PNPUTIL
from pyhtmlgui import  Observable
from core.libs.subcommand import SubCommand
from config.constants import OPENVPN_DRIVER
from .driver_state import OpenVpnDriverState

class InstalledDriver():
    def __init__(self):
        self.name = None
        self.version_date = None
        self.version_number = None


class OpenVpnDriver(Observable):
    def __init__(self, core):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

        self.core = core

        self.lock = threading.Lock()

        self.wintun = Driver_WinTun(self)
        self.tapwindows = Driver_TapWindows(self)
        self.wintun.attach_observer(self._on_subdriver_changed)
        self.tapwindows.attach_observer(self._on_subdriver_changed)
        if self.core.settings.vpn.openvpn.driver.get() == OPENVPN_DRIVER.tap_windows6_9_00_00_9:
            self.tapwindows.set_version_to_install(TAPWINDOW_9_00_00_9_INF)
        if self.core.settings.vpn.openvpn.driver.get() == OPENVPN_DRIVER.tap_windows6_9_00_00_21:
            self.tapwindows.set_version_to_install(TAPWINDOW_9_00_00_21_INF)
        self.core.settings.vpn.openvpn.driver.attach_observer(self._on_settings_driver_changed)

        self.state = OpenVpnDriverState()
        self._is_running = True
        self.force_reinstall = False
        self._wakeup_event = threading.Event()
        self.on_driver_changed = Observable()
        self.__worker_thread = threading.Thread(target=self._worker_thread, daemon=True)
        self.__worker_thread.start()

    def _on_settings_driver_changed(self, source):
        if self.core.settings.vpn.openvpn.driver.get() == OPENVPN_DRIVER.tap_windows6_latest:
            self.tapwindows.set_version_to_install(TAPWINDOW_LATEST_INF)
        if self.core.settings.vpn.openvpn.driver.get() == OPENVPN_DRIVER.tap_windows6_9_00_00_9:
            self.tapwindows.set_version_to_install(TAPWINDOW_9_00_00_9_INF)
        if self.core.settings.vpn.openvpn.driver.get() == OPENVPN_DRIVER.tap_windows6_9_00_00_21:
            self.tapwindows.set_version_to_install(TAPWINDOW_9_00_00_21_INF)
        self.update_async()

    def update(self):
        self._update()

    def update_async(self):
        self._wakeup_event.set()

    def reinstall(self):
        self.force_reinstall = True
        self._wakeup_event.set()

    def shutdown(self):
        self._is_running = False
        self._wakeup_event.set()

    def _worker_thread(self):
        while self._is_running is True:
            self._wakeup_event.wait()
            self._wakeup_event.clear()
            while self.core.deviceManager.state.get() != "IDLE":
                self._logger.debug("waiting for devicemanager to get ready")
                time.sleep(1)
            self._update()

    def _update(self):
        try:
            self.lock.acquire()
            self.state.set(OpenVpnDriverState.WORKING)
            self.notify_observers()
            force = self.force_reinstall
            self.force_reinstall = False
            tun_changed = self.wintun.install(force=force)
            tap_changed = self.tapwindows.install(force=force)
            if tun_changed or tap_changed:
                self.on_driver_changed.notify_observers()

            self.state.set(OpenVpnDriverState.IDLE)
        finally:
            self.lock.release()
        self.notify_observers()

    def _on_subdriver_changed(self, event):
        self.notify_observers()


class Driver_generic(Observable):
    def __init__(self, identifier, openVpnDriver):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.identifier = identifier
        self.openVpnDriver = openVpnDriver
        self.installed_drivers = []
        self.available_version_date = None
        self.available_version_number = None
        self._load_installed_drivers()

    def install(self, force = False):
        uninstall = force
        exists = False
        was_changed = False
        for installedDriver in self._enum_drivers():
            if installedDriver.version_number != self.available_version_number:
                uninstall = True
            else:
                exists = True

        if uninstall is True:
            was_changed = True
            self._clear_driverstore()

        if uninstall is True or exists is False:
            was_changed = True
            self._add_driver()

        if was_changed is True:
            self._load_installed_drivers()
        return was_changed

    def _load_installed_drivers(self):
        self.installed_drivers = [i for i in self._enum_drivers()]
        self.notify_observers()

    def _clear_driverstore(self):
        changed = False
        for installedDriver in self._enum_drivers():
            self._delete_driver(installedDriver.name)
            changed = True
        if changed is True:
            self._load_installed_drivers()

    def _enum_drivers(self):
        success, stdout, stderr = SubCommand().run(PNPUTIL, [ "/enum-drivers", "/class", "Net" ])
        try:
            parts  = stdout.replace(b"\r", b"").replace(b"  ", b" ").split(b"\n\n")
        except Exception as e:
            self._logger.debug("Failed to enumerate drivers, %s" % e)
            parts = []

        for part in parts:
            if part.find(self.identifier.encode("UTF-8")) != -1:
                try:
                    i = InstalledDriver()
                    i.name = part.split(b"\n")[0].split(b": ")[1].strip().decode("UTF-8").strip()
                    i.version_date = part.split(b"\n")[5].split(b": ")[1].strip().split(b" ")[0].strip().decode("UTF-8").strip()
                    i.version_number = part.split(b"\n")[5].split(b": ")[1].strip().split(b" ")[1].strip().decode("UTF-8").strip()
                    yield i
                except Exception as e:
                    self._logger.debug("Failed to parse driver enumeration, %s" % e)
        return []

    def _enum_devices(self):
        success, stdout, stderr = SubCommand().run(PNPUTIL, [ "/enum-devices", "/class", "Net" ])
        try:
            parts  = stdout.replace(b"\r", b"").replace(b"  ", b" ").split(b"\n\n")
        except Exception as e:
            self._logger.debug("Failed to enumerate devices, %s" % e)
            parts = []

        for part in parts:
            try:
                if part.find(self.identifier.encode("UTF-8")) != -1:
                    lines = part.split(b"\n")
                    instance_id = lines[0].split(b": ")[1].strip().decode("UTF-8").strip()
                    yield instance_id
            except Exception as e:
                self._logger.debug("Failed to parse device enumeration, %s" % e)
        return []

    def _delete_driver(self, oemname):
        if oemname not in  [x.name for x in self.installed_drivers]:
            raise Exception("No such driver installed, %s is unknown" % oemname)

        for instanceid in self._enum_devices():
            self._remove_device(instanceid)

        success, stdout, stderr = SubCommand().run(PNPUTIL, ["/delete-driver", oemname])
        self.openVpnDriver.on_driver_changed.notify_observers()
        self._load_installed_drivers()

    def _remove_device(self, instance_id):
        success, stdout, stderr = SubCommand().run(PNPUTIL, [ "/remove-device", instance_id ])

    def _add_driver(self):
        raise NotImplementedError()


class Driver_TapWindows(Driver_generic):
    def __init__(self, openVpnDriver):
        self.identifier = "TAP-Windows Provider V9"
        super().__init__(self.identifier, openVpnDriver)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.set_version_to_install(TAPWINDOW_LATEST_INF)

    def _add_driver(self):
        success, stdout, stderr = SubCommand().run(PNPUTIL, ["/add-driver", self._inf_file ])

    def set_version_to_install(self, inf_file):
        self._inf_file = inf_file
        try:
            parts = open(self._inf_file,"r").read().split("DriverVer")[1].split("=")[1].split("\n")[0].strip().split(",")
            self.available_version_date   = parts[0].strip()
            self.available_version_number = parts[1].strip()
        except Exception as e:
            self._logger.debug("Failed to get TapWindows version, %s" % e)
            self.available_version_date   = 0
            self.available_version_number = 0


class Driver_WinTun(Driver_generic):
    def __init__(self, openVpnDriver):
        self.identifier = "WireGuard LLC"
        super().__init__(self.identifier, openVpnDriver)
        self._logger = logging.getLogger(self.__class__.__name__)
        try:
            parts = open(WINTUN_INF,"r").read().split("DriverVer")[1].split("=")[1].split("\n")[0].strip().split(",")
            self.available_version_date   = parts[0].strip()
            self.available_version_number = parts[1].strip()
        except Exception as e:
            self._logger.debug("Failed to get WinTUN version, %s" % e)
            self.available_version_date   = 0
            self.available_version_number = 0

    def _add_driver(self):
        success, stdout, stderr = SubCommand().run(PNPUTIL, ["/add-driver", WINTUN_INF ])
