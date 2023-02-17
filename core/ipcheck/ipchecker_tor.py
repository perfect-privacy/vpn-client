import re
from .ipchecker_generic import GenericIPChecker, ApiMalfunctionError

class TorIPChecker(GenericIPChecker):

    _url4 = "https://check.torproject.org/"
    _url6 = None

    def _parse_response(self, response):

        try:
            match = re.search('<p>Your IP address appears to be:  <strong>([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})</strong></p>', response.content)

            public_ip = match.group(1)  # raises an exception on failure

            return public_ip, None, None, None

        except:
            self._logger.error("invalid response: malformed HTML")
            raise ApiMalfunctionError("invalid response")
