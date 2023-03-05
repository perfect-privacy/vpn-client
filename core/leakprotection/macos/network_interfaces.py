from core.libs.subcommand import SubCommand
import random

class NetworkInterface():
    def __init__(self, core, name, all_ipv4_dns_servers, all_ipv6_dns_servers):
        self.core = core
        self.name = name
        self.dns_servers_v4 = [] # currently set, read from system
        self.dns_servers_v6 = []
        self.all_ipv4_dns_servers = all_ipv4_dns_servers
        self.all_ipv6_dns_servers = all_ipv6_dns_servers
        self.dnsleakprotection_enabled = False

    def enableDnsLeakProtection(self):
        dnsservers = []
        if self.core.settings.leakprotection.use_custom_dns_servers.get() is True:
            dnsservers = [self.core.settings.leakprotection.custom_dns_server_1.get(), self.core.settings.leakprotection.custom_dns_server_2.get()]
            dnsservers = [x.strip() for x in dnsservers if x.strip() != ""]
            dnsservers.sort()
            if len(dnsservers) > 0:
                if dnsservers == sorted(self.dns_servers_v4 + self.dns_servers_v6):
                    return

        if len(dnsservers) == 0:
            existing_servers = set(self.dns_servers_v4 + self.dns_servers_v6)
            if len(existing_servers) > 0 and existing_servers.issubset(self.all_ipv4_dns_servers + self.all_ipv6_dns_servers):
                return
            dnsservers = [random.choice(self.all_ipv4_dns_servers), random.choice(self.all_ipv4_dns_servers), random.choice(self.all_ipv6_dns_servers), random.choice(self.all_ipv6_dns_servers)]

        if len(dnsservers) > 0:
            self.dnsleakprotection_enabled = True
            _, _, _ = SubCommand().run('/usr/sbin/networksetup', args=['-setdnsservers'   , self.name] + dnsservers)
            _, _, _ = SubCommand().run('/usr/sbin/networksetup', args=['-setsearchdomains', self.name, "local"] )

    def disableDnsLeakProtection(self):
        all_current_dns = self.dns_servers_v4 + self.dns_servers_v6
        has_pp_dns = False
        if len(all_current_dns) > 0:
            for current_dns in all_current_dns:
                if current_dns in (self.all_ipv4_dns_servers + self.all_ipv6_dns_servers):
                    has_pp_dns = True
        if has_pp_dns is True or self.dnsleakprotection_enabled is True:
            self.dnsleakprotection_enabled = False
            _, _, _ = SubCommand().run('/usr/sbin/networksetup', args=['-setdnsservers'   , self.name, "Empty"])
            _, _, _ = SubCommand().run('/usr/sbin/networksetup', args=['-setsearchdomains', self.name, "Empty"] )

    def disableIpv6(self):
        success, stdout, stderr = SubCommand().run("/usr/sbin/networksetup", args=["-setv6off", self.name])

    def enableIpv6(self):
        success, stdout, stderr = SubCommand().run("/usr/sbin/networksetup", args=["-setv6automatic", self.name])

    def __str__(self):
        data = []
        data.append("name: %s" % self.name)
        data.append("dns_servers_v4: %s" % self.dns_servers_v4)
        data.append("dns_servers_v6: %s" % self.dns_servers_v6)
        return "\n".join(data)

class NetworkInterfaces():

    def __init__(self,core ):
        self.core = core
        self.networkinterfaces = []
        self._load()

    def _load(self):
        if self.core is not None:
            all_ipv4_dns_servers = [item.vpn_server_config.dns_ipv4 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv4 != "" and item.vpn_server_config.bandwidth_mbps > 500 and item.bandwidth_available_percent > 0]
            all_ipv6_dns_servers = [item.vpn_server_config.dns_ipv6 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv6 != "" and item.vpn_server_config.bandwidth_mbps > 500 and item.bandwidth_available_percent > 0]
        else:
            all_ipv4_dns_servers = []
            all_ipv6_dns_servers = []


        self.networkinterfaces = []
        success, stdout, stderr = SubCommand().run("/usr/sbin/networksetup", args=["-listallnetworkservices"])
        lines = stdout.decode("utf-8").split("\n")
        if len(lines) > 1:
            for line in lines[1:]:
                name = line.strip()
                if name == "":
                    continue
                ni = NetworkInterface(self.core, name, all_ipv4_dns_servers, all_ipv6_dns_servers)
                self.networkinterfaces.append(ni)
                success, stdout, stderr = SubCommand().run("/usr/sbin/networksetup", args=["-getdnsservers", name])
                stdout = stdout.decode("utf-8")
                if "There aren't any DNS Servers set" not in stdout:
                    for line in stdout.split("\n"):
                        if ":" in line:
                            ni.dns_servers_v6.append(line.strip())
                        elif "." in line:
                            ni.dns_servers_v4.append(line.strip())

    def enableDnsLeakProtection(self):
        for interface in self.networkinterfaces:
            interface.enableDnsLeakProtection()

    def disableDnsLeakProtection(self):
        for interface in self.networkinterfaces:
            interface.disableDnsLeakProtection()

    def disableIpv6(self):
        for interface in self.networkinterfaces:
            interface.disableIpv6()

    def enableIpv6(self):
        for interface in self.networkinterfaces:
            interface.enableIpv6()
