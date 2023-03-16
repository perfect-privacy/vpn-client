import traceback

from core.libs.powershell import getPowershellInstance
from core.libs.subcommand import SubCommand
import random
from config.files import NETSH
from core.libs.web.reporter import ReporterInstance


class NetworkInterface():
    def __init__(self, core, all_ipv4_dns_servers, all_ipv6_dns_servers):
        self.core = core
        self.interfaceIndex = None
        self.dhcpenabled = False
        self.servicename = None
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
            if ipv6[0].startswith("2") or ipv6[0].startswith("3"):
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv6", "delete", "address", self.interfaceIndex, "address=%s" % ipv6[0], "store=active"])

    def enableIpv6(self):
        # enable does nothing, if a automatically assigned Ipv6 has been removed, it will come back automatically when announcements are no longer firewalled
        pass

    def enableDnsLeakProtection(self):
        dnsservers = []
        new_dnsservers_v4 = []
        new_dnsservers_v6 = []
        if self.ipenabled is True:
            interfaces = [h.connection.interface for h in self.core.session.hops if h.connection is not None and h.connection.interface is not None]
            if self.interfaceIndex in interfaces:
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
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv4", "set", "dnsserver", self.interfaceIndex, "static", "address=%s" % new_dnsservers_v4[0], "validate=no"])
            if len(new_dnsservers_v4) > 1:
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv4", "set", "dnsserver", self.interfaceIndex, "static", "address=%s" % new_dnsservers_v4[1], "index=1", "validate=no"])
            if len(new_dnsservers_v6) > 0:
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv6", "set", "dnsserver", self.interfaceIndex, "static", "address=%s" % new_dnsservers_v6[0] , "validate=no"])
            if len(new_dnsservers_v6) > 1:
                success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv6", "set", "dnsserver", self.interfaceIndex, "static", "address=%s" % new_dnsservers_v6[1], "index=1", "validate=no"])

            self.dnsleakprotection_enabled = True

    def disableDnsLeakProtection(self):
        if self.dnsleakprotection_enabled is True or "0.0.0.0" in self.dns_servers_v4 or "::" in self.dns_servers_v6:
            self.dnsleakprotection_enabled = False
            success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv4", "set", "dnsserver", self.interfaceIndex, "dhcp", "validate=no"])
            success, stdout, stderr = SubCommand().run(NETSH, ["interface", "ipv6", "set", "dnsserver", self.interfaceIndex, "dhcp", "validate=no"])


    def __str__(self):
        data = []
        data.append("InterfaceIndex: %s" % self.interfaceIndex)
        data.append("dhcpenabled: %s" % self.dhcpenabled)
        data.append("ipv6: %s" % self.ipv6)
        data.append("ipv4: %s" % self.ipv4)
        data.append("servicename: %s" % self.servicename)
        data.append("ipenabled: %s" % self.ipenabled)
        data.append("dns_servers_v4: %s" % self.dns_servers_v4)
        data.append("dns_servers_v6: %s" % self.dns_servers_v6)
        return "\n".join(data)

class NetworkInterfaces():

    def __init__(self,core ):
        self.core = core
        self.networkinterfaces = None
        self._load()

    def _load(self):
        if self.core is not None:
            all_ipv4_dns_servers = [item.vpn_server_config.dns_ipv4 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv4 != "" and item.vpn_server_config.bandwidth_mbps > 500 and item.is_online is True]
            all_ipv6_dns_servers = [item.vpn_server_config.dns_ipv6 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv6 != "" and item.vpn_server_config.bandwidth_mbps > 500 and item.is_online is True]
        else:
            all_ipv4_dns_servers = []
            all_ipv6_dns_servers = []

        if self.networkinterfaces is None:
            self.networkinterfaces = {}
        networkdatas = getPowershellInstance().execute("Get-DnsClientServerAddress | Select-Object -Property InterfaceIndex,ServerAddresses,AddressFamily", as_data = True)
        if networkdatas is None:
            ReporterInstance.report("failed_to_load_network_devices","")
            return

        for networkdata in networkdatas:
            try:
                networkdata["InterfaceIndex"] = "%s" % networkdata["InterfaceIndex"]
                if networkdata["InterfaceIndex"] not in self.networkinterfaces:
                    ni = NetworkInterface(self.core, all_ipv4_dns_servers, all_ipv6_dns_servers)
                    ni.interfaceIndex =  networkdata["InterfaceIndex"]
                    self.networkinterfaces[ni.interfaceIndex] = ni
                else:
                    ni = self.networkinterfaces[ networkdata["InterfaceIndex"]]

                if networkdata["AddressFamily"] == 2:
                    ni.dns_servers_v4 = networkdata["ServerAddresses"]
                if networkdata["AddressFamily"] == 23:
                    ni.dns_servers_v6 = networkdata["ServerAddresses"]
            except Exception as e:
                ReporterInstance.report("get_dns_failed", traceback.format_exc())

        networkdatas = getPowershellInstance().execute("Get-CimInstance -Class Win32_NetworkAdapterConfiguration | Select-Object -Property InterfaceIndex,DHCPEnabled,ServiceName,IPEnabled,IPAddress,IPSubnet", as_data = True )
        if networkdatas is None:
            ReporterInstance.report("failed_to_load_network_devices_part2", "")
            return
        for networkdata in networkdatas:
            try:
                networkdata["InterfaceIndex"] = "%s" % networkdata["InterfaceIndex"]
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
        for key, interface in self.networkinterfaces.items():
            interface.disableIpv6()

    def enableIpv6(self):
        return # enable does nothing, ipv6 will come back if dhcpv6 is no longer blocked
        #self._load()
        #for key, interface in self.networkinterfaces.items():
        #    interface.enableIpv6()

    def enableDnsLeakProtection(self):
        for key, interface in self.networkinterfaces.items():
            interface.enableDnsLeakProtection()

    def disableDnsLeakProtection(self):
        for key, interface in self.networkinterfaces.items():
            interface.disableDnsLeakProtection()

