import threading
import logging
import time
import traceback

from core.libs.powershell import getPowershellInstance
from core.libs.web.reporter import ReporterInstance
from pyhtmlgui import  Observable
from config.constants import OPENVPN_DRIVER
from config.files import OPENVPN, TAPCTL
from core.libs.generic_state import GenericState
from core.libs.subcommand import SubCommand

class DeviceManagerState(GenericState):
    IDLE         = "IDLE"
    WORKING      = "WORKING"
    INSTALLING   = "INSTALLING"
    UNINSTALLING = "UNINSTALLING"
    _DEFAULT = IDLE

class OpenVpnDevice():
    def __init__(self):
        self.index = None
        self.name  = None
        self.guid  = None
        self.type  = None


class DeviceManager(Observable):
    def __init__(self, core):
        '''

        :type core: core.Core
        '''
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

        self.core = core
        self.lock = threading.Lock()
        self.wintun_devices = []
        self.tapwindows_devices = []
        self.state = DeviceManagerState()
        if self.core is not None:
            self.core.openVpnDriver.on_driver_changed.attach_observer(self._on_driver_changed)
            self.core.settings.vpn.openvpn.cascading_max_hops.attach_observer(self._on_cascading_max_hops_changed)
            self.core.settings.vpn.openvpn.driver.attach_observer(self._on_settings_driver_changed)

        self._is_running = True
        self._wakeup_event = threading.Event()
        self.__worker_thread = threading.Thread(target=self._worker_thread, daemon=True)
        self.__worker_thread.start()
        self.force_reinstall = False

    def _on_driver_changed(self,event):
        self.update_async()

    def get_device_by_hop(self, hopnr):
        driver = self.core.settings.vpn.openvpn.driver.get()
        if driver == OPENVPN_DRIVER.wintun:
            try:
                return self.wintun_devices[hopnr -1]
            except:
                pass
            return None
        else:
            try:
                return self.tapwindows_devices[hopnr -1]
            except:
                pass
            return None

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

    def uninstall(self):
         devices = [d for d in self._enum_devices() if d.type in ["wintun", "tap-windows6"] and d.name.startswith("Perfect Privacy")]
         for device in devices:
             success, stdout, stderr = SubCommand().run(TAPCTL, ["delete", "{%s}" % device.guid])

    def _worker_thread(self):
        while self._is_running is True:
            self._wakeup_event.wait()
            self._wakeup_event.clear()
            while self.core.openVpnDriver.state.get() != "IDLE":
                self._logger.debug("waiting for driver to get ready")
                time.sleep(1)
            self._update()

    def _load_existing_devices(self):
        self.existing_devices   = sorted([d for d in self._enum_devices()], key=lambda x:x.guid)
        self.wintun_devices     = [d for d in self.existing_devices if d.type == "wintun"]
        self.tapwindows_devices = [d for d in self.existing_devices if d.type == "tap-windows6"]
        self.notify_observers()

    def _update(self):
        try:
            self.lock.acquire()
            self.state.set(DeviceManagerState.WORKING)

            driver = self.core.settings.vpn.openvpn.driver.get()
            cascading_max_hops =  self.core.settings.vpn.openvpn.cascading_max_hops.get()
            changed = False

            self._load_existing_devices()

            nonpp_tapwindows_devices = [d for d in self.tapwindows_devices if not d.name.startswith("Perfect Privacy")]
            pp_tapwindows_devices    = [d for d in self.tapwindows_devices if     d.name.startswith("Perfect Privacy")]
            nonpp_wintun_devices     = [d for d in self.wintun_devices     if not d.name.startswith("Perfect Privacy")]
            pp_wintun_devices        = [d for d in self.wintun_devices     if     d.name.startswith("Perfect Privacy")]

            force = self.force_reinstall
            self.force_reinstall = False

            if driver == OPENVPN_DRIVER.wintun:
                to_remove = pp_tapwindows_devices
                exiting_devices    = pp_wintun_devices
            else:
                to_remove = pp_wintun_devices
                exiting_devices    = pp_tapwindows_devices

            if force is True:
                to_remove = pp_tapwindows_devices + pp_wintun_devices
            else:
                too_many_cnt = len(exiting_devices) - cascading_max_hops
                if too_many_cnt > 0:
                    for i in range(too_many_cnt):
                        to_remove.append(exiting_devices[i*-1])

            for device in to_remove:
                if device in exiting_devices:
                    exiting_devices.remove(device)

            if len(to_remove) > 0:
                self.state.set(DeviceManagerState.UNINSTALLING)

            for device in to_remove:
                changed = True
                self._delete(device.guid)
                self._load_existing_devices()

            self.state.set(DeviceManagerState.WORKING)
            if changed is True:
                self._load_existing_devices()
                changed = False

            hopnames_valid = []
            for hop_nr in range(1, cascading_max_hops+1):
                hopname = "Perfect Privacy VPN %s" % (hop_nr)
                hopnames_valid.append(hopname)
                if len([d for d in exiting_devices if d.name == hopname]) == 0: # device does not exist
                    self.state.set(DeviceManagerState.INSTALLING)
                    self._create(driver, hopname)
                    self._load_existing_devices()
                    changed = True

            if changed is True:
                self._load_existing_devices()
                changed = False

            if changed:
                self._load_existing_devices()

            # if not all installed:
            # data = {
            #   "max_hops": 2
            #   "installed hops"
            #   "driver" : wintun
            #   "logs" : last x log entry from this class
            # }
            self.state.set(DeviceManagerState.IDLE)

        finally:
            self.lock.release()
        self.notify_observers()

    def _on_settings_driver_changed(self, event):
        self._logger.debug("_on_settings_driver_changed")
        self.update_async()

    def _on_cascading_max_hops_changed(self, event):
        self._logger.debug("_on_cascading_max_hops_changed")
        self.update_async()

    def _create(self, driver, name):
        args = ["create", "--name" , "%s" % name]
        if driver == OPENVPN_DRIVER.wintun:
            args.extend([ "--hwid", "wintun"])
        success, stdout, stderr = SubCommand().run(TAPCTL, args)

    def _delete(self, guid):
        success, stdout, stderr = SubCommand().run(TAPCTL, [ "delete", "{%s}" % guid])

    def _enum_devices(self):
        networkdatas = getPowershellInstance().execute("Get-DnsClientServerAddress", as_data = True)
        name_to_index = {}
        if networkdatas is None:
            ReporterInstance.report("devicemanager_enumeration_failed", "")
            return []

        for networkdata in networkdatas:
            try:
                name_to_index[networkdata["InterfaceAlias"]] = networkdata["InterfaceIndex"]
            except Exception as e:
                self._logger.debug("Failed to load networkdata, %s" % e)
                ReporterInstance.report("devicemanager_get_interfaces_failed", { "exception" : traceback.format_exc(), "networkdata" : networkdata })

        success, stdout, stderr = SubCommand().run(OPENVPN, [ "--show-adapters"])
        for line in stdout.split(b"\n"):
            try:
                if line.find(b"{") > -1 or line.find(b"}") > -1 or line.find(b"\\") > -1:
                    try:
                        name = line.split(b"'")[1].strip().decode("UTF-8")
                    except:
                        continue # no, or foreign character name, aka not ours.
                    d = OpenVpnDevice()
                    d.index = name_to_index[name]
                    d.name = name
                    d.guid = line.split(b"{")[1].split(b"}")[0].strip().decode("UTF-8")
                    d.type = line.split(b"}")[1].strip().decode("UTF-8")
                    yield d
            except Exception as e:
                ReporterInstance.report("devicemanager_show_adapters_failed", traceback.format_exc())
                self._logger.debug("Failed to parse device enumeration, %s" % e)
        return []

