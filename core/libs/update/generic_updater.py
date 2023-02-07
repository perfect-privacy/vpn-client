import logging
from threading import RLock
import math

from .updater_state import UpdaterState
from core.libs.perpetual_timer import PerpetualTimer
from core.libs.permanent_property import PermanentProperty

from pyhtmlgui import Observable


class GenericUpdater(Observable):

    def __init__(self, file_url, signature_url, version_url, download_directory, min_check_interval_seconds=5 * 60, max_check_interval_seconds=7 * 24 * 60 * 60,
                 err_check_interval_seconds=10 * 60):

        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

        self.file_url = file_url
        self.signature_url = signature_url
        self.version_url = version_url
        self.download_directory = download_directory
        self.last_successful_check = PermanentProperty(self.__class__.__name__ + ".last_successful_check", 0)
        self.last_failed_check = PermanentProperty(self.__class__.__name__ + ".last_failed_check", 0)
        self._min_check_interval_seconds = min_check_interval_seconds
        self._max_check_interval_seconds = max_check_interval_seconds
        self._err_check_interval_seconds = err_check_interval_seconds

        self.state = UpdaterState()

        self.update_installed = Observable()

        self._lock = RLock()
        self._auto_update_timer = PerpetualTimer(
            self._check_for_updates,
            self._max_check_interval_seconds if self.last_successful_check.get() else self._err_check_interval_seconds,
            self.last_successful_check.get())

        self.next_check = None
        self.version_online = None
        self.version_local  = None

    def _check_for_updates(self):
        raise NotImplementedError()

    def enable(self):
        self._logger.debug("enabling")
        self._auto_update_timer.enable()
        self.next_check = math.floor(self._auto_update_timer.last_call_timestamp + self._auto_update_timer.interval)
        self.notify_observers()

    def disable(self):
        self._logger.debug("disabling")
        self._auto_update_timer.disable()
        self.next_check = None
        self.notify_observers()

    def check_now(self):
        self.enable()
        self._auto_update_timer.call_now()



class UpdateCancelledError(Exception):
    """ Update cancelled """



