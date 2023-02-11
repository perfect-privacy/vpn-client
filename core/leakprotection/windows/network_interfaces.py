from core.libs.subcommand import SubCommand
import random

class NetworkInterface():
    def __init__(self, core):
        self.core = core
        self.index = 0
        self.dhcpenabled = False
        self.servicename = None
        self.interfacealias = None
        self.ipenabled = None
        self.dns_servers_v4 = []
        self.dns_servers_v6 = []
        self.ipv6 = []
        self.ipv4 = []
        self.dnsleakprotection_enabled = False

    def disableIpv6(self):
        for ipv6 in self.ipv6:
            success, stdout, stderr = SubCommand().run("netsh", ["interface", "ipv6", "delete", "address", "%s" % self.index, "address=%s" % ipv6[0], "store=active"])

    def enableIpv6(self):
        # enable does nothing, if a automatically assigned Ipv6 has been removed, it will come back automatically when announcements are no longer firewalled
        pass

    def enableDnsLeakProtection(self):
        all_ipv4_dns_servers = [item.vpn_server_config.dns_ipv4 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv4 != "" and item.vpn_server_config.bandwidth_mbps > 500]
        all_ipv6_dns_servers = [item.vpn_server_config.dns_ipv6 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv6 != "" and item.vpn_server_config.bandwidth_mbps > 500]


        changed = False

        if self.ipenabled is True:
            if self.interfacealias.startswith("Perfect Privacy") or self.interfacealias.startswith("PerfectPrivacy"):
                if self.core.settings.leakprotection.use_custom_dns_servers.get() is True:
                    new_dnsservers_v4 = [ip for ip in [self.core.settings.leakprotection.custom_dns_server_1.get(), self.core.settings.leakprotection.custom_dns_server_2.get()]]
                    new_dnsservers_v6 = [ip for ip in [self.core.settings.leakprotection.custom_dns_server_1.get(), self.core.settings.leakprotection.custom_dns_server_2.get()]]
                else:
                    new_dnsservers_v4 = [random.choice(all_ipv4_dns_servers) , random.choice(all_ipv4_dns_servers)] # TODO better selection
                    new_dnsservers_v6 = [random.choice(all_ipv6_dns_servers) , random.choice(all_ipv6_dns_servers)]
            else: # not our interface
                new_dnsservers_v4 = ["0.0.0.0"]
                new_dnsservers_v6 = ["::"]

            if new_dnsservers_v4 != self.dns_servers_v4:
                changed = True
                success, stdout, stderr = SubCommand().run("netsh", ["interface", "ipv4", "set", "dnsserver", "%s" % (self.index), "static", "address=%s" % new_dnsservers_v4[0], "validate=no"])
                if len(new_dnsservers_v4) > 1:
                    success, stdout, stderr = SubCommand().run("netsh", ["interface", "ipv4", "set", "dnsserver", "%s" % (self.index), "static", "address=%s" % new_dnsservers_v4[1], "index=1", "validate=no"])
            if new_dnsservers_v6 != self.dns_servers_v6:
                changed = True
                success, stdout, stderr = SubCommand().run("netsh", ["interface", "ipv6", "set", "dnsserver", "%s" % (self.index), "static", "address=%s" % new_dnsservers_v6[0] , "validate=no"])
                if len(new_dnsservers_v6) > 1:
                    success, stdout, stderr = SubCommand().run("netsh", ["interface", "ipv4", "set", "dnsserver", "%s" % (self.index), "static", "address=%s" % new_dnsservers_v6[1], "index=1", "validate=no"])

        if self.dnsleakprotection_enabled is False: # so we can run multiple times
            self.dnsleakprotection_enabled = changed

    def disableDnsLeakProtection(self):
        if self.dnsleakprotection_enabled is True or "0.0.0.0" in self.dns_servers_v4 or "::" in self.dns_servers_v6:
            self.dnsleakprotection_enabled = False
            success, stdout, stderr = SubCommand().run("netsh.exe", ["interface", "ipv4", "set", "dnsserver", "%s" % self.index, "dhcp", "validate=no"])
            success, stdout, stderr = SubCommand().run("netsh.exe", ["interface", "ipv6", "set", "dnsserver", "%s" % self.index, "dhcp", "validate=no"])


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
        if self.networkinterfaces is None:
            self.networkinterfaces = {}
        networkdatas = self.core.powershell.execute("Get-DnsClientServerAddress | ConvertTo-Json", as_data = True)
        for networkdata in networkdatas:
            if networkdata["InterfaceIndex"] not in self.networkinterfaces:
                ni = NetworkInterface(self.core)
                ni.index =  networkdata["InterfaceIndex"]
                self.networkinterfaces[ni.index] = ni
            else:
                ni = self.networkinterfaces[ networkdata["InterfaceIndex"]]

            ni.interfacealias = networkdata["InterfaceAlias"]
            if networkdata["AddressFamily"] == 2:
                ni.dns_servers_v4 = networkdata["ServerAddresses"]
            if networkdata["AddressFamily"] == 23:
                ni.dns_servers_v6 = networkdata["ServerAddresses"]

        networkdatas = self.core.powershell.execute("Get-CimInstance -Class Win32_NetworkAdapterConfiguration | ConvertTo-Json", as_data = True )
        for networkdata in networkdatas:
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

