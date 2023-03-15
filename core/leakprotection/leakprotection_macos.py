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
        self.current_rules_str = None
        super().__init__(core=core)

    def _enable(self):
        self._logger.info("adjusting firewall")
        rules = [
            "set skip on lo0",
            "block in all",
            "block out all",
        ]

        if len(self.core.session.hops) > 0:
            lowest_hop = self.core.session.hops[0]
            if lowest_hop.connection is not None and lowest_hop.connection.external_host_ip is not None:
                rules.append("pass out  inet proto {protocol} to {public_ip_address} port {port} keep state".format(protocol=lowest_hop.connection.external_host_protocol,
                                                                                                   public_ip_address=lowest_hop.connection.external_host_ip,
                                                                                                   port=lowest_hop.connection.external_host_port))

        for hop in self.core.session.hops:
            if hop.connection is not None and hop.connection.interface is not None:
                rules.append("pass out on %s all keep state" % hop.connection.interface)

        rules.extend([
            "pass out inet to 10.0.0.0/8",
            "pass in  inet from 10.0.0.0/8",
            "pass out inet to 192.168.0.0/16",
            "pass in  inet from 192.168.0.0/16",
            "pass out inet to 172.16.0.0/12",
            "pass in  inet from 172.16.0.0/12",
            "pass out inet proto UDP to 224.0.0.251 port 5353",  # mDNS / local discovery
            "pass out inet to 169.254.0.0/16",  # link-local (works on primary interface only)
        ])

        # BLOCK ROUTER
        if self.core.settings.leakprotection.block_access_to_local_router.get() is True:
            for router_ip in self._get_router_ips():
                rules.append("block out inet to %s" % router_ip)

        # SNMP/UPNP
        # SNMP/UPNP
        if self.core.settings.leakprotection.enable_snmp_upnp_protection.get() is True:
            for port in ["161:162", "1900"]:
                for proto in ["TCP", "UDP"]:
                    rules.append("block out inet  proto %s to 0.0.0.0/0 port %s" % (proto, port))

        rules_str = "\n".join(rules) + "\n"
        if rules_str != self.current_rules_str:
            self._logger.debug("Updating firewall rules")
            self.current_rules_str = rules_str
            try:
                fd, path = tempfile.mkstemp(prefix="pf_")
                with os.fdopen(fd, "w") as f:
                    f.write(rules_str)

                subprocess.Popen([PFCTL, "-f", path]).communicate()
                subprocess.Popen([PFCTL, "-e"]).communicate()
                subprocess.Popen([PFCTL, "-F", "states"]).communicate()

            except Exception as e:
                self._logger.error("unexpected exception: {}".format(e))
                self._logger.debug(traceback.format_exc())

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
            self._logger.info("turning off firewall")
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