'''
class GenericFileUpdater(object):

    def __init__(self, downloader, file_name, downloaded_update_directory, last_successful_check=None,
                 min_check_interval_seconds=5*60, max_check_interval_seconds=7*24*60*60, err_check_interval_seconds=10*60,
                 allow_downgrade=False):
        """
        :type downloader: daemon.api.downloader.Downloader
        """
        self._logger = logging.getLogger(self.__class__.__name__)

        self._downloader = downloader
        self._update_file_name = file_name
        self._downloaded_update_directory = downloaded_update_directory
        self._last_successful_check = last_successful_check
        self._min_check_interval_seconds = min_check_interval_seconds
        self._max_check_interval_seconds = max_check_interval_seconds
        self._err_check_interval_seconds = err_check_interval_seconds
        self._allow_downgrade = allow_downgrade

        self.state = UpdaterState()
        self.state.on_change.connect(self._on_updater_state_change)
        self._update_thread = None

        self.on_last_successful_check_change = Signal()

        self._lock = RLock()
        self._auto_update_timer = PerpetualTimer(
            self._auto_update_worker,
            self._max_check_interval_seconds if self._last_successful_check else self._err_check_interval_seconds,
            self._last_successful_check)

        self._installed_version_number = self._get_installed_version_number()
        self._downloaded_update_version_number = self._get_downloaded_update_version_number()
        self._update_is_available_online = False
        self._online_available_version_number = None
        self._online_available_sha256 = None

        self._clear_already_installed_update()

    @property
    def last_successful_check(self):
        return self._last_successful_check

    def enable(self):
        self._logger.debug("enabling")
        self._auto_update_timer.enable()
        self.next_check = math.floor(self._auto_update_timer.last_call_timestamp + self._auto_update_timer.interval)


    def disable(self):
        self._logger.debug("disabling")
        self._auto_update_timer.disable()
        self.next_check = None

    def _auto_update_worker(self):
        if self._update_thread and self._update_thread.is_alive():
            self._logger.debug("can not start a check for updates: still running")
            return

        if self.update_is_available_on_disk:
            self._logger.debug("checking for updates cancelled: update already downloaded")
            self.state.set(UpdaterState.UPDATER_STATE_READY_FOR_INSTALL)
            return

        self._logger.debug("starting checking for updates and updating")
        try:
            self._check_for_updates_worker()

            if self.state.main_state == UpdaterState.UPDATER_STATE_UPDATE_AVAILABLE:
                self._download_updates_worker()

            now = datetime.now().timestamp()
            self._auto_update_timer.last_call_timestamp = now
            self._auto_update_timer.interval = self._max_check_interval_seconds
            self._last_successful_check = math.floor(now)
            self.on_last_successful_check_change.send(self)
            self._logger.debug("successfully checked for updates")
        except (UpdateCancelledError, DownloadError) as e:
            self._logger.debug(
                "error while checking for updates, retry in {} seconds".format(self._err_check_interval_seconds))
            self._auto_update_timer.interval = self._err_check_interval_seconds
        except:
            self._auto_update_timer.interval = self._err_check_interval_seconds
            self._logger.error("unexpected exception while checking for updates")
            self._logger.debug(traceback.format_exc())
            reporter.report_error(traceback=traceback.format_exc())

    def _get_installed_version_number(self):
        raise NotImplementedError()

    @property
    def installed_version_number(self):
        return self._installed_version_number

    def _get_downloaded_update_version_number(self):
        version_number = None
        if self.update_is_available_on_disk:
            self._logger.debug("there's an update available on disk")
            try:
                update_path, version_path = self._get_update_and_version_paths()
                with open(version_path, "r") as f:
                    version_number = f.readline(1024).strip()
                self._logger.debug("the version number of that update is: {}".format(version_number))
            except:
                self._logger.debug("an error occurred while reading the available update version number from file")
                self._logger.debug(traceback.format_exc())

        return version_number

    @property
    def downloaded_update_version_number(self):
        return self._downloaded_update_version_number

    @property
    def online_available_version_number(self):
        return self._online_available_version_number

    def _get_update_and_version_paths(self):
        update_path = os.path.join(self._downloaded_update_directory, self._update_file_name)
        version_path = update_path + ".version"
        return update_path, version_path

    @property
    def update_is_available_on_disk(self):
        update_path, version_path = self._get_update_and_version_paths()
        return os.path.exists(update_path) and os.path.exists(version_path)

    def install_updates_if_available(self):
        if not self.update_is_available_on_disk or not self._downloaded_update_version_number:
            self._logger.debug("no downloaded update available, nothing to do")
            return
        self._install_update()
        self._installed_version_number = self._get_installed_version_number()
        self._downloaded_update_version_number = self._get_downloaded_update_version_number()

    def _install_update(self):
        raise NotImplementedError()

    def _clear_already_installed_update(self):
        if self.installed_version_number == self.downloaded_update_version_number:
            self._logger.debug("removing already installed update")
            try:
                update_path, version_path = self._get_update_and_version_paths()
                os.remove(update_path)
                os.remove(version_path)
            except OSError:
                self._logger.error("unable to remove update files")
                reporter.report_error(traceback=traceback.format_exc())
            self._downloaded_update_version_number = None

    def request_check_and_update(self):
        now = datetime.now().timestamp()
        if self._last_successful_check:
            time_since_last_successful_check = now - self._last_successful_check
            self._logger.debug("time since last successful check: {}s".format(time_since_last_successful_check))
            if time_since_last_successful_check < self._min_check_interval_seconds:
                self._logger.debug("checking for updates cancelled: minimum interval ({}s) not exceeded".format(
                    self._min_check_interval_seconds))
                return
        self._auto_update_timer.call_now()

    def _check_for_updates_worker(self):
        self._logger.debug("checking for updates")

        self.state.set(UpdaterState.UPDATER_STATE_CHECKING)

        temp_download_dir = None
        try:
            temp_download_dir = self._create_temporary_download_directory()

            available_update_version_number, file_sha256 = self._download_version(
                temp_download_dir, self._update_file_name)

            if not available_update_version_number:
                self._logger.debug("couldn't get online available version number")
                self.state.set(UpdaterState.UPDATER_STATE_UPDATE_FAILED)
                raise DownloadError()
            self._online_available_version_number = available_update_version_number
            self._online_available_sha256 = file_sha256

            if (available_update_version_number == self._downloaded_update_version_number and
                    self._downloaded_update_version_number is not None):
                self._logger.debug("available update ({}) already downloaded".format(available_update_version_number))
                self.state.set(UpdaterState.UPDATER_STATE_READY_FOR_INSTALL)
                return

            comparision = self._compare_version_numbers(new_version_number=available_update_version_number,
                                                        old_version_number=self._installed_version_number)
            if comparision == 0:
                self._logger.debug("already up to date")
                self._update_is_available_online = False
                self.state.set(UpdaterState.UPDATER_STATE_NO_UPDATE_REQUIRED)
            elif comparision < 0:
                self._logger.debug("downgrade available")
                if self._allow_downgrade:
                    self._update_is_available_online = True
                    self.state.set(UpdaterState.UPDATER_STATE_UPDATE_AVAILABLE)
                else:
                    self._logger.debug("downgrade not allowed")
                    self._update_is_available_online = False
                    self.state.set(UpdaterState.UPDATER_STATE_NO_UPDATE_REQUIRED)
            else:
                self._logger.debug("update available")
                self._update_is_available_online = True
                self.state.set(UpdaterState.UPDATER_STATE_UPDATE_AVAILABLE)
        except DownloadError as e:
            self._logger.debug("checking for updates failed")
            self.state.set(UpdaterState.UPDATER_STATE_UPDATE_FAILED, sub_message=str(e))
            raise e
        except Exception as e:
            self._logger.debug("an error occurred while checking for updates")
            self._logger.debug(traceback.format_exc())
            self.state.set(UpdaterState.UPDATER_STATE_UPDATE_FAILED)
            raise e
        finally:
            if temp_download_dir:
                self._logger.debug("removing temporary download directory at: {}".format(temp_download_dir))
                shutil.rmtree(temp_download_dir, ignore_errors=True)

    def _compare_version_numbers(self, new_version_number, old_version_number):
        """
        :return: 0 if equal, negative if new_version_number < old_version_number, positive if new_version_number > old_version_number 
        """
        raise NotImplementedError()

    def _download_updates_worker(self):
        self._logger.debug("downloading update")

        if self.online_available_version_number and not self._update_is_available_online:
            self._logger.info("downloading update cancelled: there's no update available")
            self.state.set(UpdaterState.UPDATER_STATE_IDLE)
            raise UpdateCancelledError()

        if self.online_available_version_number is None or not self._online_available_sha256:
            self._logger.info("downloading update cancelled: didn't check for update previously")
            self.state.set(UpdaterState.UPDATER_STATE_IDLE)
            raise UpdateCancelledError()

        temp_download_dir = None
        try:
            temp_download_dir = self._create_temporary_download_directory()

            # download the config file, verify the checksum and the signature
            self.state.set(UpdaterState.UPDATER_STATE_DOWNLOADING)
            temp_file_path = self._download_and_verify(
                temp_download_dir, self._update_file_name, self._online_available_sha256)

            # move downloaded and verified file to install directory
            if not os.path.exists(self._downloaded_update_directory):
                try:
                    os.makedirs(self._downloaded_update_directory, mode=0o755)
                    self._logger.debug("created directory at: {}".format(self._downloaded_update_directory))
                except:
                    self._logger.error("Couldn't create directory: {}".format(self._downloaded_update_directory))
                    raise DownloadError()
            update_path, version_path = self._get_update_and_version_paths()
            shutil.move(temp_file_path, update_path)

            # write version number to file for later use in _get_downloaded_update_version_number
            # the file has been successfully checked against the sha256 which has been read from the same version file,
            # so the downloaded file has the same version number
            with open(version_path, "w") as f:
                f.write(self._online_available_version_number)
            self._downloaded_update_version_number = self._online_available_version_number

            self._logger.debug("downloaded update is ready for install")
            self.state.set(UpdaterState.UPDATER_STATE_READY_FOR_INSTALL)
        except Exception as e:
            self._logger.debug("an error occurred while downloading the update")
            self._logger.debug(traceback.format_exc())
            self.state.set(UpdaterState.UPDATER_STATE_UPDATE_FAILED)
            raise e
        finally:
            if temp_download_dir:
                self._logger.debug("removing temporary download directory at: {}".format(temp_download_dir))
                shutil.rmtree(temp_download_dir, ignore_errors=True)

    def _create_temporary_download_directory(self, prefix=None):
        self._logger.debug("creating temporary directory")
        temp_download_dir = mkdtemp(prefix=prefix)
        self._logger.debug("the temporary directory will be at '{}'".format(temp_download_dir))
        if not os.path.exists(temp_download_dir):
            try:
                os.makedirs(temp_download_dir, mode=0o755)
                self._logger.debug("created temporary download directory at: {}".format(temp_download_dir))
            except:
                self._logger.error("Couldn't create download directory: {}".format(temp_download_dir))
                raise DownloadError()
        return temp_download_dir

    def _download_version(self, temp_download_dir, download_file):
        # download version file
        self._logger.debug("downloading version file")
        self._logger.debug("temp_download_dir: {}".format(temp_download_dir))
        self._logger.debug("download_file: {}".format(download_file))
        version_path = self._downloader.download_and_save_to_file(
            file_name="{}.version".format(download_file), dest_dir=temp_download_dir,
            expected_max_content_length=1024)  # max 1kb
            #expected_content_type='text/plain', expected_max_content_length=1024)  # max 1kb

        # get version and sha256sum from version file
        self._logger.debug("parsing version file")
        version_number = None
        sha256_of_update = None
        with open(version_path, "r") as version_file:
            for line in version_file:
                if version_number is None:
                    version_number = line.strip()
                if line.strip().startswith("sha256:"):
                    sha256_of_update = line.replace("sha256:", "").strip()
        if version_number is None or sha256_of_update is None:
            raise DownloadError(_("invalid version file"))
        self._logger.debug("parsing version file finished: version: {}, sha256: {}".format(version_number, sha256_of_update))

        return version_number, sha256_of_update

    def _download_and_verify(self, temp_download_dir, download_file, config_sha256):

        # download signature
        self._logger.debug("downloading signature file")
        sig_path = self._downloader.download_and_save_to_file(
            file_name="{}.sig".format(download_file), dest_dir=temp_download_dir,
            expected_max_content_length=1024*5)  # max 5kb
            #expected_content_type='application/octet-stream', expected_max_content_length=1024*5)  # max 5kb
        self._logger.debug("signature file download finished")

        # download file
        self._logger.debug("downloading file: {}".format(download_file))
        downloaded_file_path = self._downloader.download_and_save_to_file(
            file_name=download_file, dest_dir=temp_download_dir,
            expected_max_content_length=1024*1024*100)  # max 100mb
            #expected_content_type='application/octet-stream', expected_max_content_length=1024*1024*100)  # max 100mb

        # verify sha256sum
        sha256_ok = self._downloader.verify_sha256sum(downloaded_file_path, config_sha256)
        if not sha256_ok:
            self._logger.error("sha256sum check failed!")
            raise DownloadError(_("Verifying the checksum failed. Please try again later."))
        self._logger.debug("sha256sum check passed")

        # verify signature
        self._logger.debug("verifying signature")
        signature_ok = self._downloader.verify_signature(downloaded_file_path, sig_path)
        if not signature_ok:
            self._logger.error("signature check failed!")
            raise DownloadError(_("Verifying the signature failed. Please try again later."))
        self._logger.debug("signature check passed")

        return downloaded_file_path

    def _unzip(self, zip_path, unzip_dir):
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
            raise DownloadError(_("Error extracting ZIP file: {}").format(str(e)))
        self._logger.debug("unzipping done")

    def shutdown(self):
        self._auto_update_timer.shutdown()

    def _on_updater_state_change(self, sender, is_doing_something, message):
        self._logger.info(message)
'''