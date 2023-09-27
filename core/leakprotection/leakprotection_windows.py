import logging
import traceback

from .leakprotection_generic import LeakProtection_Generic
from .windows.network_interfaces import NetworkInterfaces

from .windows.firewallrules import \
    FirewallRuleOutgoingProfileDefaultBlock, \
    FirewallRuleAllowConnectionToServer, \
    FirewallRuleAllowNetworkingLan, \
    FirewallRuleAllowFromVpnLocalIps, \
    FirewallRuleAllowIpSecUDP, \
    FirewallRuleAllowIpSecTCP, \
    FirewallRuleAllowIpSecGRE, \
    FirewallRuleAllowIpSec,\
    FirewallRuleBlockInternet, \
    FirewallRuleBlockWrongWay, \
    FirewallRuleBlockMsLeak, \
    FirewallRuleBlockSnmpUpnp_UDP, \
    FirewallRuleBlockSnmpUpnp_TCP, \
    FirewallRuleBlockDefaultGateway, \
    FirewallRuleBlockDNS_TCP,\
    FirewallRuleBlockDNS_UDP,\
    FirewallRuleBlockIpv6RouteAnnouncements,\
    FirewallRuleBlockIpv6Dhcp, \
    FirewallReset
from ..libs.powershell import getPowershellInstance
from ..libs.web.reporter import ReporterInstance


