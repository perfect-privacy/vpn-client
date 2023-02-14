import os
import shutil
from gettext import gettext as _
import logging
from datetime import datetime
import math
import traceback
from core.libs.update.generic_updater import GenericUpdater
from core.libs.update.updater_state   import UpdaterState
from core.libs.web import SecureDownload, WebRequest
from config.config import APP_VERSION
from config.urls   import SOFTWARE_UPDATE_URL
from config.files  import SOFTWARE_UPDATE_FILENAME
from config.paths  import SOFTWARE_UPDATE_DIR

class SoftwareUpdater(GenericUpdater):
    def __init__(self, core,
                 min_check_interval_seconds=5*60,
                 max_check_interval_seconds=7*24*60*60,
                 err_check_interval_seconds=10*60):

        self.core = core
        super(SoftwareUpdater, self).__init__(
            file_url = SOFTWARE_UPDATE_URL,
            signature_url  = SOFTWARE_UPDATE_URL + ".sig",
            version_url  = SOFTWARE_UPDATE_URL + ".version",
            download_directory  = SOFTWARE_UPDATE_DIR,
            min_check_interval_seconds = min_check_interval_seconds,
            max_check_interval_seconds = max_check_interval_seconds,
            err_check_interval_seconds = err_check_interval_seconds)

        self._logger = logging.getLogger(self.__class__.__name__)
        self.version_local = APP_VERSION
        if os.path.exists(os.path.join(SOFTWARE_UPDATE_DIR, SOFTWARE_UPDATE_FILENAME)):
            self.state.set(UpdaterState.UPDATER_STATE_READY_FOR_INSTALL)
            self.version_online = open(os.path.join(SOFTWARE_UPDATE_DIR, "%s.version" % SOFTWARE_UPDATE_FILENAME), "r").read()


    def _check_for_updates(self):
        if self.state.get()  != UpdaterState.UPDATER_STATE_IDLE and self.state.get() != UpdaterState.UPDATER_STATE_READY_FOR_INSTALL:
            self._logger.debug("can not start a check for updates: not idle")
            return
        if  self.core.allow_webrequests() is False:
            self._logger.debug("No webrequests now, everything is firewalled")
            return

        self._logger.debug("starting checking for updates and updating")
        now = datetime.now().timestamp()
        self.state.set(UpdaterState.UPDATER_STATE_CHECKING)
        self.notify_observers()

        try:
            r = WebRequest().get(self.version_url)

            r.raise_for_status()
            [int(x) for x in r.content.decode("UTF-8").split("\n")[0].strip().split(".")]  # crash if content is not a number
            self.version_online = "%s" % r.content.decode("UTF-8").split("\n")[0].strip()
            self.notify_observers()

            if self.version_online is not None and self._compare_version_numbers(self.version_online, self.version_local) > 0:
                downloaded_version = 0
                if os.path.exists(os.path.join(SOFTWARE_UPDATE_DIR, "%s.version" % SOFTWARE_UPDATE_FILENAME)):
                    downloaded_version = open(os.path.join(SOFTWARE_UPDATE_DIR, "%s.version" % SOFTWARE_UPDATE_FILENAME), "r").read()
                if self._compare_version_numbers(self.version_online, downloaded_version) > 0:
                    self.state.set(UpdaterState.UPDATER_STATE_DOWNLOADING)
                    executable = SecureDownload().download(self.file_url, self.signature_url)
                    open(os.path.join(SOFTWARE_UPDATE_DIR, SOFTWARE_UPDATE_FILENAME), "wb").write(executable)
                    open(os.path.join(SOFTWARE_UPDATE_DIR, "%s.version" % SOFTWARE_UPDATE_FILENAME), "w").write(self.version_online)
                self.state.set(UpdaterState.UPDATER_STATE_READY_FOR_INSTALL)
                self.update_installed.notify_observers()
            else:
                self._auto_update_timer.last_call_timestamp = now
                self._auto_update_timer.interval = self._max_check_interval_seconds
                self.last_successful_check.set(math.floor(now))
                self._logger.debug("successfully checked for updates")
                self.state.set(UpdaterState.UPDATER_STATE_IDLE)

        except Exception as e:
            self.last_failed_check.set(math.floor(now))
            self._logger.debug(traceback.format_exc())
            self._logger.debug("error while checking for updates, retry in {} seconds".format(self._err_check_interval_seconds))
            self._auto_update_timer.interval = self._err_check_interval_seconds
            self.state.set(UpdaterState.UPDATER_STATE_IDLE)

        self.next_check = math.floor(self._auto_update_timer.last_call_timestamp + self._auto_update_timer.interval)
        self.notify_observers()


    def _compare_version_numbers(self, new_version_number, old_version_number):
        new_split = new_version_number.split(".")
        old_split = old_version_number.split(".")

        if len(old_split) != len(new_split):
            # force update if the version numbers are not comparable or one of them is invalid
            self._logger.error("invalid version number: '{}' or '{}'".format(old_version_number, new_version_number))
            return 1

        for i, new_part in enumerate(new_split):
            if new_part == old_split[i]:
                continue
            elif new_part > old_split[i]:
                return 1
            elif new_part < old_split[i]:
                return -1
            else:
                self._logger.error("program error")
                raise Exception()

        return 0
