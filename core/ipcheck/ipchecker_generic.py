import logging
import time

import requests.exceptions as request_exceptions
from gettext import gettext as _
from threading import RLock, Thread

from core.libs.web import WebRequest
from .ipcheck_result import IPCheckerResult

class GenericIPChecker(object):

    _url4 = None
    _url6 = None

    def __init__(self, fallback_checker=None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._fallback_checker = fallback_checker

    @property
    def supports_ipv4(self):
        return self._url4 is not None

    @property
    def supports_ipv6(self):
        return self._url6 is not None

    def check(self, expected_ipv4_addresses, expected_ipv6_addresses, result4, result6):
        """
        :type expected_ipv4_addresses: list[str]
        :type expected_ipv6_addresses: list[str]
        :rtype: IPCheckerResult
        """
        t4 = Thread(daemon=True, target=self._check_runner, kwargs={"expected_ip_addresses": expected_ipv4_addresses, "get_func": "_get4", "result": result4, "use_alt": True})
        t6 = Thread(daemon=True, target=self._check_runner, kwargs={"expected_ip_addresses": expected_ipv6_addresses, "get_func": "_get6", "result": result6, "use_alt": False})
        t4.start()
        t6.start()
        t4.join()
        t6.join()


    def _check_runner(self, expected_ip_addresses, get_func, result, use_alt=True):
        """
        :type expected_ip_addresses: list[str]
        :type get_func: str
        :param result: the IPCheckerResult to update
        :type result: IPCheckerResult
        """
        public_ip, public_dns, public_city, public_country = None, None, None, None
        successfull = False
        for i in range(2):
            try:
                response = getattr(self, get_func)()
                public_ip, public_dns, public_city, public_country = self._parse_response(response)
                successfull = True
                break
            except:
                time.sleep(1)

        if use_alt is True and ( successfull is False or public_ip is None):
            try:
                response = getattr(self._fallback_checker, get_func)()
                public_ip, public_dns, public_city, public_country = self._fallback_checker._parse_response(response)
            except:
                result.clear()
                return
        if public_ip is None:
            result.clear()
            return
        vpn_connected = public_ip in expected_ip_addresses

        result.update(vpn_connected=vpn_connected,
                      public_ip=public_ip,
                      public_rdns=public_dns,
                      public_city=public_city,
                      public_country=public_country)

    def _parse_response(self, response):
        """
        :return: n-tuple (public_ip, public_dns, public_city, public_country)
        :rtype: (str, str, str, str)
        """
        raise NotImplementedError()

    def _get4(self):
        """
        :rtype: requests.Response
        """
        return self._get(self._url4)

    def _get6(self):
        """
        :rtype: requests.Response
        """
        return self._get(self._url6)

    def _get(self, url):
        """
        :type url: str
        :rtype: requests.Response
        """
        if url is None:
            self._logger.debug("no URL specified")
            raise RuntimeError()
        try:
            response = WebRequest().get(url=url, timeout=3)
        except request_exceptions.ConnectionError:
            self._logger.error("network problem " + url)
            raise ApiNetworkError(_("network problem"))
        except request_exceptions.HTTPError:
            self._logger.error("invalid HTTP response "  + url)
            raise ApiMalfunctionError(_("invalid HTTP response"))
        except request_exceptions.Timeout:
            self._logger.error("request timeout "  + url)
            raise ApiNetworkError(_("request timeout"))
        except request_exceptions.TooManyRedirects:
            self._logger.error("too many redirects " + url)
            raise ApiMalfunctionError(_("too many redirects"))
        except request_exceptions.RequestException as error:
            raise ApiError("{}".format(error.strerror))
        else:
            return response

class ApiNetworkError(Exception):pass
class ApiMalfunctionError(Exception):pass
class ApiError(Exception):pass