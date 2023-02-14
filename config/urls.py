from .files import CONFIG_UPDATE_FILENAME, SOFTWARE_UPDATE_FILENAME

CONFIG_UPDATE_URL   = "https://www.perfect-privacy.com/downloads/%s" % CONFIG_UPDATE_FILENAME
SOFTWARE_UPDATE_URL = "https://www.perfect-privacy.com/downloads/%s" % SOFTWARE_UPDATE_FILENAME
TRAFFIC_JSON_URL    = "https://www.perfect-privacy.com/api/traffic.json"

HOST_IP_MAP = {  # to circumvent dns resolution in some cases
    "www.perfect-privacy.com"       : [ "217.114.218.30", "31.204.152.232"],
    "checkip.perfect-privacy.com"   : [ "95.211.186.91" , "178.162.211.99"],
    "v6-checkip.perfect-privacy.com": [ "2001:1af8:4020:a019:2::1", "2a00:c98:2050:a034:3::1"],
    "check.torproject.org"          : [ "116.202.120.181"]
}

