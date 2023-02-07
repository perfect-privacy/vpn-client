import random
import logging
import os
import json
from config.paths import CONFIG_DIR
from .vpn_config import VPNServerConfig
from pyhtmlgui import ObservableDict, Observable


# common for Servers and Server Collections
class VpnServerOrGroup(Observable):
    def __init__(self, name):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.name = name
        self.identifier = None
        self.bandwidth_in  = 0
        self.bandwidth_out = 0
        self.bandwidth_max = 0

    @property
    def bandwidth_used_mbit(self):
        if self.bandwidth_in < 0 or self.bandwidth_out < 0:
            return 0
        return ( self.bandwidth_in + self.bandwidth_out ) / 2

    @property
    def bandwidth_used_percent(self):
        return min( int( 100 / self.bandwidth_max * self.bandwidth_used_mbit), 100)

    @property
    def bandwidth_available_percent(self):
        if self.bandwidth_in < 0 and self.bandwidth_out < 0:
            return 0
        return 100 - self.bandwidth_used_percent

    @property
    def country_shortcodes(self):
        return list(set([s.vpn_server_config.country_shortcode for s in self.get_vpn_servers()]))

    def match_identifier(self, identifier):
        if self.identifier == identifier:
            return True
        return False

    def set_bandwidth(self, bandwidth_in, bandwidth_out, bandwidth_max):
        changed = False
        if self.bandwidth_in  != bandwidth_in:
            self.bandwidth_in  = bandwidth_in
            changed = True
        if self.bandwidth_out != bandwidth_out:
            self.bandwidth_out = bandwidth_out
            changed = True
        if self.bandwidth_max != bandwidth_max:
            self.bandwidth_max = bandwidth_max
            changed = True
        if changed is True:
            self.notify_observers()

    def get_vpn_servers(self):
        raise NotImplementedError()


# One VPN Server
class VpnServer(VpnServerOrGroup):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.identifier = "server=%s" % name
        self.vpn_server_config = None

    def add_config(self, vpnConfig):
        self.vpn_server_config = vpnConfig
        self.bandwidth_max = vpnConfig.bandwidth_mbps
        self.notify_observers()

    def search_by_identifier(self, identifer):
        if self.match_identifier(identifer):
            return self
        return None

    def match_filter(self, filter):
        filter = filter.lower()
        if self.name.lower().find(filter) != -1:
            return True
        if self.vpn_server_config.country_name.lower().find(filter) != -1:
            return True
        if self.vpn_server_config.city.lower().find(filter) != -1:
            return True
        if self.vpn_server_config.hostname.lower().find(filter) != -1:
            return True
        if self.vpn_server_config.groupname.lower().find(filter) != -1:
            return True
        return False

    def __repr__(self, prefix=""):
        s = prefix + 'VPN Server %s\n' % self.name
        return s

    def get_vpn_servers(self):
        """
            :rtype: list[VpnServer]
        """
        return [self]

    def get_ipv6s(self):
        return [ self.vpn_server_config.primary_ipv6 ] + self.vpn_server_config.alternative_ipv6
    def get_ipv4s(self):
        return [ self.vpn_server_config.primary_ipv4 ] + self.vpn_server_config.alternative_ipv4

    def __len__(self):
        return 1


# common for collections of Servers
class VpnGroup(VpnServerOrGroup):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.identifier = None

    @property
    def subitems(self):
        raise NotImplementedError()

    def search_by_identifier(self, identifer):
        if self.match_identifier(identifer):
            return self
        if identifer in self.subitems.keys():
            return self.subitems[identifer]
        for _, subitem in self.subitems.items():
            r = subitem.search_by_identifier(identifer)
            if r is not None:
                return r
        return None

    def match_filter(self, filter):
        for _, subitem in self.subitems.items():
            if subitem.match_filter(filter) is True:
                return True
        return False

    def get_vpn_servers(self):
        """
            :rtype: list[VpnServer]
        """
        servers = []
        for _, subitem in self.subitems.items():
            servers.extend(subitem.get_vpn_servers())
        return servers

    def get_ipv6s(self):
        r = []
        for server in self.get_vpn_servers():
            r.extend(server.get_ipv6s())
        return r

    def get_ipv4s(self):
        r = []
        for server in self.get_vpn_servers():
            r.extend(server.get_ipv4s())
        return r


    def __len__(self):
        return len(self.subitems)


# the actual server group classes.
# instanciate Planet, use add_config for add VpnServer config file objects
class VpnGroupCity(VpnGroup):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.identifier = "city=%s" % name
        self.servers = ObservableDict() # server key is hostname

    @property
    def subitems(self):
        return self.servers

    def add_config(self, vpnConfig):
        if vpnConfig.hostname not in self.servers:
            self.servers[vpnConfig.hostname] = VpnServer(vpnConfig.hostname)
            self.servers[vpnConfig.hostname].attach_observer(self._on_server_updated)
        self.servers[vpnConfig.hostname].add_config(vpnConfig)

    def _on_server_updated(self, sender):
        self.set_bandwidth(
            sum([x.bandwidth_in  for _,x in self.servers.items() if x.bandwidth_in  > 0]),
            sum([x.bandwidth_out for _,x in self.servers.items() if x.bandwidth_out > 0]),
            sum([x.bandwidth_max for _,x in self.servers.items() if x.bandwidth_max > 0]),
        )

    def __repr__(self, prefix=""):
        s = prefix + 'VPN City "%s", %s Servers\n' % (self.name, self.subitems.__len__())
        for key, item in self.servers.items():
            s += item.__repr__(prefix + " ")
        return s


