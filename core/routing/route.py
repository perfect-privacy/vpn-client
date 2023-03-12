import ipaddress
import logging

from config.config import PLATFORM
from config.constants import PLATFORMS
from core.libs.permanent_property import PermanentProperty
from core.libs.subcommand import SubCommand
from config.files import ROUTE, NETSH



class RouteV6():
    def __init__(self, destination_net, gateway, interface = None, persist = False):
        self.destination_net = destination_net
        self.gateway = gateway
        self.interface = interface
        self.persist = persist

    def enable(self):
        raise NotImplementedError()
    def delete(self):
        raise NotImplementedError()

class RouteV6Macos(RouteV6):
    def delete(self):
        if self.interface is None:
            #self._logger.debug("No OpenVPN device, no deleting ipv6 route")
            return
        SubCommand().run("route", ["-n", "delete", "-inet6", self.destination_net, "-iface", self.interface])

    def enable(self):
        if self.interface is None:
            #self._logger.debug("No OpenVPN device, no adding ipv6 route")
            return
        SubCommand().run("route", ["-n", "add", "-inet6", self.destination_net,"-iface",  self.interface])

class RouteV6Windows(RouteV6):
    def delete(self):
        args = ["interface", "ipv6", "delete", "route", self.destination_net]
        if self.gateway != "" and self.gateway is not None:
            args.append(self.gateway)
        if self.interface != "" and self.interface is not None:
            args.append("interface=%s" % self.interface)
        if self.persist is True:
            args.append("store=persistent")
        SubCommand().run(NETSH, args)

    def enable(self):
        args = ["interface", "ipv6", "add", "route", self.destination_net]
        if self.gateway != "" and self.gateway is not None:
            args.append(self.gateway)
        if self.interface != "" and self.interface is not None:
            args.append("interface=%s" % self.interface)
        if self.persist is True:
            args.append("store=persistent")
        else:
            args.append("store=active")
        SubCommand().run(NETSH, args)



class RouteV4():
    def __init__(self, destination_ip, destination_mask, gateway, interface = None, persist = False):
        self.destination_ip = destination_ip
        self.destination_mask = destination_mask
        self.gateway = gateway
        self.interface = interface
        self.persist = persist

    def enable(self):
        raise NotImplementedError()
    def delete(self):
        raise NotImplementedError()

class RouteV4Windows(RouteV4):
    def delete(self):
        SubCommand().run(ROUTE, ["delete", self.destination_ip, "mask", self.destination_mask, self.gateway])

    def enable(self):
        cmd = ["add"]
        if self.persist is True:
            cmd.append("-p")
        cmd.extend([ self.destination_ip, "mask",  self.destination_mask, self.gateway])
        SubCommand().run(ROUTE, cmd)

class RouteV4Macos(RouteV4):
    def delete(self):
        SubCommand().run("route",["-n", "delete", "-net", "%s/%s" % (self.destination_ip,ipaddress.IPv4Network('0.0.0.0/%s' % self.destination_mask).prefixlen),self.gateway])

    def enable(self):
        SubCommand().run("route", ["-n", "add", "-net", "%s/%s" % (self.destination_ip, ipaddress.IPv4Network('0.0.0.0/%s' % self.destination_mask).prefixlen), self.gateway])

