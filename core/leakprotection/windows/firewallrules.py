import logging
import socket
import struct

from core.libs.powershell import getPowershellInstance
from core.libs.permanent_property import PermanentProperty
from core.libs.web.reporter import ReporterInstance

NET_FW_ACTION_BLOCK = "Block"
NET_FW_ACTION_ALLOW = "Allow"
NET_FW_RULE_DIR_OUT = "Outbound"
NET_FW_RULE_DIR_IN  = "Inbound"
NET_FW_IP_PROTOCOL_TCP = "TCP"
NET_FW_IP_PROTOCOL_UDP = "UDP"

class FirewallRule():
    def __init__(self):
        if not hasattr(self, "name")            : self.name             = ""
        if not hasattr(self, "description")     : self.description      = None
        if not hasattr(self, "action")          : self.action           = None
        if not hasattr(self, "direction")       : self.direction        = None
        if not hasattr(self, "protocol")        : self.protocol         = None
        if not hasattr(self, "remote_ports")    : self.remote_ports     = None
        if not hasattr(self, "remote_addresses"): self.remote_addresses = None
        if not hasattr(self, "local_ports")     : self.local_ports      = None
        if not hasattr(self, "local_addresses") : self.local_addresses  = None
        if not hasattr(self, "applicationName") : self.applicationName  = None
        self._is_enabled = None
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    def is_enabled(self):
        if self._is_enabled is None:
            self._is_enabled = self.exists()
        return self._is_enabled
    @is_enabled.setter
    def is_enabled(self, value):
        self._is_enabled = value

    def enable(self, **kwargs):
        if self.is_enabled is False:
            self._logger.info("%s activating" % self.__class__.__name__)
            new_rule_cmd = "New-NetFirewallRule %s" % self._build()
            getPowershellInstance().execute(new_rule_cmd)
        self.is_enabled = True

    def update(self):
        self._logger.info("%s updating" % self.__class__.__name__)
        new_rule_cmd = "Set-NetFirewallRule %s" % self._build(update=True)
        getPowershellInstance().execute(new_rule_cmd)

    def disable(self):
        if self.is_enabled is True:
            self._logger.info("%s disabling" % self.__class__.__name__)
            delete_rule_cmd = 'Remove-NetFirewallRule -Name "%s"' % self.name
            getPowershellInstance().execute(delete_rule_cmd, may_fail=True)
        self.is_enabled = False

    def exists(self):
        return getPowershellInstance().execute('Get-NetFirewallRule -Name "%s"' % self.name, as_data = True, may_fail=True) != None

    def _build(self, update = False):
        args = []
        args.append('-Name "%s"' % self.name)
        if update is False:
            args.append('-DisplayName  "%s"' % self.name)
            args.append('-Description  "%s"' % self.description)
        if self.action is not None:
            args.append('-Action  %s' % self.action)
        if self.direction is not None:
            args.append('-Direction  %s' % self.direction)
        if self.protocol is not None:
            args.append('-Protocol  %s' % self.protocol)
        if self.remote_ports is not None:
            args.append('-RemotePort  @(%s)' % ", ".join(['"%s"' % x for x in self.remote_ports]))
        if self.remote_addresses is not None:
            args.append('-RemoteAddress  @(%s)' % ", ".join(['"%s"' % x for x in self.remote_addresses]))
        if self.local_ports is not None:
            args.append('-LocalPort  @(%s)' % ", ".join(['"%s"' % x for x in self.local_ports]))
        if self.local_addresses is not None:
            args.append('-LocalAddress  @(%s)' % ", ".join(['"%s"' % x for x in self.local_addresses]))
        if self.applicationName is not None:
            args.append('-Program   "%s"' % self.applicationName)
        return " ".join(args)

class FirewallRuleOutgoingProfileDefaultBlock():
    # https://docs.microsoft.com/en-us/powershell/module/netsecurity/set-netfirewallprofile?view=win10-ps
    def __init__(self):
        self.default_profiles = PermanentProperty(self.__class__.__name__ + ".default_profiles", []) # load from disk
        self.is_enabled = PermanentProperty(self.__class__.__name__ + ".is_enabled", False)
        self._logger = logging.getLogger(self.__class__.__name__)

    def enable(self):
        if self.is_enabled.get() is True:
            return
        self._logger.info("%s activating" % self.__class__.__name__)
        #if self.default_profiles.get() is None:
        #    self.default_profiles.set(getPowershellInstance().execute("Get-NetFirewallProfile", as_data = True))
        getPowershellInstance().execute("Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Block -Enabled True")
        self.is_enabled.set(True)

    def disable(self):
        if self.is_enabled.get() is False:
            return
        if self.default_profiles.get() is not None:
            self._logger.info("%s disabling" % self.__class__.__name__)
            #for profile in self.default_profiles.get(): # this would be better, for user whos default profile is not "allow", but this results in many more problems
            #    getPowershellInstance().execute("Set-NetFirewallProfile -Profile %s -DefaultOutboundAction %s" % (profile["Profile"],  profile["DefaultOutboundAction"]))
            #self.default_profiles.set(None)
            getPowershellInstance().execute("Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Allow")

        self.is_enabled.set(False)

