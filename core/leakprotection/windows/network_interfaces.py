import traceback

from core.libs.subcommand import SubCommand
import random
from config.files import NETSH
from core.libs.web.reporter import ReporterInstance


class NetworkInterface():
    def __init__(self, core, all_ipv4_dns_servers, all_ipv6_dns_servers):
        self.core = core
        self.index = 0
        self.dhcpenabled = False
        self.servicename = None
        self.interfacealias = None
        self.ipenabled = None
        self.dns_servers_v4 = []  # currently set, read from system
        self.dns_servers_v6 = []
        self.all_ipv4_dns_servers = all_ipv4_dns_servers
        self.all_ipv6_dns_servers = all_ipv6_dns_servers
        self.ipv6 = []
        self.ipv4 = []
        self.dnsleakprotection_enabled = False

    def disableIpv6(self):
        for ipv6 in self.ipv6:
            success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv6", "delete", "address", "%s" % self.index, "address=%s" % ipv6[0], "store=active"])

    def enableIpv6(self):
        # enable does nothing, if a automatically assigned Ipv6 has been removed, it will come back automatically when announcements are no longer firewalled
        pass

    def enableDnsLeakProtection(self):
        dnsservers = []
        new_dnsservers_v4 = []
        new_dnsservers_v6 = []
        if self.ipenabled is True:
            if self.interfacealias.startswith("Perfect Privacy") or self.interfacealias.startswith("PerfectPrivacy"):
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
                new_dnsservers_v4 = [ip for ip in dnsservers if "." in ip]
                new_dnsservers_v6 = [ip for ip in dnsservers if ":" in ip]
            else: # not our interface
                if self.dns_servers_v4 != ["0.0.0.0"]:
                    new_dnsservers_v4 = ["0.0.0.0"]
                if self.dns_servers_v6 != ["::"]:
                    new_dnsservers_v6 = ["::"]

            if len(new_dnsservers_v4) > 0:
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv4", "set", "dnsserver", "%s" % (self.index), "static", "address=%s" % new_dnsservers_v4[0], "validate=no"])
            if len(new_dnsservers_v4) > 1:
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv4", "set", "dnsserver", "%s" % (self.index), "static", "address=%s" % new_dnsservers_v4[1], "index=1", "validate=no"])
            if len(new_dnsservers_v6) > 0:
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv6", "set", "dnsserver", "%s" % (self.index), "static", "address=%s" % new_dnsservers_v6[0] , "validate=no"])
            if len(new_dnsservers_v6) > 1:
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv4", "set", "dnsserver", "%s" % (self.index), "static", "address=%s" % new_dnsservers_v6[1], "index=1", "validate=no"])

            self.dnsleakprotection_enabled = True

    def disableDnsLeakProtection(self):
        if self.dnsleakprotection_enabled is True or "0.0.0.0" in self.dns_servers_v4 or "::" in self.dns_servers_v6:
            self.dnsleakprotection_enabled = False
            success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv4", "set", "dnsserver", "%s" % self.index, "dhcp", "validate=no"])
            success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv6", "set", "dnsserver", "%s" % self.index, "dhcp", "validate=no"])


    def __str__(self):
        data = []
        data.append("Index: %s" % self.index)
        data.append("dhcpenabled: %s" % self.dhcpenabled)
        data.append("ipv6: %s" % self.ipv6)
        data.append("ipv4: %s" % self.ipv4)
        data.append("servicename: %s" % self.servicename)
        data.append("interfacealias: %s" % self.interfacealias)
        data.append("ipenabled: %s" % self.ipenabled)
        data.append("dns_servers_v4: %s" % self.dns_servers_v4)
        data.append("dns_servers_v6: %s" % self.dns_servers_v6)
        return "\n".join(data)

class NetworkInterfaces():

    def __init__(self,core ):
        self.core = core
        self.networkinterfaces = None

    def _load(self):
        all_ipv4_dns_servers = [item.vpn_server_config.dns_ipv4 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv4 != "" and item.vpn_server_config.bandwidth_mbps > 500]
        all_ipv6_dns_servers = [item.vpn_server_config.dns_ipv6 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv6 != "" and item.vpn_server_config.bandwidth_mbps > 500]

        if self.networkinterfaces is None:
            self.networkinterfaces = {}
        networkdatas = self.core.powershell.execute("Get-DnsClientServerAddress | ConvertTo-Json", as_data = True)
        if networkdatas is None:
            ReporterInstance.report("failed_to_load_network_devices","")
            return

        for networkdata in networkdatas:
            try:
                if networkdata["InterfaceIndex"] not in self.networkinterfaces:
                    ni = NetworkInterface(self.core, all_ipv4_dns_servers, all_ipv6_dns_servers)
                    ni.index =  networkdata["InterfaceIndex"]
                    self.networkinterfaces[ni.index] = ni
                else:
                    ni = self.networkinterfaces[ networkdata["InterfaceIndex"]]

                ni.interfacealias = networkdata["InterfaceAlias"]
                if networkdata["AddressFamily"] == 2:
                    ni.dns_servers_v4 = networkdata["ServerAddresses"]
                if networkdata["AddressFamily"] == 23:
                    ni.dns_servers_v6 = networkdata["ServerAddresses"]
            except Exception as e:
                ReporterInstance.report("get_dns_failed", traceback.format_exc())

        networkdatas = self.core.powershell.execute("Get-CimInstance -Class Win32_NetworkAdapterConfiguration | ConvertTo-Json", as_data = True )
        if networkdatas is None:
            ReporterInstance.report("failed_to_load_network_devices_part2", "")
            return
        for networkdata in networkdatas:
            try:
                if networkdata["InterfaceIndex"] not in self.networkinterfaces:
                    continue
                ni = self.networkinterfaces[ networkdata["InterfaceIndex"]]
                ni.dhcpenabled = networkdata["DHCPEnabled"]
                ni.servicename = networkdata["ServiceName"]
                ni.ipenabled   = networkdata["IPEnabled"]
                ni.ipv4 = []
                ni.ipv6 = []
                if networkdata["IPAddress"] is not None:
                    for i in range(0,len(networkdata["IPAddress"])):
                        ip = networkdata["IPAddress"][i]
                        netmask = networkdata["IPSubnet"][i]
                        if ip.find(":") != -1:
                            ipn = (ip, netmask)
                            if ipn not in ni.ipv6:
                                ni.ipv6.append(ipn)
                        else:
                            ipn = (ip, netmask)
                            if ipn not in ni.ipv4:
                                ni.ipv4.append(ipn)
            except Exception as e:
                ReporterInstance.report("get_adapters_failed", traceback.format_exc())

    def disableIpv6(self):
        self._load()
        for key, interface in self.networkinterfaces.items():
            interface.disableIpv6()

    def enableIpv6(self):
        self._load()
        for key, interface in self.networkinterfaces.items():
            interface.enableIpv6()

    def enableDnsLeakProtection(self):
        self._load()
        for key, interface in self.networkinterfaces.items():
            interface.enableDnsLeakProtection()

    def disableDnsLeakProtection(self):
        self._load()
        for key, interface in self.networkinterfaces.items():
            interface.disableDnsLeakProtection()

