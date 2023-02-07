import logging
from core.libs.powershell import Powershell
from core.libs.permanent_property import PermanentProperty

NET_FW_ACTION_BLOCK = "Block"
NET_FW_ACTION_ALLOW = "Allow"
NET_FW_RULE_DIR_OUT = "Outbound"
NET_FW_RULE_DIR_IN  = "Inbound"
NET_FW_IP_PROTOCOL_TCP = "TCP"
NET_FW_IP_PROTOCOL_UDP = "UDP"

powershell = Powershell()

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
        #self.is_enabled = PermanentProperty(self.__class__.__name__ + ".is_enabled", False)
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
            self._logger.debug(new_rule_cmd)
            powershell.execute(new_rule_cmd)
        self.is_enabled = True

    def disable(self):
        if self.is_enabled is True:
            self._logger.info("%s disabling" % self.__class__.__name__)
            delete_rule_cmd = 'Remove-NetFirewallRule -Name "%s"' % self.name
            self._logger.debug(delete_rule_cmd)
            powershell.execute(delete_rule_cmd)
        self.is_enabled = False

    def exists(self):
        return powershell.execute('Get-NetFirewallRule -Name "%s"  | ConvertTo-Json' % self.name, as_data = True) != None

    def _build(self):
        args = []
        args.append('-Name "%s"' % self.name)
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
        if self.default_profiles.get() is None:
            self.default_profiles.set(powershell.execute("Get-NetFirewallProfile | ConvertTo-Json", as_data = True))
        powershell.execute("Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Block")
        self.is_enabled.set(True)

    def disable(self):
        if self.is_enabled.get() is False:
            return
        if self.default_profiles.get() is not None:
            self._logger.info("%s disabling" % self.__class__.__name__)
            for profile in self.default_profiles.get():
                powershell.execute("Set-NetFirewallProfile -Profile %s -DefaultOutboundAction %s" % (profile["Profile"],  profile["DefaultOutboundAction"]))
            self.default_profiles.set(None)
        self.is_enabled.set(False)

