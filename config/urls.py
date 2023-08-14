from .files import CONFIG_UPDATE_FILENAME, SOFTWARE_UPDATE_FILENAME

CONFIG_UPDATE_URL   = "https://www.perfect-privacy.com/downloads/%s" % CONFIG_UPDATE_FILENAME
SOFTWARE_UPDATE_URL = "https://www.perfect-privacy.com/downloads/%s" % SOFTWARE_UPDATE_FILENAME
TRAFFIC_JSON_URL    = "https://www.perfect-privacy.com/api/traffic.json"

HOST_IP_MAP = {  # to circumvent dns resolution in some cases
    "www.perfect-privacy.com"       : [ "212.7.210.184","95.211.199.144","185.17.184.3", "37.48.94.55","5.79.98.56", "95.211.146.77", "80.255.7.78","217.114.218.30", "178.162.209.143", "37.58.57.6", "81.95.5.45", "80.255.10.206", "178.255.148.174", "37.59.164.111", "195.138.249.14", "31.204.150.121", "31.204.150.153", "31.204.153.87", "31.204.152.232", "31.204.153.210", "94.242.194.102"],
    "checkip.perfect-privacy.com"   : [ "95.211.186.91" , "178.162.211.99"],
    "v6-checkip.perfect-privacy.com": [ "2001:1af8:4020:a019:2::1", "2a00:c98:2050:a034:3::1"],
    "check.torproject.org"          : [ "116.202.120.181"]
}

