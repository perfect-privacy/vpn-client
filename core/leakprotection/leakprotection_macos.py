import logging
import tempfile
import os
import subprocess
import traceback
from collections import namedtuple
from .leakprotection_generic import LeakProtection_Generic
from .macos.network_interfaces import NetworkInterfaces
from ..libs.subcommand import SubCommand

TRANSPORT_PROTOCOL_UDP = "udp"
TRANSPORT_PROTOCOL_TCP = "tcp"

PFCTL = "/sbin/pfctl"

Hop = namedtuple("Hop", "hop_id public_ip_address port transport_protocol interface")

class LeakProtection_macos(LeakProtection_Generic):
    def __init__(self, core=None):
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)
        self.current_rules_str = ""
        super().__init__(core=core)

    def _enable(self):
        rules = [
            "set skip on lo0",
            "block out all",
        ]

        if len(self.core.session.hops) > 0:
            lowest_hop = self.core.session.hops[0]
            if lowest_hop.connection is not None and lowest_hop.connection.external_host_ip is not None:
                rules.append("pass out inet proto %s to %s port  %s keep state" % (lowest_hop.connection.external_host_protocol, lowest_hop.connection.external_host_ip, lowest_hop.connection.external_host_port))

        for hop in self.core.session.hops:
            if hop.connection is not None and hop.connection.interface is not None:
                rules.append("pass out on %s all keep state" % hop.connection.interface)

        local_ipv4_ranges = ["10.0.0.0/8", "192.168.0.0/16", "172.16.0.0/12", "169.254.0.0/16", ]
        local_ipv6_ranges = ["fe80::/64", "ff01::/16", "ff02::/16"]

        for local_ipv4_range in local_ipv4_ranges:
            rules.append("pass out inet to %s" % local_ipv4_range)
        for local_ipv6_range in local_ipv6_ranges:
            rules.append("pass out inet6 to %s" % local_ipv6_range)
        rules.append("pass out inet  proto UDP to 224.0.0.251 port 5353")

        # BLOCK ROUTER
        if self.core.settings.leakprotection.block_access_to_local_router.get() is True:
            for router_ip in self._get_router_ips():
                rules.append("block out inet to %s" % router_ip)

        # SNMP/UPNP
        if self.core.settings.leakprotection.enable_snmp_upnp_protection.get() is True:
            for port in ["161:162", "1900"]:
                for proto in ["TCP", "UDP"]:
                    rules.append("block out inet proto %s to 0.0.0.0/0 port %s" % (proto, port))

        # block ipv6 route adv and dhcv6
        if self.core.settings.leakprotection.enable_ipv6_leak_protection.get() is True:
            rules.append("block in  inet6 proto ipv6-icmp from any icmp6-type { 128, 133, 134, 135, 136, 137, 138 }")
            rules.append("block out inet  proto UDP       to   any port 547")
            rules.append("block in  inet  proto UDP       from any port 546")
            rules.append("block out inet6 proto UDP       to   any port 547")
            rules.append("block in  inet6 proto UDP       from any port 546")

        # block local dns servers
        if self.core.settings.leakprotection.enable_dnsleak_protection.get() is True:
            for local_ipv4_range in local_ipv4_ranges:
                rules.append("block out inet  proto UDP to %s port 53" % local_ipv4_range)
                rules.append("block out inet  proto TCP to %s port 53" % local_ipv4_range)
            for local_ipv6_range in local_ipv6_ranges:
                rules.append("block out inet6 proto UDP to %s port 53" % local_ipv6_range)
                rules.append("block out inet6 proto TCP to %s port 53" % local_ipv6_range)

        rules_str = "\n".join(rules) + "\n"
        if rules_str != self.current_rules_str:
            self._logger.debug("Updating firewall rules")
            try:
                fd, path = tempfile.mkstemp(prefix="pf_")
                with os.fdopen(fd, "w") as f:
                    f.write(rules_str)

                subprocess.Popen([PFCTL, "-f", path]).communicate()
                subprocess.Popen([PFCTL, "-e"]).communicate()
                if self.current_rules_str == "":
                    subprocess.Popen([PFCTL, "-F", "states"]).communicate()

            except Exception as e:
                self._logger.error("Unexpected exception: {}".format(e))
                self._logger.debug(traceback.format_exc())
            self.current_rules_str = rules_str

        self.networkInterfaces = NetworkInterfaces(self.core)

        # PROTECT IPV6
        if self.core.settings.leakprotection.enable_ipv6_leak_protection.get() is True:
            self.networkInterfaces.disableIpv6()
        else:
            self.networkInterfaces.enableIpv6()

        # DNS leak protection
        if self.core.settings.leakprotection.enable_dnsleak_protection.get():
            self.networkInterfaces.enableDnsLeakProtection()
        else:
            self.networkInterfaces.disableDnsLeakProtection()

    def _disable(self):
        self.networkInterfaces = NetworkInterfaces(self.core)
        if self.current_rules_str != "":
            self._logger.info("Turning off firewall")
            subprocess.Popen([PFCTL, "-d"]).communicate()
            self.current_rules_str = ""
        self.networkInterfaces.disableDnsLeakProtection()

    def reset(self):
        subprocess.Popen([PFCTL, "-d"]).communicate()
        self.current_rules_str = ""
        success, stdout, stderr = SubCommand().run("/usr/sbin/networksetup", args=["-listallnetworkservices"])
        lines = stdout.decode("utf-8").split("\n")
        if len(lines) > 1:
            for line in lines[1:]:
                name = line.strip()
                if name == "":
                    continue
                _, _, _ = SubCommand().run('/usr/sbin/networksetup', args=['-setdnsservers'   , name, "Empty"])
                _, _, _ = SubCommand().run('/usr/sbin/networksetup', args=['-setsearchdomains', name, "Empty"])

    def _get_router_ips(self):
        success, stdout, stderr = SubCommand().run("/usr/sbin/networksetup", args=["-listallnetworkservices"])
        lines = stdout.decode("utf-8").split("\n")
        results = []
        if len(lines) > 1:
            for line in lines[1:]:
                name = line.strip()
                if name == "":
                    continue
                success, stdout, stderr = SubCommand().run("/usr/sbin/networksetup", args=["-getinfo", name])
                try:
                    ip = stdout.decode("utf-8").split("Router:")[1].split("\n").strip()
                    if "." in ip or ":" in ip:
                        results.append(ip)
                except:
                    pass
        return results