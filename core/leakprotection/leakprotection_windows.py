import logging

from .leakprotection_generic import LeakProtection_Generic
from .windows.network_interfaces import NetworkInterfaces
from .windows.deadrouting import DeadRouting

from .windows.firewallrules import \
    FirewallRuleOutgoingProfileDefaultBlock, \
    FirewallRuleAllowConnectionToServer, \
    FirewallRuleAllowNetworkingLan, \
    FirewallRuleAllowFromVpnLocalIp, \
    FirewallRuleBlockWrongWay, \
    FirewallRuleBlockMsLeak, \
    FirewallRuleBlockSnmpUpnp, \
    FirewallRuleBlockDefaultGateway, \
    FirewallRuleBlockDNS,\
    FirewallRuleBlockIpv6RouteAnnouncements,\
    FirewallRuleBlockIpv6Dhcp, \
    FirewallReset

class LeakProtection_windows(LeakProtection_Generic):
    def __init__(self, core=None):
        '''
        :type core: core.Core
        '''
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)

        self.networkInterfaces = NetworkInterfaces(self.core)
        self.deadrouting = DeadRouting()
        self.firewallRuleOutgoingProfileDefaultBlock = FirewallRuleOutgoingProfileDefaultBlock()
        self.firewallRuleAllowConnectionToServer = FirewallRuleAllowConnectionToServer()
        self.firewallRuleAllowNetworkingLan = FirewallRuleAllowNetworkingLan()
        self.firewallRuleAllowFromVpnLocalIp = FirewallRuleAllowFromVpnLocalIp()
        self.firewallRuleBlockWrongWay = FirewallRuleBlockWrongWay()
        self.firewallRuleBlockMsLeak = FirewallRuleBlockMsLeak()
        self.firewallRuleBlockSnmp = FirewallRuleBlockSnmpUpnp()
        self.firewallRuleBlockDefaultGateway = FirewallRuleBlockDefaultGateway()
        self.firewallRuleBlockDNS = FirewallRuleBlockDNS()
        self.firewallRuleBlockIpv6RouteAnnouncements = FirewallRuleBlockIpv6RouteAnnouncements()
        self.firewallRuleBlockIpv6Dhcp = FirewallRuleBlockIpv6Dhcp()
        self.firewallReset = FirewallReset()

        self.firewallRules = [
            self.firewallRuleOutgoingProfileDefaultBlock,
            self.firewallRuleAllowConnectionToServer,
            self.firewallRuleAllowNetworkingLan,
            self.firewallRuleAllowFromVpnLocalIp,
            self.firewallRuleBlockWrongWay,
            self.firewallRuleBlockMsLeak,
            self.firewallRuleBlockSnmp,
            self.firewallRuleBlockDefaultGateway,
            self.firewallRuleBlockDNS,
            self.firewallRuleBlockIpv6RouteAnnouncements,
            self.firewallRuleBlockIpv6Dhcp,
        ]
        super().__init__(core)


    def _enable(self):
        '''
        :type settings: core.settings.Settings
        :return:
        '''
        if self.core.settings.leakprotection.enable_deadrouting.get() is True:
            if self._whitelisted_server is not None:  #[public_ip_address, port, protocol]
                self.deadrouting.whitelist_server(self._whitelisted_server[0])
            self.deadrouting.enable()
        else:
            self.deadrouting.disable()

        self.firewallRuleOutgoingProfileDefaultBlock.enable()
        self.firewallRuleAllowNetworkingLan.enable()

        if self._whitelisted_server is not None:
            public_ip_address, port, protocol = self._whitelisted_server
            self.firewallRuleAllowConnectionToServer.enable(public_ip_address, port, protocol)
        else:
            self.firewallRuleAllowConnectionToServer.disable()

        if self._highest_hop_ipv4_local_ip is not None:
            self.firewallRuleAllowFromVpnLocalIp.enable(self._highest_hop_ipv4_local_ip, self._highest_hop_ipv6_local_ip)
        else:
            self.firewallRuleAllowFromVpnLocalIp.disable()

        # WRONG WAY PROTECTION
        if self.core.settings.leakprotection.enable_wrong_way_protection.get() is True and self._highest_hop_ipv4_local_ip is not None:
            self.firewallRuleBlockWrongWay.enable(self._highest_hop_ipv4_local_ip)
        else:
            self.firewallRuleBlockWrongWay.disable()

        # MS LEAK PROTECTION
        if self.core.settings.leakprotection.enable_ms_leak_protection.get() is True:
            self.firewallRuleBlockMsLeak.enable()
        else:
            self.firewallRuleBlockMsLeak.disable()

        # SNMP/UPNP
        if self.core.settings.leakprotection.enable_snmp_upnp_protection.get() is True:
            self.firewallRuleBlockSnmp.enable()
        else:
            self.firewallRuleBlockSnmp.disable()

        # BLOCk ROUTER
        if self.core.settings.leakprotection.block_access_to_local_router.get() is True:
            self.firewallRuleBlockDefaultGateway.enable()
        else:
            self.firewallRuleBlockDefaultGateway.disable()

        # PROTECT IPV6
        if self.core.settings.leakprotection.enable_ipv6_leak_protection.get() is True:
            self.firewallRuleBlockIpv6Dhcp.enable()
            self.firewallRuleBlockIpv6RouteAnnouncements.enable()
            self.networkInterfaces.disableIpv6()
        else:
            self.firewallRuleBlockIpv6Dhcp.disable()
            self.firewallRuleBlockIpv6RouteAnnouncements.disable()
            self.networkInterfaces.enableIpv6()

        # DNS leak protection
        if self.core.settings.leakprotection.enable_dnsleak_protection.get() is True:
            self.networkInterfaces.enableDnsLeakProtection()
        else:
            self.networkInterfaces.disableDnsLeakProtection()


    def _disable(self):
        self.deadrouting.disable()
        for rule in self.firewallRules:
            rule.disable()
        self.networkInterfaces.enableIpv6()
        self.networkInterfaces.disableDnsLeakProtection()

    def reset(self):
        self.deadrouting.disable(force=True)
        self.networkInterfaces.disableDnsLeakProtection()
        self.firewallReset.run()