class FirewallRuleAllowConnectionToServer(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Allow server connection"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        super().__init__()

    def enable(self, ip, port, protocol):
        if self.remote_addresses is None or self.remote_ports is None:
            changed = True
        else:
            changed = self.remote_addresses[0] != ip or self.remote_ports[0] != port or self.protocol != protocol.upper()
        if changed:
            self.disable()
            self.remote_addresses = [ip]
            self.remote_ports = [port]
            self.protocol = protocol.upper()
        super().enable()

class FirewallRuleAllowNetworkingLan(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Allow LAN networking"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_addresses = ["10.0.0.0/8","172.16.0.0/12","192.168.0.0/16"]
        super().__init__()

class FirewallRuleAllowFromVpnLocalIp(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy - Allow traffic from local VPN IP"
        self.description = self.name
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        super().__init__()

    def enable(self, local_ipv4, local_ipv6):
        changed = False
        if self.local_addresses is None or self.remote_ports is None:
            changed = True
        else:
            if len(self.local_addresses) > 0:
                changed = self.local_addresses[0] != local_ipv4
            if len(self.local_addresses) > 1 and changed is False:
                changed = changed or self.local_addresses[1] != local_ipv6
            else:
                if local_ipv6 is not None:
                    changed = True
        if changed:
            self.disable()
            self.local_addresses = [local_ipv4]
            if local_ipv6 is not None:
                self.local_addresses.append(local_ipv6)
        super().enable()

class FirewallRuleBlockWrongWay(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block WrongWay leak"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_IN
        super().__init__()

        '''
        block packets that arrive from "public internet ips" to "all lan ips, except the highest connected vpn hop local ip"
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
        if changed:
            self.disable()
            self.local_addresses = localAddresses
            self.remote_addresses = remoteAddresses
        super().enable()

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

class FirewallRuleBlockSnmpUpnp():
    def __init__(self):
        self.tcp_rule = _FirewallRuleBlockSnmpUpnp_TCP()
        self.udp_rule = _FirewallRuleBlockSnmpUpnp_UDP()

    def enable(self):
        self.tcp_rule.enable()
        self.udp_rule.enable()

    def disable(self):
        self.tcp_rule.disable()
        self.udp_rule.disable()

    def exists(self):
        return self.tcp_rule.exists() and self.udp_rule.exists()

class _FirewallRuleBlockSnmpUpnp_UDP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block SNMP/UDP"
        self.description = "Block outgoing SNMP/UDP requests to prevent network manipulations"
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_ports = ["161","162","1900"]
        self.protocol = NET_FW_IP_PROTOCOL_UDP
        super().__init__()

class _FirewallRuleBlockSnmpUpnp_TCP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block SNMP/TCP"
        self.description = "Block outgoing SNMP/TCP requests to prevent network manipulations"
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_ports = ["161","162","1900"]
        self.protocol = NET_FW_IP_PROTOCOL_TCP
        super().__init__()

class FirewallRuleBlockDNS():
    def __init__(self):
        self.tcp_rule = _FirewallRuleBlockDNS_TCP()
        self.udp_rule = _FirewallRuleBlockDNS_UDP()

    def enable(self, ips):
        self.tcp_rule.enable(ips)
        self.udp_rule.enable(ips)

    def disable(self):
        self.tcp_rule.disable()
        self.udp_rule.disable()

    def exists(self):
        return self.tcp_rule.exists() and self.udp_rule.exists()

class _FirewallRuleBlockDNS_UDP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block unknown DNS servers, UDP"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_ports = ["53"]
        self.protocol = NET_FW_IP_PROTOCOL_UDP
        super().__init__()

    def enable(self, ips):
        self.remote_addresses = ips

class _FirewallRuleBlockDNS_TCP(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy - Block unknown DNS servers, TCP"
        self.description = self.name
        self.action = NET_FW_ACTION_BLOCK
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_ports = ["53"]
        self.protocol = NET_FW_IP_PROTOCOL_TCP
        super().__init__()

    def enable(self, ips):
        self.remote_addresses = ips

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




'''

class FirewallRuleAllowIpSec(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy IPSEC"
        self.description = "Allow Perfect Privacy IPSEC"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.remotePorts = "500,4500"
        self.protocol = NET_FW_IP_PROTOCOL_UDP

    def set_ips(self, serverips):
        if (self.validate(serverips) == False):
            self.remove()
            self.remoteAddresses = serverips
            self.create()

class FirewallRuleAllowIpSecEncapsulation(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy IPSEC Encapsulation"
        self.description = "Allow Perfect Privacy IPSEC Encapsulation"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = 4

    def add(self, serverips):
        if (self.validate(serverips) == False):
            self.remove()
            self.remoteAddresses = serverips
            self.create()

class FirewallRuleAllowIpSecEncapsulationV6(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy IPSEC Encapsulation Ipv6"
        self.description = "Allow Perfect Privacy IPSEC Encapsulation Ipv6"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = 41

    def add(self, serverips):
        if (self.validate(serverips) == False):
            self.remove()
            self.remoteAddresses = serverips
            self.create()

class FirewallRuleAllowDns(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy VPN DNS"
        self.description = "Allow Perfect Privacy VPN DNS"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = 17
        self.remotePorts = "53"

    def add(self, nameservers):
    
        if (self.validate(nameservers) == False):
            self.remove()
            self.remoteAddresses = nameservers
            self.create()
'''
'''
class FirewallRuleAllowStunnelBinary(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy Stunnel Binary"
        self.description = "Allow Perfect Stunnel Binary"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT

    def add(self, applicationName):
        if (self.validate() == False):
            self.remove()
            self.applicationName = applicationName
            self.create()

class FirewallRuleAllowObfsproxyBinary(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy Obfsproxy Binary"
        self.description = "Allow Perfect Obfsproxy Binary"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT

    def add(self,applicationName):
        if (self.validate() == False)
            self.remove()
            self.applicationName = applicationName
            self.create()

class FirewallRuleAllowSSHBinary(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy SSH Binary"
        self.description = "Allow Perfect SSH Binary"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT

    def add(self, applicationName):
        if (self.validate() == False):
            self.remove()
            self.applicationName = applicationName
            self.create()

class FirewallRuleAllowOpenVpnBinary(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy OpenVPN Binary"
        self.description = "Allow Perfect OpenVPN Binary"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT

    def add(self,applicationName):
        if (self.validate() == False):
            self.remove()
            self.applicationName = applicationName
            self.create()

class FirewallRuleAllowGui(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy VPN GUI"
        self.description = "Allow Perfect Privacy VPN GUI"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT

    def add(self, applicationName):
        if (self.validate() == False):
            self.remove()
            self.applicationName = applicationName
            self.create()



class FirewallRuleAllowPortForwardTcp(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy VPN Portforwarding TCP"
        self.description = "Perfect Privacy VPN Portforwarding TCP"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_IN
        self.protocol = NET_FW_IP_PROTOCOL_TCP

    def add(self, ports):
        if (self.validate(ports) == False):
            self.remove()
            self.local_ports = ports
            self.create()

class FirewallRuleAllowPortForwardUdp(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy VPN Portforwarding UDP"
        self.description = "Perfect Privacy VPN Portforwarding UDP"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_IN
        self.protocol = NET_FW_IP_PROTOCOL_UDP

    def add(self,ports):
        if (self.validate(ports) == False):
            self.remove()
            self.local_ports = ports
            self.create()




class FirewallRuleAllowIcmp(FirewallRule):

    def __init__(self):
        self.name = "Perfect Privacy VPN ICMP"
        self.description = "allow Perfect Privacy VPN ICMP"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.protocol = 1

    def add(self,serverips):
        if (self.validate(serverips) == False):
            self.remove()
            self.remoteAddresses = serverips
            self.create()



class FirewallRuleBlockOutgoingAllowedSystemRules(FirewallRule):
    def __init__(self):
        self.name = "Perfect Privacy VPN Networking LAN"
        self.description = "Allow Perfect Privacy VPN Networking LAN"
        self.action = NET_FW_ACTION_ALLOW
        self.direction = NET_FW_RULE_DIR_OUT
        self.remote_addresses = "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

    def add(self):
        if (self.validate() == False):
            self.remove()
            self.create()

'''
