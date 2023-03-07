import requests.exceptions as request_exceptions
import logging
from gettext import gettext as _
from config.config import SIG_PUBKEY
from .webrequest import WebRequest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key


class SecureDownload():
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def download(self, file_url, signature_url ):
        file_response = self._download(file_url)
        sig_response  = self._download(signature_url)
        if self.verify_signature(file_response,sig_response) is not True:
            raise Exception("Failed to verify signature")
        self._logger.debug("Signature verified")
        return file_response

    def _download(self, url):
        self._logger.debug("downloading from '{}'".format(url))
        try:
            r = WebRequest().get(url=url)
            if int(r.headers['Content-Length']) != len(r.content):
                raise Exception("Content length failed")
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

        self._logger.debug("Download OK")
        return r.content

    def verify_signature(self, data, signature):
        try:
            public_key = load_pem_public_key(SIG_PUBKEY.encode("UTF-8"), default_backend())
            public_key.verify(
                signature,
                data,
                padding.PKCS1v15(),
                hashes.SHA512(),
            )
        except Exception as e:
            self._logger.debug("Signature check failed! %s" % e )
            return False
        return True



class DownloadError(Exception):
    """ Download failed """