class LeakProtection_windows(LeakProtection_Generic):
    def __init__(self, core=None):
        '''
        :type core: core.Core
        '''
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)

        #self.deadrouting = DeadRouting()
        self.firewallRuleOutgoingProfileDefaultBlock = FirewallRuleOutgoingProfileDefaultBlock()
        self.firewallRuleAllowConnectionToServer = FirewallRuleAllowConnectionToServer()
        self.firewallRuleAllowNetworkingLan = FirewallRuleAllowNetworkingLan()
        self.firewallRuleAllowFromVpnLocalIps = FirewallRuleAllowFromVpnLocalIps()
        self.firewallRuleAllowIpSec = FirewallRuleAllowIpSec()
        self.firewallRuleAllowIpSecTCP = FirewallRuleAllowIpSecTCP()
        self.firewallRuleAllowIpSecUDP = FirewallRuleAllowIpSecUDP()
        self.firewallRuleAllowIpSecGRE = FirewallRuleAllowIpSecGRE()
        self.firewallRuleBlockInternet = FirewallRuleBlockInternet()
        self.firewallRuleBlockWrongWay = FirewallRuleBlockWrongWay()
        self.firewallRuleBlockMsLeak = FirewallRuleBlockMsLeak()
        self.firewallRuleBlockSnmpTcp = FirewallRuleBlockSnmpUpnp_TCP()
        self.firewallRuleBlockSnmpUdp = FirewallRuleBlockSnmpUpnp_UDP()
        self.firewallRuleBlockDefaultGateway = FirewallRuleBlockDefaultGateway()
        self.firewallRuleBlockDNS_TCP = FirewallRuleBlockDNS_TCP()
        self.firewallRuleBlockDNS_UDP = FirewallRuleBlockDNS_UDP()
        self.firewallRuleBlockIpv6RouteAnnouncements = FirewallRuleBlockIpv6RouteAnnouncements()
        self.firewallRuleBlockIpv6Dhcp = FirewallRuleBlockIpv6Dhcp()
        self.firewallReset = FirewallReset()

        self.firewallRules = [
            self.firewallRuleOutgoingProfileDefaultBlock,
            self.firewallRuleAllowConnectionToServer,
            self.firewallRuleAllowNetworkingLan,
            self.firewallRuleAllowFromVpnLocalIps,
            self.firewallRuleAllowIpSec,
            self.firewallRuleAllowIpSecUDP,
            self.firewallRuleAllowIpSecTCP,
            self.firewallRuleAllowIpSecGRE,
            self.firewallRuleBlockInternet,
            self.firewallRuleBlockWrongWay,
            self.firewallRuleBlockMsLeak,
            self.firewallRuleBlockSnmpTcp,
            self.firewallRuleBlockSnmpUdp,
            self.firewallRuleBlockDefaultGateway,
            self.firewallRuleBlockDNS_TCP,
            self.firewallRuleBlockDNS_UDP,
            self.firewallRuleBlockIpv6RouteAnnouncements,
            self.firewallRuleBlockIpv6Dhcp,
        ]
        super().__init__(core)


    def _enable(self):

        # ALLOW TO LOWEST HOP IP
        external_host_ip = None
        if len( self.core.session.hops) > 0:
            lowest_hop = self.core.session.hops[0]
            if lowest_hop.connection is not None and lowest_hop.connection.external_host_ip is not None:
                external_host_ip = lowest_hop.connection.external_host_ip
                if lowest_hop.connection.type == "ipsec":
                    self.firewallRuleAllowIpSec.enable(external_host_ip)
                    self.firewallRuleAllowIpSecUDP.enable(external_host_ip)
                    self.firewallRuleAllowIpSecTCP.enable(external_host_ip)
                    self.firewallRuleAllowIpSecGRE.enable(external_host_ip)
                    self.firewallRuleAllowConnectionToServer.disable()
                else:
                    self.firewallRuleAllowConnectionToServer.enable(external_host_ip, lowest_hop.connection.external_host_port, lowest_hop.connection.external_host_protocol)
                    self.firewallRuleAllowIpSec.disable()
                    self.firewallRuleAllowIpSecUDP.disable()
                    self.firewallRuleAllowIpSecTCP.disable()
                    self.firewallRuleAllowIpSecGRE.disable()

        # ALLOW FROM LOCAL VPN IPS
        local_vpn_ipv4s = []
        local_vpn_ipv6s = []
        for hop in self.core.session.hops:
            if hop.connection is not None and hop.connection.ipv4_local_ip is not None:
                local_vpn_ipv4s.append( hop.connection.ipv4_local_ip)
                if  hop.connection.ipv6_local_ip is not None:
                    local_vpn_ipv6s.append( hop.connection.ipv6_local_ip)
        if len(local_vpn_ipv4s) > 0:
            self.firewallRuleAllowFromVpnLocalIps.enable(local_vpn_ipv4s, local_vpn_ipv6s)
        else:
            self.firewallRuleAllowFromVpnLocalIps.disable()

        # ALLOW LAN
        self.firewallRuleAllowNetworkingLan.enable()

        # DEFAULT BLOCK
        self.firewallRuleOutgoingProfileDefaultBlock.enable()

        # BLOCK TO INTERNET, except from vpn ip and to vpn server, OVERWRITE WINDOWS ALLOW RULES
        if external_host_ip is None:
            self.firewallRuleBlockInternet.enable(remote_ipv4s=[], local_ipv4s=local_vpn_ipv4s)
        else:
            self.firewallRuleBlockInternet.enable(remote_ipv4s=[external_host_ip], local_ipv4s=local_vpn_ipv4s)

        # WRONG WAY PROTECTION
        if self.core.settings.leakprotection.enable_wrong_way_protection.get() is True and len(local_vpn_ipv4s) > 0:
            self.firewallRuleBlockWrongWay.enable(local_vpn_ipv4s[-1])
        else:
            self.firewallRuleBlockWrongWay.disable()

        # MS LEAK PROTECTION
        if self.core.settings.leakprotection.enable_ms_leak_protection.get() is True:
            self.firewallRuleBlockMsLeak.enable()
        else:
            self.firewallRuleBlockMsLeak.disable()

        # SNMP/UPNP
        if self.core.settings.leakprotection.enable_snmp_upnp_protection.get() is True:
            self.firewallRuleBlockSnmpTcp.enable()
            self.firewallRuleBlockSnmpUdp.enable()
        else:
            self.firewallRuleBlockSnmpTcp.disable()
            self.firewallRuleBlockSnmpUdp.disable()

        # BLOCK ROUTER
        if self.core.settings.leakprotection.block_access_to_local_router.get() is True:
            self.firewallRuleBlockDefaultGateway.enable()
        else:
            self.firewallRuleBlockDefaultGateway.disable()

        self.networkInterfaces = NetworkInterfaces(self.core)

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
            self.firewallRuleBlockDNS_TCP.enable()
            self.firewallRuleBlockDNS_UDP.enable()
        else:
            self.networkInterfaces.disableDnsLeakProtection()
            self.firewallRuleBlockDNS_TCP.disable()
            self.firewallRuleBlockDNS_UDP.disable()

    def _disable(self):
        self.networkInterfaces = NetworkInterfaces(self.core)

        getPowershellInstance().execute('Remove-NetFirewallRule -Name "perfect*privacy*"', may_fail=True)

        for rule in self.firewallRules:
            if hasattr(rule, "name") and rule.name.startswith("Perfect Privacy"):
                rule.is_enabled = False
                continue
            rule.disable()
        self.networkInterfaces.enableIpv6()
        self.networkInterfaces.disableDnsLeakProtection()

    def reset(self):
        try:
            self.networkInterfaces = NetworkInterfaces(self.core)
            self.networkInterfaces.disableDnsLeakProtection()
        except Exception as e:
            ReporterInstance.report("firewall_reset_dns_failed", traceback.format_exc())
        try:
            self.firewallReset.run()
        except Exception as e:
            ReporterInstance.report("firewall_reset_firewall_failed", traceback.format_exc())
