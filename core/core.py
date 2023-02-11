# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2014-2015 Perfect Privacy <support@perfect-privacy.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE
import logging
import os
import subprocess
import sys
import threading
import time
from threading import Timer

#from config.paths import APP_UPDATE_DIR, SOFTWARE_UPDATE_IN_PROGRESS_PATH
#from core.libs.smartnet import SmartNet
from config.files import SOFTWARE_UPDATE_FILENAME
from config.paths import SOFTWARE_UPDATE_DIR
from core.userapi.userapi import UserAPI
#from core.libs.wlanaccesspoint import WlanAccesspoint
#from core.libs.wlanclient.wlanClient import WlanClient
#from core.vpn.configs import VpnServerPlanet
# from .vpn.vpn_config_loader import ConfigLoader #, get_group_by_identifier
from pyhtmlgui import Observable

from .leakprotection.leakprotection_generic import LeakProtectionState
from .libs.update.updater_state import UpdaterState
from .libs.web import reporter
from .libs.powershell import Powershell
from config.constants import PLATFORMS
from config.config import PLATFORM
from .configupdater import ConfigUpdater
from .leakprotection import LeakProtection
from .ipcheck import IpCheck
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
from config.constants import PLATFORMS
from config.paths import APP_DIR
from .vpnsession.session import SessionState


class Core(Observable):

    def __init__(self, global_logger):
        super().__init__()
        self.global_logger = global_logger
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        self._start_timers = []
        self._is_shutting_down = False
        self.on_exited = Observable()

        self.on_update_started = Observable()
        self.frontend_active = False

        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug("loading core")

        self.settings = Settings()
        self.settings.account.attach_observer(self._on_credentials_updated)
        self.settings.startup.start_on_boot.attach_observer(self._on_start_on_boot_updated)

        self.vpnGroupPlanet = VpnGroupPlanet()
        self.vpnGroupPlanet.load_configs_json()

        if PLATFORM == PLATFORMS.windows:
            self.powershell = Powershell()

        self.favourites = Favourites(self)

        self.session = Session(self)

        self.leakprotection = LeakProtection(core=self)
        self.settings.leakprotection.attach_observer(self._on_leakprotection_settings_changed)

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
            if PLATFORM == PLATFORMS.windows:
                self.leakprotection.reset()
            self.settings.is_first_startup.set(False)

        self.userapi = UserAPI(self)
        self._start_timers.append(Timer(5, self.userapi.request_update))

        self.session.start()
        for t in self._start_timers:
            t.start()

    def on_frontend_ready(self, pyHtmlGuiInstance, nr_of_active_frontends):
        self.frontend_active = nr_of_active_frontends > 0
        self.trafficDownload.check_now()
        self.ipcheck.check_now()
        self.userapi.request_update()

    def on_frontend_exit(self, pyHtmlGuiInstance, nr_of_active_frontends):
        self.frontend_active = nr_of_active_frontends > 0

    def _on_session_state_changed(self, *args, **kwargs):
        if self.session.state.get() in [SessionState.DISCONNECTING, SessionState.CONNECTING]:
            self.ipcheck.clear()
        if self.session.state.get() in [SessionState.IDLE, SessionState.CONNECTED]:
            Timer(2, self.ipcheck.check_now).start()

    def check_connection(self):
        self.ipcheck.check_now()
        self.leakprotection.update_async()

    def _on_leakprotection_settings_changed(self, event):
        self.leakprotection.update_async()

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

    def _on_start_on_boot_updated(self, sender):
        if PLATFORM == PLATFORMS.windows:
            startup_path = "c:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp"
            shortcut_path = os.path.join(startup_path, "Perfect Privacy.lnk")
            if self.settings.startup.start_on_boot.get() == False:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
            else:
                if not os.path.exists(startup_path):
                    os.makedirs(startup_path)
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.IconLocation = str(os.path.join(APP_DIR, "gui", "default", "static", "img", "pp_icon.ico"))
                shortcut.Targetpath = os.path.join(APP_DIR, "perfect-privacy.exe")
                shortcut.save()

        elif PLATFORM == PLATFORMS.macos:
            if self.settings.startup.start_on_boot.get() == False:
                os.system('launchctl unload "/Library/LaunchAgents/perfect-privacy.plist"')
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
                os.system('launchctl load "/Library/LaunchAgents/perfect-privacy.plist"')

    def _on_credentials_updated(self, sender):
        self.settings.account.account_expiry_date_utc = None
        self.userapi.request_update()

    def quit(self):
        try:
            if self._is_shutting_down:
                self._logger.debug("shutdown already in progress")
                return
            self._is_shutting_down = True
            self._logger.info("shutting down")

            for t in self._start_timers:
                try:
                    t.cancel()
                except:
                    pass

            try:
                self._logger.debug("shutting down session")
                self.session.quit()
                self._logger.debug("session shut down")
            except AttributeError:
                pass
            except Exception as e:
                self._logger.error("unable to shut down session: {}".format(str(e)))

            try:
                reporter.shutdown()
            except:
                self._logger.debug("shutting down reporter failed")
        except Exception as e:
            self._logger.error("shutting down gracefully failed: {}".format(str(e)))
        finally:
            self.on_exited.notify_observers()
        self._logger.info("shutdown finished")
