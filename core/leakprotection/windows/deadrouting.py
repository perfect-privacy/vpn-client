import ipaddress
from core.libs.subcommand import SubCommand
from config.files import ROUTE, NETSH

class DeadRouting():
    def __init__(self):
        self.whitelisted_server_ip = None
        self.is_enabled = False

    def whitelist_server(self, server):
        if self.whitelisted_server_ip is not None and self.is_enabled is True:
            SubCommand().run(ROUTE, ["delete", self.whitelisted_server_ip, "mask", "255.255.255.255"])
        self.whitelisted_server_ip = server
        if self.is_enabled is True:
            default_gw = self._find_default_gateway()
            if default_gw is not None:
                SubCommand().run(ROUTE, ["add", self.whitelisted_server_ip, "mask", "255.255.255.255", default_gw])

    def clear_whitelist(self):
        if self.whitelisted_server_ip is not None and self.is_enabled is True:
            SubCommand().run(ROUTE, ["delete", self.whitelisted_server_ip, "mask", "255.255.255.255"])
        self.whitelisted_server_ip = None

    def enable(self):
        if self.is_enabled is False:
            self.is_enabled = True
            if self.whitelisted_server_ip is not None:
                default_gw = self._find_default_gateway()
                if default_gw is not None:
                    SubCommand().run(ROUTE, ["add", self.whitelisted_server_ip, "mask", "255.255.255.255", default_gw])
            SubCommand().run(ROUTE, ["add", "-p",   "0.0.0.0", "mask", "128.0.0.0", "10.255.255.255", "metric", "9999"]) # bugus unreachable ip, 127.0.0.1 does not work
            SubCommand().run(ROUTE, ["add", "-p", "128.0.0.0", "mask", "128.0.0.0", "10.255.255.255", "metric", "9999"])
            SubCommand().run(NETSH, ["interface", "ipv6", "add", "route", "2000::/4", "interface=1", "store=persistent"])
            SubCommand().run(NETSH, ["interface", "ipv6", "add", "route", "3000::/4", "interface=1", "store=persistent"])

    def disable(self, force=False):
        if self.is_enabled is True or force is True:
            self.is_enabled = False
            #if self.whitelisted_server_ip is not None: don't delete here, active connection will delete it on down
            #    SubCommand().run(ROUTE, ["delete", self.whitelisted_server_ip, "mask", "255.255.255.255"])
            SubCommand().run(ROUTE, ["delete",   "0.0.0.0", "mask", "128.0.0.0", "10.255.255.255"])
            SubCommand().run(ROUTE, ["delete", "128.0.0.0", "mask", "128.0.0.0", "10.255.255.255"])
            SubCommand().run(NETSH, ["interface", "ipv6", "delete", "route", "2000::/4", "interface=1",])
            SubCommand().run(NETSH, ["interface", "ipv6", "delete", "route", "3000::/4", "interface=1",])

    def _find_default_gateway(self):
        success, stdout, stderr = SubCommand().run(ROUTE, [ "print", "-4"])
        lines = stdout.split(b"\n")
        for line in lines:
            if line.find(b"0.0.0.0") == -1:
                continue
            parts = b' '.join(line.split()).strip().split(b" ")
            target = parts[0].strip().decode("UTF-8")
            netmask = parts[1].strip().decode("UTF-8")
            try:
                gateway = parts[2].strip().decode("UTF-8")
            except:
                gateway = None
            #network = parts[3].strip().decode("UTF-8")
            if target == "0.0.0.0" and netmask == "0.0.0.0" and self._is_ip(gateway):
                return gateway
        return None

    def _is_ip(self, str):
        try:
            ip = ipaddress.ip_address(str)
            return True
        except:
            pass
        return False
