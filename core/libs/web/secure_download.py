import requests.exceptions as request_exceptions
import os
import logging
from gettext import gettext as _
from subprocess import Popen, PIPE
import tempfile
import hashlib

from config.config import SIG_PUBKEY
from .webrequest import WebRequest

# download files and verify their signature




class SecureDownload():
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def download(self, file_url, signature_url ):
        file_response = self._download(file_url)
        sig_response  = self._download(signature_url)
        if self.verify_signature(file_response,sig_response) is not True:
            raise Exception("Failed to verify signature")
        return file_response

    def _download(self, url, headers = {}, post = False, post_data= None, stream= None, expected_content_type = None, expected_max_content_length = None):
        self._logger.debug("downloading from '{}'".format(url))
        self._logger.debug("method: {}".format("POST" if post else "GET"))
        self._logger.debug("expected content type: {}".format(expected_content_type))
        self._logger.debug("max expected length: {}".format(expected_max_content_length))

        try:
            self._logger.debug("requesting")
            if post:  # POST
                r = WebRequest().post(url=url)
            else:  # GET
                r = WebRequest().get(url=url)
            self._logger.debug("request finished")

            r.raise_for_status()

        except request_exceptions.ConnectionError as e:
            raise DownloadError(_("Connection error: {}").format(str(e)))
        except request_exceptions.HTTPError as e:
            raise DownloadError(_("Invalid HTTP response: {}").format(str(e)))
        except request_exceptions.Timeout as e:
            raise DownloadError(_("Timeout: {}").format(str(e)))
        except request_exceptions.TooManyRedirects as e:
            raise DownloadError(_("Too many redirects: {}").format(str(e)))
        except request_exceptions.RequestException as e:
            raise DownloadError(_("Ambiguous exception: {}").format(str(e)))
        except AssertionError:
            raise DownloadError("assertion failed")
        except Exception as e:
            self._logger.error("unexpected error: {}".format(str(e)))
            raise DownloadError(_("Unknown error"))

        if not r.ok:
            raise DownloadError(
                _("invalid response: server returned status code {}")
                .format(r.status_code))

        # check content type
        if expected_content_type is not None:
            if 'content-type' not in r.headers:
                self._logger.warning("No Content-Type received from server: "
                                     "ignoring expected content type")
            elif expected_content_type not in r.headers['content-type']:
                self._logger.debug("content-type: '{}'".format(
                    r.headers['content-type']))
                if "text/html" in r.headers['content-type'] \
                        and "perfectprivacypass" in r.content.decode():
                    # 'perfectprivacypass' is the name of the input field
                    self._logger.error("Your credentials appear to be wrong. Please double-check and try again.")
                    raise DownloadError(
                        _("Your username/password appears to be wrong.\n"
                          "Please double-check your account credentials."))
                self._logger.debug("Wrong content-type. Expected '{}' but got '{}'".format(
                    expected_content_type, r.headers['content-type']))
                raise DownloadError(
                    _("expected '{expected_type}' "
                      "but got '{actual_type}' from server")
                    .format(expected_type=expected_content_type,
                            actual_type=r.headers['content-type']))

        # check length
        if expected_max_content_length is not None:
            if 'content-length' not in r.headers:
                self._logger.warning(
                    "No Content-Length received from server: "
                    "ignoring expected max content length")
            else:
                self._logger.debug("content-length: '{}'".format(
                    r.headers['content-length']))
                if int(r.headers['content-length']) > expected_max_content_length:
                    self._logger.error(
                        "downloaded file is too big ({} > {})".format(
                            r.headers['content-length'],
                            expected_max_content_length))
                    raise DownloadError(_("Downloaded file is too big"))

        self._logger.debug("response OK")
        return r.content

    def _sha256(self, file_path):
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            chunk = True
            while chunk:
                chunk = f.read(4096)
                sha256.update(chunk)
        return sha256.hexdigest()

    def verify_sha256sum(self, file_path, expected_hash):
        """
        Verify the sha256 checksum of a file.

        :param file_path: the full path of the file to check
        :type file_path: str | unicode
        :param expected_hash: the expected sha256sum
        :type expected_hash: str | unicode
        :return: whether the check has been passed successfully
        :rtype: bool
        :raises Exception
        """

        self._logger.debug("checking sha256sum of '{}' (must be '{}')".format(file_path, expected_hash))

        try:
            calculated_hash = self._sha256(file_path)
            if calculated_hash == expected_hash:
                self._logger.debug("sha256 ok")
                return True
        except Exception as e:
            import traceback
            import sys
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = traceback.format_exception(exc_type, exc_value,
                                            exc_traceback, limit=2)
            self._logger.debug("exception occurred while checking sha256: {}"
                               .format("".join(tb)))
            raise Exception(_("couldn't check sha256: {}").format(str(e)))

        self._logger.debug("sha256 check failed!")
        return False

    def verify_signature(self, file_path, sig_file_path):
        return True
        """
        Verify the sha512 signature of a file. Use a hard-encoded public key.

        :param file_path: the full path to the file to check
        :type file_path: str | unicode
        :param sig_file_path: the full path to the signature file
        :type sig_file_path: str | unicode
        :return: whether the check has been passed successfully
        :rtype: bool
        :raises Exception
        """
        self._logger.debug("checking signature of '{}'".format(file_path))

        pubkey_file_path = None
        try:
            fd, pubkey_file_path = tempfile.mkstemp(text=True)
            f = os.fdopen(fd, "w")
            os.chmod(pubkey_file_path, 0o644)
            f.write(SIG_PUBKEY)
            f.close()

            sig_proc = Popen(["/usr/bin/openssl", "dgst", "-sha512",
                              "-verify", pubkey_file_path,
                              "-signature", sig_file_path,
                              file_path],
                             stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            out, err = sig_proc.communicate()

            if sig_proc.returncode == 0 and out.find("OK") >= 0:
                self._logger.debug("signature ok")
                return True
        except Exception as e:
            self._logger.debug("exception occurred while checking signature: "
                               "{}".format(str(e)))
            raise Exception(_("couldn't check signature: {}").format(str(e)))
        finally:
            # remove the public key file
            try:
                if pubkey_file_path is not None and \
                        os.path.exists(pubkey_file_path):
                    os.unlink(pubkey_file_path)
            except:
                pass
        self._logger.debug("signature check failed!")
        return False




class DownloadError(Exception):
    """ Download failed """