class FirewallRuleAllowConnectionToServer(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Allow server connection"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        super().__init__()

    def enable(self, ip, port, protocol):
        changed =  self.remote_addresses is None or self.remote_ports is None or self.remote_addresses[0] != ip or self.remote_ports[0] != port or self.protocol != protocol.upper()
        if changed is True or self.is_enabled is False:
            self.remote_addresses = [ip]
            self.remote_ports = [port]
            self.protocol = protocol.upper()
            super().enable() if self.is_enabled is False else self.update()


class FirewallRuleAllowNetworkingLan(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Allow LAN networking"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_addresses = ["10.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12","192.168.0.0/16", "fe80::/64", "ff01::/16", "ff02::/16"]
        super().__init__()

class FirewallRuleAllowFromVpnLocalIps(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy - Allow traffic from local VPN IP"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        super().__init__()

    def enable(self, local_ipv4s, local_ipv6s):
        changed = self.local_addresses != local_ipv4s+local_ipv6s or self.local_addresses is None
        if changed is True or self.is_enabled is False:
            self.local_addresses = local_ipv4s+local_ipv6s
            super().enable() if self.is_enabled is False else self.update()


class FirewallRuleBlockInternet(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block Internet Access"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        super().__init__()
        '''
        block sending packets from "all ips, except vpn hop local ips" to "public internet ips except hop server ips"  
        '''

    def enable(self, remote_ipv4s, local_ipv4s):
        local_ipv4_boundarys = ["0.0.0.0", "223.255.255.255"]
        for local_ipv4 in set(local_ipv4s):
            try:
                local_ipv4_boundarys.append(self.int2ip(self.ip2int(local_ipv4) - 1))
                local_ipv4_boundarys.append(self.int2ip(self.ip2int(local_ipv4) + 1))
            except:
                pass
        local_ipv4_boundarys.sort(key=lambda x:self.ip2int(x))

        localAddresses = []
        for i in range(0, len(local_ipv4_boundarys),2):
            localAddresses.append("%s-%s" % (local_ipv4_boundarys[i],local_ipv4_boundarys[i+1]))
        localAddresses.append("::-fdbf:1d37:bbe0::")
        localAddresses.append("fdbf:1d37:bbe1::-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff")

        internet_ipv4_boundarys = [
           "0.0.0.0","9.255.255.255","11.0.0.0","126.255.255.255","128.0.0.0","169.253.255.255","169.255.0.0","172.15.255.255",
           "172.32.0.0","192.167.255.255","192.169.0.0","223.255.255.255"
        ]
        for remote_ipv4 in remote_ipv4s:
            try:
                internet_ipv4_boundarys.append(self.int2ip(self.ip2int(remote_ipv4) - 1))
                internet_ipv4_boundarys.append(self.int2ip(self.ip2int(remote_ipv4) + 1))
            except:
                pass
        internet_ipv4_boundarys.sort(key=lambda x:self.ip2int(x))

        remoteAddresses = []
        for i in range(0, len(internet_ipv4_boundarys),2):
            remoteAddresses.append("%s-%s" % (internet_ipv4_boundarys[i],internet_ipv4_boundarys[i+1]))
        remoteAddresses.append("2000::/3")

        changed = self.local_addresses != localAddresses or self.remote_addresses != remoteAddresses
        if changed is True or self.is_enabled is False:
            self.local_addresses = localAddresses
            self.remote_addresses = remoteAddresses
            super().enable() if self.is_enabled is False else self.update()

    def ip2int(self,addr):
        return struct.unpack("!I", socket.inet_aton(addr))[0]

    def int2ip(self, addr):
        return socket.inet_ntoa(struct.pack("!I", addr))


class FirewallRuleBlockWrongWay(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block WrongWay leak"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_IN
        super().__init__()

        '''
        block packets that arrive from "public internet ips" to "all ips, except the highest connected vpn hop local ip"
        This prevents packets that arrive from the internet on any non VPN ip to be returned over the VPN
        https://www.perfect-privacy.com/en/blog/wrong-way-security-problem-exposes-real-ip
        '''

    def enable(self, highest_hop_localip):
        ipparts = highest_hop_localip.split('.')
        lowerip  = "%s.%s.%s.%s" % ( ipparts[0], ipparts[1], ipparts[2], (int(ipparts[3]) - 1))
        higherip = "%s.%s.%s.%s" % ( ipparts[0], ipparts[1], ipparts[2], (int(ipparts[3]) + 1))
        localAddresses = [
            "0.0.0.0-%s" % lowerip,
            "%s-223.255.255.255" % higherip,
            "::-fdbf:1d37:bbe0::",
            "fdbf:1d37:bbe1::-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"
        ]
        remoteAddresses = [
            "2000::/3",
            "0.0.0.0-9.255.255.255",
            "11.0.0.0-126.255.255.255",
            "128.0.0.0-169.253.255.255",
            "169.255.0.0-172.15.255.255",
            "172.32.0.0-192.167.255.255",
            "192.169.0.0-223.255.255.255"
        ]
        changed = self.local_addresses != localAddresses or self.remote_addresses != remoteAddresses
        if changed is True or self.is_enabled is False:
            self.local_addresses = localAddresses
            self.remote_addresses = remoteAddresses
            super().enable() if self.is_enabled is False else self.update()

class FirewallRuleBlockMsLeak(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block MsLeak"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_addresses = [
            "2000::/3",
            "0.0.0.0-9.255.255.255",
            "11.0.0.0-126.255.255.255",
            "128.0.0.0-169.253.255.255",
            "169.255.0.0-172.15.255.255",
            "172.32.0.0-192.167.255.255",
            "192.169.0.0-223.255.255.255"
        ] # "the internet"
        self.protocol = NET_FW_IP_PROTOCOL_TCP
        self.remote_ports = ["139", "445"]
        super().__init__()

class FirewallRuleBlockDefaultGateway(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block DefaultGateway access"
        self.description = "Block connections to default Gateway to prevent router manipulation leaks"
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_addresses = ["Defaultgateway"]
        super().__init__()

class FirewallRuleBlockSnmpUpnp_UDP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block SNMP/UDP"
        self.description = "Block outgoing SNMP/UDP requests to prevent network manipulations"
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_ports = ["161","162","1900"]
        self.protocol = NET_FW_IP_PROTOCOL_UDP
        super().__init__()

class FirewallRuleBlockSnmpUpnp_TCP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block SNMP/TCP"
        self.description = "Block outgoing SNMP/TCP requests to prevent network manipulations"
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_ports = ["161","162","1900"]
        self.protocol = NET_FW_IP_PROTOCOL_TCP
        super().__init__()

class FirewallRuleBlockDNS_UDP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block local DNS servers, UDP"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_ports = ["53"]
        self.protocol = NET_FW_IP_PROTOCOL_UDP
        self.remote_addresses = ["10.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12","192.168.0.0/16", "fe80::/64", "ff01::/16", "ff02::/16"]
        super().__init__()

class FirewallRuleBlockDNS_TCP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block local DNS servers, TCP"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_ports = ["53"]
        self.protocol = NET_FW_IP_PROTOCOL_TCP
        self.remote_addresses = ["10.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12","192.168.0.0/16", "fe80::/64", "ff01::/16", "ff02::/16"]
        super().__init__()

class FirewallRuleBlockIpv6RouteAnnouncements(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block IPv6 route announcements"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = 58
        self.applicationName = "C:\WINDOWS\system32\svchost.exe"
        self.remote_addresses = [
            "ff02::2",
            "fe80::/64",
            "LocalSubnet"
        ]
        self.local_addresses = [
            "fe80::/64"
        ]
        super().__init__()

class FirewallRuleBlockIpv6Dhcp(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block IPv6 DHCP"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = 17
        self.remote_ports = [547]
        self.local_ports = [546]
        super().__init__()


class FirewallRuleAllowIpSecUDP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Allow IPSEC UDP to server"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = NET_FW_IP_PROTOCOL_UDP
        self.remote_ports = [500,4500]
        super().__init__()

    def enable(self, ip):
        changed =  self.remote_addresses is None or self.remote_ports is None or self.remote_addresses[0] != ip
        if changed is True or self.is_enabled is False:
            self.remote_addresses = [ip]
            super().enable() if self.is_enabled is False else self.update()

class FirewallRuleAllowIpSecTCP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Allow IPSEC TCP to server"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = NET_FW_IP_PROTOCOL_TCP
        self.remote_ports = [1723]
        super().__init__()

    def enable(self, ip):
        changed =  self.remote_addresses is None or self.remote_ports is None or self.remote_addresses[0] != ip
        if changed is True or self.is_enabled is False:
            self.remote_addresses = [ip]
            super().enable() if self.is_enabled is False else self.update()

class FirewallRuleAllowIpSec(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Allow IPSEC to server"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = 4
        super().__init__()

    def enable(self, ip):
        changed =  self.remote_addresses is None or self.remote_ports is None or self.remote_addresses[0] != ip
        if changed is True or self.is_enabled is False:
            self.remote_addresses = [ip]
            super().enable() if self.is_enabled is False else self.update()

class FirewallRuleAllowIpSecGRE(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Allow IPSEC GRE to server"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = 47
        super().__init__()

    def enable(self, ip):
        changed = self.remote_addresses is None or self.remote_ports is None or self.remote_addresses[0] != ip
        if changed is True or self.is_enabled is False:
            self.remote_addresses = [ip]
            super().enable() if self.is_enabled is False else self.update()

class FirewallReset():
    def run(self):
        getPowershellInstance().execute("Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Allow -Enabled True")
        getPowershellInstance().execute('Remove-NetFirewallRule -Name "perfect*privacy*"', may_fail=True)