class VpnGroupCountry(VpnGroup):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.identifier = "country=%s" % name
        self.citys = ObservableDict()
        self.servers = ObservableDict()


    @property
    def subitems(self):
        return self.citys

    def add_config(self, vpnConfig):
        if vpnConfig.city not in self.citys:
            self.citys[vpnConfig.city] = VpnGroupCity(vpnConfig.city)
            self.citys[vpnConfig.city].attach_observer(self._on_city_updated)
        self.citys[vpnConfig.city].add_config(vpnConfig)
        for _, item in self.citys.items():
            self.servers.update(item.servers)

    def _on_city_updated(self, sender):
        self.set_bandwidth(
            sum([x.bandwidth_in  for _,x in self.citys.items() if x.bandwidth_in  > 0]),
            sum([x.bandwidth_out for _,x in self.citys.items() if x.bandwidth_out > 0]),
            sum([x.bandwidth_max for _,x in self.citys.items() if x.bandwidth_max > 0]),
        )

    def __repr__(self, prefix=""):
        s = prefix + 'VPN Country "%s", %s Citys\n' % (self.name, self.subitems.__len__())
        for key, item in self.citys.items():
            s += item.__repr__(prefix + " ")
        return s


class VpnGroupZone(VpnGroup):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.identifier = "zone=%s" % name
        self.countrys = ObservableDict()
        self.citys = ObservableDict()
        self.servers = ObservableDict()

    @property
    def subitems(self):
        return self.countrys

    def add_config(self, vpnConfig):
        if vpnConfig.country_name not in self.countrys:
            self.countrys[vpnConfig.country_name] = VpnGroupCountry(vpnConfig.country_name)
            self.countrys[vpnConfig.country_name].attach_observer(self._on_country_updated)
        self.countrys[vpnConfig.country_name].add_config(vpnConfig)

        for _, country in self.countrys.items():
            self.citys.update(country.citys)
            for _, city in country.citys.items():
                self.servers.update(city.servers)

    def _on_country_updated(self, sender):
        self.set_bandwidth(
            sum([x.bandwidth_in  for _,x in self.countrys.items() if x.bandwidth_in  > 0]),
            sum([x.bandwidth_out for _,x in self.countrys.items() if x.bandwidth_out > 0]),
            sum([x.bandwidth_max for _,x in self.countrys.items() if x.bandwidth_max > 0]),
        )

    def __repr__(self, prefix=""):
        s = prefix + 'VPN Zone "%s", %s Countrys\n' % (self.name, self.subitems.__len__())
        for key, item in self.countrys.items():
            s += item.__repr__(prefix + " ")
        return s


class VpnGroupPlanet(VpnGroup):
    def __init__(self, name="earth"):
        super().__init__(name)
        self.name = name
        self.identifier = "planet=%s" % name
        self.zones = ObservableDict()
        self.countrys = ObservableDict()
        self.citys = ObservableDict()
        self.servers = ObservableDict()

    @property
    def subitems(self):
        return self.zones

    def add_config(self, vpnConfig):
        if vpnConfig.country_name not in self.zones:
            self.zones[vpnConfig.country_name] = VpnGroupZone(vpnConfig.country_name)
            self.zones[vpnConfig.country_name].attach_observer(self._on_zone_updated)
        self.zones[vpnConfig.country_name].add_config(vpnConfig)

        for _, zone in self.zones.items():
            self.countrys.update(zone.countrys)
            for _, country in zone.countrys.items():
                self.citys.update(country.citys)
                for _, city in country.citys.items():
                    self.servers.update(city.servers)

    def add_bandwidth_data(self, data):
        #{ 'miami.perfect-privacy.com': {'bandwidth_out': 105196, 'bandwidth_max': 1000000, 'timestamp': 1604155926, 'bandwidth_in': 103683}, }
        for _, server in self.servers.items():
            key = server.vpn_server_config.url
            if key not in data and "1." in key:
                key = key.replace("1.",".")
            if key in data:
                server.set_bandwidth(
                    -1 if int(data[key]['bandwidth_in'])  < 0 else int(data[key]['bandwidth_in']  / 1000),
                    -1 if int(data[key]['bandwidth_out']) < 0 else int(data[key]['bandwidth_out'] / 1000),
                    -1 if int(data[key]['bandwidth_max']) < 0 else int(data[key]['bandwidth_max'] / 1000)
                )

    def _on_zone_updated(self, sender):
        self.set_bandwidth(
            sum([x.bandwidth_in  for _,x in self.zones.items() if x.bandwidth_in  > 0]),
            sum([x.bandwidth_out for _,x in self.zones.items() if x.bandwidth_out > 0]),
            sum([x.bandwidth_max for _,x in self.zones.items() if x.bandwidth_max > 0]),
        )

    def load_configs_json(self):
        self._logger.debug("loading config file from {}".format(CONFIG_DIR))
        try:
            servers_data = json.loads(open(os.path.join(CONFIG_DIR, "servers.json"),"r").read())
        except:
            self._logger.debug("Failed to load config file from {}".format(CONFIG_DIR))
            servers_data = []

        for server_data in servers_data:
            vpn_server_config = VPNServerConfig()
            vpn_server_config.load(server_data)
            self.add_config(vpn_server_config)
        #print("%s Configs loaded" % len(servers_data))

    def __repr__(self, prefix=""):
        s = prefix + 'VPN Planet "%s", %s Zones \n' % (self.name, self.subitems.__len__())
        for key, item in self.zones.items():
            s += item.__repr__(" ")
        return s
