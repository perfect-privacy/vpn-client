import json
from .ipchecker_generic import GenericIPChecker, ApiMalfunctionError

class PerfectPrivacyIPChecker(GenericIPChecker):

    _url4 = "https://checkip.perfect-privacy.com/json"
    _url6 = "https://v6-checkip.perfect-privacy.com/json"

    def _parse_response(self, response):

        try:
            checkip_json = json.loads(response.content)
            return (checkip_json["IP"],
                    checkip_json["DNS"],
                    checkip_json["CITY"],
                    checkip_json["COUNTRY"])
        except:
            self._logger.error("invalid response: malformed JSON")
            raise ApiMalfunctionError(("invalid response: malformed JSON"))
