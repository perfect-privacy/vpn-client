import logging
import random
import subprocess
import time
import traceback
import os
from .leakprotection_generic import LeakProtection_Generic
from .macos.network_interfaces import NetworkInterfaces
from ..libs.subcommand import SubCommand
from ..libs.web.reporter import ReporterInstance




class LeakProtection_linux(LeakProtection_Generic):
    def __init__(self, core=None):
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)
        self.current_rules_str = ""
        super().__init__(core=core)

    def _enable(self):
        local_ipv4_ranges = ["10.0.0.0/8", "127.0.0.0/8", "192.168.0.0/16", "172.16.0.0/12", "169.254.0.0/16", ]
        local_ipv6_ranges = ["fe80::/64", "ff01::/16", "ff02::/16"]

        rules = []
        rules.append("iptables  -N perfect-privacy")
        rules.append("ip6tables -N perfect-privacy")

        # BLOCK ROUTER
        if self.core.settings.leakprotection.block_access_to_local_router.get() is True:
            for router_ip in self._get_router_ips():
                rules.append('iptables -A perfect-privacy -p tcp -d %s -j DROP' % router_ip)

        # Block ipv6 route adv and dhcv6
        if self.core.settings.leakprotection.enable_ipv6_leak_protection.get() is True:
            rules.append('ip6tables -A perfect-privacy -p ipv6-icmp --icmpv6-type 128 -j DROP')
            rules.append('ip6tables -A perfect-privacy -p ipv6-icmp --icmpv6-type 133 -j DROP')
            rules.append('ip6tables -A perfect-privacy -p ipv6-icmp --icmpv6-type 134 -j DROP')
            rules.append('ip6tables -A perfect-privacy -p ipv6-icmp --icmpv6-type 135 -j DROP')
            rules.append('ip6tables -A perfect-privacy -p ipv6-icmp --icmpv6-type 136 -j DROP')
            rules.append('ip6tables -A perfect-privacy -p ipv6-icmp --icmpv6-type 137 -j DROP')
            rules.append('ip6tables -A perfect-privacy -p ipv6-icmp --icmpv6-type 138 -j DROP')
            rules.append('ip6tables -A perfect-privacy -p TCP --dport 547 -j DROP')
            rules.append('ip6tables -A perfect-privacy -p TCP --dport 546 -j DROP')
            rules.append('iptables  -A perfect-privacy -p UDP --dport 547 -j DROP')
            rules.append('iptables  -A perfect-privacy -p UDP --dport 546 -j DROP')

        # Block local dns servers
        if self.core.settings.leakprotection.enable_dnsleak_protection.get() is True:
            for local_ipv4_range in local_ipv4_ranges:
                rules.append('iptables -A perfect-privacy -p UDP --dport 53 -d %s -j DROP' % local_ipv4_range)
                rules.append('iptables -A perfect-privacy -p TCP --dport 53 -d %s -j DROP' % local_ipv4_range)
            for local_ipv6_range in local_ipv6_ranges:
                rules.append('ip6tables -A perfect-privacy -p UDP --dport 53 -d %s -j DROP' % local_ipv6_range)
                rules.append('ip6tables -A perfect-privacy -p TCP --dport 53 -d %s -j DROP' % local_ipv6_range)

        # SNMP/UPNP
        if self.core.settings.leakprotection.enable_snmp_upnp_protection.get() is True:
            for port in ["161", "162", "1900"]:
                for proto in ["tcp", "udp"]:
                    rules.append("iptables  -A perfect-privacy -p %s --dport %s -j DROP" % (proto, port))
                    rules.append("ip6tables -A perfect-privacy -p %s --dport %s -j DROP" % (proto, port))

        # Allow local lan
        rules.append('iptables -A perfect-privacy -d 224.0.0.251 -p TCP --dport 5353 -j ACCEPT')
        rules.append('iptables -A perfect-privacy -d 224.0.0.251 -p UDP --dport 5353 -j ACCEPT')
        for local_ipv4_range in local_ipv4_ranges:
            rules.append('iptables -A perfect-privacy -s %s -j ACCEPT' % local_ipv4_range)
        for local_ipv6_range in local_ipv6_ranges:
            rules.append('ip6tables -A perfect-privacy -s %s -j ACCEPT' % local_ipv6_range)

        # Allow connection to server
        if len(self.core.session.hops) > 0:
            for hop in self.core.session.hops:
                if hop.connection is not None and hop.connection.external_host_ip is not None:
                    rules.append("iptables -A perfect-privacy -p %s --dport %s -d %s -j ACCEPT" % (hop.connection.external_host_protocol, hop.connection.external_host_port, hop.connection.external_host_ip))
            highest_hops = self.core.session.hops[-1]
            if highest_hops.connection is not None and highest_hops.connection.ipv4_local_ip is not None:
                rules.append("iptables -A perfect-privacy -s %s -j ACCEPT" % (highest_hops.connection.ipv4_local_ip))

        # Drop everything else
        rules.append( 'iptables -A perfect-privacy -j DROP')
        rules.append('ip6tables -A perfect-privacy -j DROP')

        rules_str = "\n".join(rules)
        if rules_str != self.current_rules_str:
            uniq_name = "perfect-privacy-%s" % int(time.time())
            for rule in rules:
                os.system(rule.replace("perfect-privacy", uniq_name))
            self._logger.debug("%s Firewall rules updated" % len(rules))
            os.system('iptables  -I OUTPUT 1 -j %s' % uniq_name)
            os.system('ip6tables -I OUTPUT 1 -j %s' % uniq_name)
            self.current_rules_str = rules_str
            for iptables in ["iptables", "ip6tables"]:
                for existing_chain in self._get_existing_chains(iptables):
                    if existing_chain != uniq_name:
                        os.system('%s -D OUTPUT -j %s' % (iptables, existing_chain))
                        os.system('%s --flush %s' % (iptables, existing_chain))
                        os.system('%s -X %s' % (iptables, existing_chain))

        # PROTECT IPV6
        if self.core.settings.leakprotection.enable_ipv6_leak_protection.get() is True:
            self._disableIpv6()

        if self.core.settings.leakprotection.enable_dnsleak_protection.get():
            self.enable_dns_leak_protection()
        else:
            self.disable_dns_leak_protection()

    def _get_existing_chains(self, iptables):
        success, stdout, stderr = SubCommand().run(iptables, args=["-S", "OUTPUT"])
        lines = stdout.decode("utf-8").split("\n")
        uniq_names = set()
        for line in lines:
            if "perfect-privacy-" in line:
                uniq_names.add("perfect-privacy-%s" % line.split("perfect-privacy-")[1].split(" ")[0])
        return list(uniq_names)

    def _disable(self):
        for iptables in ["iptables", "ip6tables"]:
            for existing_chain in self._get_existing_chains(iptables):
                os.system('%s -D OUTPUT -j %s' % (iptables, existing_chain))
                os.system('%s --flush %s' % (iptables, existing_chain))
                os.system('%s -X %s' % (iptables, existing_chain))
        self.disable_dns_leak_protection()
    def reset(self):
        self._disable()

    def _disableIpv6(self):
        success, stdout, stderr = SubCommand().run("ip", args=["address"])
        stdout = stdout.decode("utf-8").replace("\t", " ").replace("  ", " ")
        while "  " in stdout:
            stdout = stdout.replace("  ", " ")
        interface = ""
        for line in stdout.split("\n"):
            try:
                if line.startswith(" inet6 ") and interface != "":
                    ipv6 = line.split("inet6 ")[1].split(" ")[0].split("%")[0]
                    if ipv6.startswith("2") or ipv6.startswith("3"):
                        SubCommand().run("ip", args=["addr", "del", ipv6, "dev", interface])
                elif not line.startswith(" ") and ": " in line:
                    interface = line.split(": ")[1].split(":")[0].strip()
            except Exception as e:
                ReporterInstance.report("disable_ipv6_failed", traceback.format_exc())

    def _get_router_ips(self):
        success, stdout, stderr = SubCommand().run("ip", args=["route", ])
        stdout = stdout.decode("UTF-8")
        while "  " in stdout:
            stdout = stdout.replace("  ", " ")
        lines = stdout.split("\n")
        gateways = []
        for line in lines:
            try:
                destination_net = line.split(" ")[0].strip()
                if destination_net == "default":
                    destination_net = "0.0.0.0/0"
                gateway = None
                if "via " in line:
                    gateway = line.split("via ")[1].split(" ")[0].strip()
                if destination_net == "0.0.0.0/0" and gateway is not None:
                   gateways.append(gateway)
            except Exception as e:
                pass
        return gateways

    def enable_dns_leak_protection(self):
        if self.core is not None:
            all_ipv4_dns_servers = [item.vpn_server_config.dns_ipv4 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv4 != "" and item.vpn_server_config.bandwidth_mbps > 500 and item.is_online is True]
            all_ipv6_dns_servers = [item.vpn_server_config.dns_ipv6 for _, item in self.core.vpnGroupPlanet.servers.items() if item.vpn_server_config.dns_ipv6 != "" and item.vpn_server_config.bandwidth_mbps > 500 and item.is_online is True]
        else:
            all_ipv4_dns_servers = []
            all_ipv6_dns_servers = []

        self.current_dns_servers = []
        current_resolv_conf = open("/etc/resolv.conf", "r").read()
        if "Perfect Privacy resolv.conf" in current_resolv_conf:
            self.current_dns_servers = [line.split(" ")[1] for line in current_resolv_conf.split("\n") if "nameserver " in line]

        dnsservers = []
        if self.core.settings.leakprotection.use_custom_dns_servers.get() is True:
            dnsservers = [self.core.settings.leakprotection.custom_dns_server_1.get(),self.core.settings.leakprotection.custom_dns_server_2.get()]
            dnsservers = [x.strip() for x in dnsservers if x.strip() != ""]
            dnsservers.sort()
            if len(dnsservers) > 0:
                if dnsservers == sorted( self.current_dns_servers):
                    return
        if len(dnsservers) == 0:
            if len(self.current_dns_servers) > 0 and set( self.current_dns_servers).issubset(all_ipv4_dns_servers + all_ipv6_dns_servers):
                return
            dnsservers = [random.choice(all_ipv4_dns_servers), random.choice(all_ipv4_dns_servers),random.choice(all_ipv6_dns_servers), random.choice(all_ipv6_dns_servers)]

        if not "Perfect Privacy resolv.conf" in current_resolv_conf:
            os.system("mv /etc/resolv.conf /etc/resolv.conf.pp.original")
        with open("/etc/resolv.conf","w") as f:
            f.write("# Perfect Privacy resolv.conf, do not edit manually.\n\n")
            for dnsserver in dnsservers:
                f.write("nameserver %s\n" % dnsserver)

    def disable_dns_leak_protection(self):
        current_resolv_conf = open("/etc/resolv.conf", "r").read()
        if "Perfect Privacy resolv.conf" in current_resolv_conf:
            if os.path.exists("/etc/resolv.conf.pp.original"):
                os.system("rm /etc/resolv.conf ; mv /etc/resolv.conf.pp.original /etc/resolv.conf")