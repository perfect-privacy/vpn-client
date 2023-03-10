import logging
import os
import ipaddress
from core.libs.subcommand import SubCommand
from config.config import PLATFORM
from config.constants import PLATFORMS
if PLATFORM == PLATFORMS.windows:
    from config.files import NETSH, ROUTE

class UpDown_Generic():
    def __init__(self, openvpnConnection):
        '''
        :type openvpnConnection: core.libs.vpn.openvpn.connection_openvpn.OpenVPNConnection
        '''
        self.openvpnConnection = openvpnConnection
        self._logger = logging.getLogger(self.__class__.__name__)
        self.gateway_data = {
            1 : [   "0.0.0.0", 128, 4096],
            2 : [ "128.0.0.0",  64, 2048],
            3 : [ "192.0.0.0",  32, 1024],
            4 : [ "224.0.0.0",  16,  512],
        }

    def up(self):
        self._logger.debug("Up")

        gw_mask, v4_mask, v6_mask = self.gateway_data[self.openvpnConnection.hop_number]
        gateway = self.find_gateway(gw_mask)

        if gateway is not None:
            self.add_route_ipv4(source_ip=self.openvpnConnection.external_host_ip, source_mask="255.255.255.255", target=gateway, device="")
        else:
            self._logger.error("No gateway found for hop %s" % self.openvpnConnection.hop_number)

        if self.openvpnConnection.ipv4_remote_gateway is not None:
            for i in range(0, 223, v4_mask):
                self.add_route_ipv4(source_ip="%s.0.0.0" % i, source_mask="%s.0.0.0" % (256-v4_mask), target=self.openvpnConnection.ipv4_remote_gateway, device=self.openvpnConnection.openvpn_device)
        else:
            self._logger.error("No ipv4_remote_gateway found for hop %s" % self.openvpnConnection.hop_number)

        for i in range(0x2000,0x3800,v6_mask):
            self.add_route_ipv6(source_ip= "%s::" % format(i,"x"), source_mask=3+self.openvpnConnection.hop_number, target="fe80::8", device=self.openvpnConnection.openvpn_device)

    def down(self):
        self._logger.debug("Down")

        gw_mask, v4_mask, v6_mask = self.gateway_data[self.openvpnConnection.hop_number]
        self.delete_route_ipv4(source_ip= self.openvpnConnection.external_host_ip, source_mask= "255.255.255.255")

        if self.openvpnConnection.ipv4_remote_gateway is not None:
            for i in range(0, 223, v4_mask):
                self.delete_route_ipv4(source_ip="%s.0.0.0" % i, source_mask="%s.0.0.0" % (256-v4_mask), target=self.openvpnConnection.ipv4_remote_gateway, device=self.openvpnConnection.openvpn_device)
        else:
            self._logger.error("No ipv4_remote_gateway found for hop %s" % self.openvpnConnection.hop_number)

        for i in range(0x2000, 0x3800, v6_mask):
            self.delete_route_ipv6(source_ip="%s::" % format(i,"x"), source_mask=3+self.openvpnConnection.hop_number, target="fe80::8", device=self.openvpnConnection.openvpn_device)

    def _is_ip(self, str):
        try:
            ip = ipaddress.ip_address(str)
            return True
        except:
            pass
        return False

    def find_gateway(self, netmask_search):
        raise NotImplementedError()

    def add_route_ipv4(self, source_ip, source_mask, target, device = ""):
        raise NotImplementedError()

    def add_route_ipv6(self, source_ip, source_mask, target, device = ""):
        raise NotImplementedError()

    def delete_route_ipv4(self, source_ip, source_mask, target = "", device= ""):
        raise NotImplementedError()

    def delete_route_ipv6(self, source_ip, source_mask, target = "", device = ""):
        raise NotImplementedError()


class UpDown_Windows(UpDown_Generic):

    def find_gateway(self, netmask_search):
        success, stdout, stderr = SubCommand().run("route", [ "print", "-4"])
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
            if gateway == "10.255.255.255": # our deadrouting entry
                continue
            if target == "0.0.0.0" and netmask == netmask_search and self._is_ip(gateway):
                return gateway
        return None

    def add_route_ipv4(self, source_ip, source_mask, target, device = ""):
        args = ["ADD", source_ip, "MASK", source_mask, target ]
        if device != "" and device is not None:
            args.extend(["IF", device])
        success, stdout, stderr = SubCommand().run(ROUTE, args)

    def add_route_ipv6(self, source_ip, source_mask, target, device = ""):
        args = [ "interface", "ipv6", "add", "route", "%s/%s" % (source_ip, source_mask) , target ]
        if device != "" and device is not None:
            args.append("interface=%s" % device)
        args.append("store=active")
        success, stdout, stderr = SubCommand().run(NETSH, args)

    def delete_route_ipv4(self, source_ip, source_mask, target = "", device = ""):
        args = [ "DELETE", source_ip, "MASK", source_mask]
        if target != "" and target is not None:
            args.append(target)
        if device != "" and device is not None:
            args.extend(["IF", device])
        success, stdout, stderr = SubCommand().run(ROUTE, args)

    def delete_route_ipv6(self, source_ip, source_mask, target = "", device = ""):
        args = [ "interface", "ipv6", "delete", "route", "%s/%s" % (source_ip, source_mask)]
        if target != "" and target is not None:
            args.append(target)
        if device != "" and device is not None:
            args.append("interface=%s" % device)
        args.append("store=active")
        success, stdout, stderr = SubCommand().run(NETSH, args)


