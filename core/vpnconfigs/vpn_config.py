from core.libs import translations
import logging

class VPNServerConfig(object):

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

        self.zone = ""
        self.country_name = ""
        self.country_shortcode = ""
        self.city = ""
        self.location = {
            "lati" : "",
            "longi" : "",
        }
        self.hostname = ""
        self.groupname = ""
        self.url = ""

        self.bandwidth_mbps = 0

        self.primary_ipv4 = ""
        self.primary_ipv6 = ""
        self.alternative_ipv4 = []
        self.alternative_ipv6 = []
        self.dns_ipv4 = ""
        self.dns_ipv6 = ""

        self.ssh_fingerprint = ""
        self.ssh_fingerprint_algorithm = ""

        self.block_p2p = False


    @property
    def all_ips(self):
        return [self.primary_ipv4] + self.alternative_ipv4

    @property
    def all_ips6(self):
        return [self.primary_ipv6] + self.alternative_ipv6

    @property
    def stunnel_ip(self):
        try:
            return self.alternative_ipv4[0]
        except IndexError:
            return None

    @property
    def ssh_ip(self):
        try:
            return self.primary_ipv4
        except IndexError:
            return None

    @property
    def obfs3_ip(self):
        try:
            return self.alternative_ipv4[2]
        except IndexError:
            return None

    @property
    def translated_city(self):
        return translations.get_translated_city(self.city)


    def load(self, server_data):
        if "groupname" not in server_data:
            server_data["groupname"] = server_data["city"]

        self.country_name      = server_data["country_name"]
        if self.country_name == "U.S.A":
            self.country_name = "United States of America"
        self.country_shortcode = server_data["country_shortcode"]
        self.city              = server_data["city"]
        self.location["lati"]  = server_data["location"]["lati"]
        self.location["longi"] = server_data["location"]["longi"]
        self.hostname          = server_data["hostname"]
        self.groupname         = server_data["groupname"]
        self.url               = server_data["url"]
        self.bandwidth_mbps    = int(server_data["bandwidth"])
        self.primary_ipv4      = server_data["primary_ipv4"]
        self.primary_ipv6      = server_data["primary_ipv6"]
        self.alternative_ipv4  = server_data["alternative_ipv4"]
        self.alternative_ipv6  = server_data["alternative_ipv6"]
        self.dns_ipv4          = server_data["dns_ipv4"]
        self.dns_ipv6          = server_data["dns_ipv6"]
        self.ssh_fingerprint   = server_data["ssh_fingerprint"]
        self.block_p2p         = server_data["block_p2p"]


    def __str__(self):
        return (
            self.__class__.__name__ +
            "<city={city}, country_code={country_code}, hostname={hostname}, "
            "bandwidth_mbps={bandwidth_mbps}, primary_ips={primary_ips}, primary_ips6={primary_ips6}, "
            "alt_ips={alt_ips}, alt_ips6={alt_ips6}, "
            "dns={dns}, dns6={dns6}, ".format(
                city=self.city, country_code=self.country_shortcode, hostname=self.hostname,
                bandwidth_mbps=self.bandwidth_mbps, primary_ips=self.primary_ipv4, primary_ips6=self.primary_ipv6,
                alt_ips=self.alternative_ipv4, alt_ips6=self.alternative_ipv6, dns=self.dns_ipv4, dns6=self.dns_ipv6))
