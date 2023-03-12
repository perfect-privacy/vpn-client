import logging
import os
import random
import threading
import time
from threading import Timer
from pyhtmlgui import Observable
from core.userapi.userapi import UserAPI
from .leakprotection.leakprotection_generic import LeakProtectionState
from .configupdater import ConfigUpdater
from .leakprotection import LeakProtection
from .ipcheck import IpCheck
from .libs.web.reporter import ReporterInstance
from .routing.routing import Routing
from .settings import Settings
from .softwareupdater import SoftwareUpdater
from .trafficdownload import TrafficDownload
from .vpnconfigs import VpnGroupPlanet
from .vpnsession import Session
from .openvpndriver import OpenVpnDriver
from .devicemanager import DeviceManager
from .favourites import Favourites
from .vpnsession.common import VpnConnectionState
from config.config import PLATFORM
from config.constants import PLATFORMS, VPN_PROTOCOLS
from config.paths import APP_DIR
from .vpnsession.session import SessionState
if PLATFORM == PLATFORMS.windows:
    import win32com.client
    import pythoncom

class Core(Observable):

    def __init__(self, global_logger):
        super().__init__()
        self.global_logger = global_logger
        logging.getLogger("requests").setLevel(logging.CRITICAL)
        logging.getLogger("urllib3").setLevel(logging.CRITICAL)

        self._start_timers = []
        self._is_shutting_down = False
        self.on_exited = Observable()

        self.on_update_started = Observable()
        self.frontend_active = False

        self._logger = logging.getLogger(self.__class__.__name__)

        self.settings = Settings()
        self.settings.account.attach_observer(self._on_credentials_updated)
        self.settings.startup.start_on_boot.attach_observer(self._on_start_on_boot_updated)
        ReporterInstance.send_crashreports = self.settings.send_crashreports
        self.vpnGroupPlanet = VpnGroupPlanet()
        self.vpnGroupPlanet.load_configs_json()

        self.favourites = Favourites(self)

        self.session = Session(self)
        self.leakprotection = LeakProtection(core=self)
        self.routing = Routing(self)

        self.settings.leakprotection.attach_observer(self.check_connection)
        self._start_timers.append(Timer(2, self.check_connection))

        self.configUpdater = ConfigUpdater(self)
        self.configUpdater.update_installed.attach_observer(self._on_config_update_installed)
        self._start_timers.append(Timer(60, self.configUpdater.enable))

        self.softwareUpdater = SoftwareUpdater(self)
        self.softwareUpdater.update_installed.attach_observer(self._on_software_update_installed)
        self._start_timers.append(Timer(60, self.softwareUpdater.enable))

        self.ipcheck = IpCheck(self)
        self._start_timers.append(Timer(10, self.ipcheck.check_now))
        self.session.state.attach_observer(self._on_session_state_changed)

        self.trafficDownload = TrafficDownload(self)
        self.trafficDownload._on_data_updated.attach_observer(self._on_trafficDownload_updated)
        self._start_timers.append(Timer(10, self.trafficDownload.check_now))

        self.deviceManager = None
        if PLATFORM == PLATFORMS.windows:
            self.openVpnDriver = OpenVpnDriver(self)
            self._start_timers.append(Timer(3, self.openVpnDriver.update_async))

            self.deviceManager = DeviceManager(self)
            self._start_timers.append(Timer(5, self.deviceManager.update_async))

        if self.settings.is_first_startup.get() is True:
            if len(self.session.hops) == 0:
                try:
                    self.session.add_hop(self.vpnGroupPlanet.countrys.get("Netherlands"))
                except:
                    pass
            if PLATFORM == PLATFORMS.windows:
                self.leakprotection.reset()
            self.settings.is_first_startup.set(False)

        self.userapi = UserAPI(self)
        self._start_timers.append(Timer(5, self.userapi.request_update))

        self.session.start()
        for t in self._start_timers:
            t.start()

        self.settings.vpn.vpn_protocol.attach_observer(self.on_updated_vpnsettings)
        self.settings.vpn.openvpn.cascading_max_hops.attach_observer(self.on_updated_vpnsettings)
        self._send_usage_stats_thread = threading.Thread(target=self.check_send_usage_stats, daemon=True)
        self._send_usage_stats_thread.start()
        self._on_start_on_boot_updated() # after first install set autostart true

    def on_updated_vpnsettings(self):
        if self.settings.vpn.vpn_protocol.get() == VPN_PROTOCOLS.openvpn:
            max_hops = self.settings.vpn.openvpn.cascading_max_hops.get()
        else:
            max_hops = 1
        while len(self.session.hops) > max_hops:
            self.session.remove_hop_by_index(len(self.session.hops) - 1)

    def on_frontend_exit_by_user(self, for_update=False):
        self.frontend_active = False
        if self.settings.startup.enable_background_mode.get() == False or for_update == True:
            self.session.disconnect()
        self.leakprotection.update_async()

    def on_frontend_connected(self, pyHtmlGuiInstance, nr_of_active_frontends):
        if self.frontend_active is False and nr_of_active_frontends > 0 and self.settings.startup.connect_on_start.get() == True:
            self.session.connect()
        self.frontend_active = nr_of_active_frontends > 0
        self.trafficDownload.check_now()
        self.ipcheck.check_now()
        self.userapi.request_update()

    def on_frontend_disconnected(self, pyHtmlGuiInstance, nr_of_active_frontends):
        pass

    def _on_session_state_changed(self, *args, **kwargs):
        if self.session.state.get() in [SessionState.DISCONNECTING, SessionState.CONNECTING]:
            self.ipcheck.clear()
        if self.session.state.get() in [SessionState.IDLE, SessionState.CONNECTED]:
            Timer(2, self.ipcheck.check_now).start()

    def check_connection(self):
        self.routing.update_async()
        self.leakprotection.update_async()
        self.ipcheck.check_now()

    def _on_software_update_installed(self, event):
        pass

    def _on_config_update_installed(self, sender):
        self.vpnGroupPlanet.load_configs_json()

    def _on_trafficDownload_updated(self, sender, data):
        self.vpnGroupPlanet.add_bandwidth_data(data)

    def allow_webrequests(self):
        connected = False
        for hop in self.session.hops:
            if hop.connection != None:
                if hop.connection.state.get() not in [ VpnConnectionState.IDLE, VpnConnectionState.CONNECTED ]:
                    return False
                if hop.connection.state.get() ==  VpnConnectionState.CONNECTED:
                    connected = True
                if hop.connection.state.get() == VpnConnectionState.IDLE:
                    connected = False
        if connected is False and self.leakprotection.state.get() != LeakProtectionState.DISABLED:
            return False
        return True

    def _on_start_on_boot_updated(self, sender=None):
        if PLATFORM == PLATFORMS.windows:
            startup_path = "c:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp"
            shortcut_path = os.path.join(startup_path, "Perfect Privacy.lnk")
            if self.settings.startup.start_on_boot.get() == False:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
            else:
                if not os.path.exists(startup_path):
                    os.makedirs(startup_path)
                pythoncom.CoInitialize()
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.IconLocation = str(os.path.join(APP_DIR, "gui", "default", "static", "icons", "pp_icon.ico"))
                shortcut.Targetpath = os.path.join(APP_DIR, "perfect-privacy.exe")
                shortcut.save()

        elif PLATFORM == PLATFORMS.macos:
            if self.settings.startup.start_on_boot.get() == False:
                if os.path.exists("/Library/LaunchAgents/perfect-privacy.plist"):
                    os.system('launchctl bootout system "/Library/LaunchAgents/perfect-privacy.plist"')
                    os.system('rm "/Library/LaunchAgents/perfect-privacy.plist"')
            else:
                s = '''
                    <?xml version="1.0" encoding="UTF-8"?>
                    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
                    <plist version="1.0">
                    <dict>
                        <key>Label</key>
                        <string>perfect-privacy</string>
                        <key>RunAtLoad</key>
                        <true/>
                        <key>ProgramArguments</key>
                        <array>
                            <string>/Applications/Perfect\ Privacy.app/Contents/MacOS/perfect-privacy</string>
                        </array>
                    </dict>
                    </plist>
                '''
                with open("/Library/LaunchAgents/perfect-privacy.plist", "w") as f:
                    f.write(s.replace("\n                    ",""))
                os.system('launchctl bootstrap system "/Library/LaunchAgents/perfect-privacy.plist"')

    def _on_credentials_updated(self, sender):
        self.settings.account.account_expiry_date_utc = None
        self.userapi.request_update()

    def quit(self):
        try:
            if self._is_shutting_down:
                return
            self._is_shutting_down = True

            for t in self._start_timers:
                try:
                    t.cancel()
                except:
                    pass

            try:
                self.configUpdater.disable()
                self.softwareUpdater.disable()
            except:
                pass

            try:
                self.session.quit()
                self._logger.debug("session shut down")
            except Exception as e:
                self._logger.error("unable to shut down session: {}".format(str(e)))

            time.sleep(2)# give async leak protection and others some time

            try:
                self.leakprotection.shutdown()
            except Exception as e:
                self._logger.error("unable to shut down leak protection: {}".format(str(e)))

        except Exception as e:
            self._logger.error("shutting down gracefully failed: {}".format(str(e)))
        finally:
            self.on_exited.notify_observers()
        self._logger.info("shutdown finished")

    def check_send_usage_stats(self):
        while True:
            time.sleep(1800) # roll dice every half hour for time to send report
            if random.randint(0, 48) != 42: # randomly trigger only ~once a day
                continue
            if random.randint(0, 500) != 42: # ~once a day have 1:500 chance to actually send stats
                continue
            if self.settings.send_statistics.get() == False:
                continue
            stats = {
                "settings.interface_level": self.settings.interface_level.get(),
                "settings.leakprotection.leakprotection_scope": self.settings.leakprotection.leakprotection_scope.get(),
                "settings.leakprotection.enable_ms_leak_protection": self.settings.leakprotection.enable_ms_leak_protection.get(),
                "settings.leakprotection.enable_wrong_way_protection": self.settings.leakprotection.enable_wrong_way_protection.get(),
                "settings.leakprotection.enable_snmp_upnp_protection": self.settings.leakprotection.enable_snmp_upnp_protection.get(),
                "settings.leakprotection.block_access_to_local_router": self.settings.leakprotection.block_access_to_local_router.get(),
                "settings.leakprotection.enable_ipv6_leak_protection": self.settings.leakprotection.enable_ipv6_leak_protection.get(),
                "settings.leakprotection.enable_deadrouting": self.settings.leakprotection.enable_deadrouting.get(),
                "settings.leakprotection.enable_dnsleak_protection": self.settings.leakprotection.enable_dnsleak_protection.get(),
                "settings.leakprotection.use_custom_dns_servers": self.settings.leakprotection.use_custom_dns_servers.get(),
                "settings.stealth.stealth_method": self.settings.stealth.stealth_method.get(),
                "settings.stealth.stealth_port": self.settings.stealth.stealth_port.get(),
                "settings.stealth.stealth_custom_node": self.settings.stealth.stealth_custom_node.get(),
                "settings.startup.start_on_boot": self.settings.startup.start_on_boot.get(),
                "settings.startup.connect_on_start": self.settings.startup.connect_on_start.get(),
                "settings.startup.enable_background_mode": self.settings.startup.enable_background_mode.get(),
                "settings.vpn.vpn_protocol": self.settings.vpn.vpn_protocol.get(),
                "settings.vpn.openvpn.protocol": self.settings.vpn.openvpn.protocol.get(),
                "settings.vpn.openvpn.cipher": self.settings.vpn.openvpn.cipher.get(),
                "settings.vpn.openvpn.driver": self.settings.vpn.openvpn.driver.get(),
                "settings.vpn.openvpn.tls_method": self.settings.vpn.openvpn.tls_method.get(),
                "settings.vpn.openvpn.port": self.settings.vpn.openvpn.port.get(),
                "settings.vpn.openvpn.cascading_max_hops": self.settings.vpn.openvpn.cascading_max_hops.get(),
                "usage.session.should_be_connected": self.session._should_be_connected.get(),
                "usage.session.hops": len(self.session.hops),
                "usage.has_ipv4": self.ipcheck.result4.public_ip != None,
                "usage.has_ipv6": self.ipcheck.result6.public_ip != None,
                "usage.ipv4_is_vpn": self.ipcheck.result4.vpn_connected == True,
                "usage.ipv6_is_vpn": self.ipcheck.result6.vpn_connected == True,
            }
            ReporterInstance.report_stats(data=stats)