class UpDown_Macos(UpDown_Generic):
    def __init__(self, openvpnConnection):
        super().__init__(openvpnConnection)
        self.gateway_data = {
            1 : [ "default", 128, 4096],
            2 : [ "1",  64, 2048],
            3 : [ "2",  32, 1024],
            4 : [ "3",  16,  512],
        }

    def find_gateway(self, netmask_search):
        success, stdout, stderr = SubCommand().run("netstat", [ "-rn", ])
        stdout = stdout.decode("UTF-8")
        while "  " in stdout:
            stdout = stdout.replace("  "," ")
        lines = stdout.split("\n")
        for line in lines:
            parts = line.split(" ")
            if len(parts) < 4:
                continue
            destination = parts[0].strip()
            gateway = parts[1].strip()
            flags = parts[2].strip()
            interface = parts[3].strip()
            if destination == netmask_search or destination.endswith("/%s" % netmask_search):
                return gateway
        return None

    def add_route_ipv4(self, source_ip, source_mask, target, device = ""):
        source_mask = ipaddress.IPv4Network('0.0.0.0/%s' % source_mask).prefixlen
        args =  ["-n", "add", "-net", "%s/%s" % (source_ip, source_mask)]
        args.append(target)
        success, stdout, stderr = SubCommand().run("route", args)

    def add_route_ipv6(self, source_ip, source_mask, target, device = ""):
        #/sbin/route add -inet6 2000::/4 -iface utun2
        if device is None:
            self._logger.debug("No OpenVPN device, no adding ipv6 route")
            return
        success, stdout, stderr = SubCommand().run("route", ["-n", "add", "-inet6", "%s/%s" % (source_ip, source_mask),"-iface" ,device])
        self._logger.debug("add_route_ipv6 %s %s %s %s" % ( source_ip, source_mask, target, device))

    def delete_route_ipv4(self, source_ip, source_mask, target = "", device = ""):
        source_mask = ipaddress.IPv4Network('0.0.0.0/%s' % source_mask).prefixlen
        args = ["-n", "delete", "-net", "%s/%s" % (source_ip, source_mask)]
        if target != "":
            args.append(target)
        success, stdout, stderr = SubCommand().run("route", args)

    def delete_route_ipv6(self, source_ip, source_mask, target = "", device = ""):
        if device is None:
            self._logger.debug("No OpenVPN device, no deleting ipv6 route")
            return
        args = ["-n", "delete", "-inet6", "%s/%s" % (source_ip, source_mask),"-iface" ,device]
        success, stdout, stderr = SubCommand().run("route", args)
        self._logger.debug("delete_route_ipv6 %s %s %s %s" % (source_ip, source_mask, target, device))


class UpDown_Linux(UpDown_Generic):
    def __init__(self, openvpnConnection):
        super().__init__(openvpnConnection)

    def find_gateway(self, netmask_search):
        success, stdout, stderr = SubCommand().run("route", [ "-n", ])
        stdout = stdout.decode("UTF-8")
        while "  " in stdout:
            stdout = stdout.replace("  "," ")
        lines = stdout.split("\n")
        for line in lines:
            parts = line.split(" ")
            if len(parts) < 4:
                continue
            destination = parts[0].strip()
            gateway = parts[1].strip()
            flags = parts[2].strip()
            interface = parts[3].strip()
            if destination == netmask_search or destination.endswith("/%s" % netmask_search):
                return gateway
        return None

    def add_route_ipv4(self, source_ip, source_mask, target, device = ""):
        args =  ["add", "-net", source_ip, "netmask", source_mask, "gw", target]
        #route add -net 192.168.1.0 netmask 255.255.255.0 gw 192.168.1.254
        success, stdout, stderr = SubCommand().run("route", args)

    def add_route_ipv6(self, source_ip, source_mask, target, device = ""):
        #/sbin/route add -inet6 2000::/4 -iface utun2
        if device is None:
            self._logger.debug("No OpenVPN device, no adding ipv6 route")
            return
        success, stdout, stderr = SubCommand().run("route", ["-n", "add", "-inet6", "%s/%s" % (source_ip, source_mask),"-iface" ,device])
        self._logger.debug("add_route_ipv6 %s %s %s %s" % ( source_ip, source_mask, target, device))

    def delete_route_ipv4(self, source_ip, source_mask, target = "", device = ""):
        args = ["delete", "-net", source_ip, "netmask", source_mask, "gw"]
        if target != "":
            args.append(target)
        success, stdout, stderr = SubCommand().run("route", args)

    def delete_route_ipv6(self, source_ip, source_mask, target = "", device = ""):
        if device is None:
            self._logger.debug("No OpenVPN device, no deleting ipv6 route")
            return
        args = ["-n", "delete", "-inet6", "%s/%s" % (source_ip, source_mask),"-iface" ,device]
        success, stdout, stderr = SubCommand().run("route", args)
        self._logger.debug("delete_route_ipv6 %s %s %s %s" % (source_ip, source_mask, target, device))

