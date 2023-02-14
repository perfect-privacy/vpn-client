import os
import shutil
from zipfile import ZipFile, BadZipfile, LargeZipFile
from datetime import datetime
import math
import traceback
from core.libs.update.updater_state import UpdaterState
from config.paths  import CONFIG_DIR, CONFIG_UPDATE_DIR
from config.urls import CONFIG_UPDATE_URL
from core.libs.web import WebRequest
from core.libs.web import SecureDownload
from core.libs.update import GenericUpdater

class ConfigUpdater(GenericUpdater):
    def __init__(self, core,
                 min_check_interval_seconds=5*60,
                 max_check_interval_seconds=7*24*60*60,
                 err_check_interval_seconds=10*60):

        self.core = core
        super(ConfigUpdater, self).__init__(
            file_url = CONFIG_UPDATE_URL,
            signature_url  = CONFIG_UPDATE_URL + ".sig",
            version_url  = CONFIG_UPDATE_URL + ".version",
            download_directory  = CONFIG_UPDATE_DIR,
            min_check_interval_seconds = min_check_interval_seconds,
            max_check_interval_seconds = max_check_interval_seconds,
            err_check_interval_seconds = err_check_interval_seconds)
        try:
            self.version_local = open(os.path.join(CONFIG_DIR, "version"), "r").read()
        except:
            self._logger.debug("Failed to load config version")
            self.version_local = None

    def _check_for_updates(self):
        if self.state.get() != UpdaterState.UPDATER_STATE_IDLE:
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

            self.version_online = "%s" % int(r.content.decode("UTF-8").split("\n")[0].strip()) # crash if version is not  is a number
            self.notify_observers()

            if self.version_online is not None:
                if self._compare_version_numbers(self.version_online, self.version_local) > 0:
                    self.state.set(UpdaterState.UPDATER_STATE_DOWNLOADING)
                    zipfile_content = SecureDownload().download(self.file_url, self.signature_url)
                    self.state.set(UpdaterState.UPDATER_STATE_INSTALLING)
                    self._install_update(zipfile_content)
                    self.update_installed.notify_observers()
            self._auto_update_timer.last_call_timestamp = now
            self._auto_update_timer.interval = self._max_check_interval_seconds
            self.last_successful_check.set( math.floor(now))

            self._logger.debug("successfully checked for updates")
        except Exception as e:
            self.last_failed_check.set(math.floor(now))
            self._logger.debug(traceback.format_exc())
            self._logger.debug(   "error while checking for updates, retry in {} seconds".format(self._err_check_interval_seconds))
            self._auto_update_timer.interval = self._err_check_interval_seconds
        self.next_check = math.floor(self._auto_update_timer.last_call_timestamp + self._auto_update_timer.interval)
        self.state.set(UpdaterState.UPDATER_STATE_IDLE)
        self.notify_observers()

    def _compare_version_numbers(self, new_version_number, old_version_number):
        try:
            new_version_number = int(new_version_number)
            old_version_number = int(old_version_number)
        except (ValueError, TypeError, Exception):
            self._logger.error("invalid config version number: '{}' or '{}'".format( old_version_number, new_version_number))
            # force update if the version numbers are not comparable or one of them is invalid
            return 1

        if new_version_number == old_version_number:
            return 0
        elif new_version_number > old_version_number:
            return 1
        elif new_version_number < old_version_number:
            return -1
        else:
            self._logger.error("program error")
            raise Exception()

    def _install_update(self, zipfile_content):
        try:
            if os.path.exists(CONFIG_UPDATE_DIR):
                shutil.rmtree(CONFIG_UPDATE_DIR)
                os.mkdir(CONFIG_UPDATE_DIR)

            zipfile = os.path.join(CONFIG_UPDATE_DIR, "update.zip")
            open(zipfile,"wb").write(zipfile_content)

            self._logger.debug("unpacking zip file")
            self.__unzip(zipfile, CONFIG_UPDATE_DIR)
            os.remove(zipfile)

            self._logger.debug("removing deprecated config files")
            if os.path.exists(CONFIG_DIR):
                shutil.rmtree(CONFIG_DIR)

            self._logger.debug("moving unzipped config files into place")
            shutil.move(CONFIG_UPDATE_DIR, CONFIG_DIR)
            self.version_local = open(os.path.join(CONFIG_DIR, "version"), "r").read()

        except Exception as e:
            raise e
        finally:
            if os.path.exists(CONFIG_UPDATE_DIR):
                shutil.rmtree(CONFIG_UPDATE_DIR, ignore_errors=True)

    def __unzip(self, zip_path, unzip_dir):
        self._logger.debug("unzipping '{}' to '{}'".format(zip_path, unzip_dir))
        try:
            if not os.path.exists(unzip_dir):
                os.makedirs(unzip_dir, mode=0o755)
            with ZipFile(zip_path, 'r') as z:
                for filename in z.namelist():
                    # save all files into one directory (without sub dirs)
                    flattened_path = os.path.join(unzip_dir, os.path.basename(filename))
                    if os.path.isdir(flattened_path):  # ignore directories
                        continue
                    with open(flattened_path, 'wb') as f:  # write file
                        os.chmod(flattened_path, 0o644)
                        f.write(z.open(filename).read())
        except (BadZipfile, LargeZipFile, Exception) as e:
            raise Exception("Error extracting ZIP file: {}".format(str(e)))
        self._logger.debug("unzipping done")


