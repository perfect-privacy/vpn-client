import ipaddress
import logging

from config.config import PLATFORM
from config.constants import PLATFORMS
from core.libs.subcommand import SubCommand
if PLATFORM == PLATFORMS.windows:
    from config.files import ROUTE, NETSH

class Route():
    def __init__(self, destination_net, gateway= None, interface = None, persist = False):
        self.destination_net = destination_net
        self.gateway = gateway
        self.interface = interface
        self.persist = persist

    def enable(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

    def __repr__(self):
        return "%s -> %s : %s" % (self.destination_net, self.gateway, self.interface)

class RouteV4Windows(Route):
    def delete(self):
        args = ["interface", "ipv4", "delete", "route", self.destination_net]
        if self.gateway is not None:
            args.append(self.gateway)
        if self.interface is not None:
            args.append("interface=%s" % self.interface)
        if self.persist is True:
            args.append("store=persistent")
        SubCommand().run(NETSH, args)

    def enable(self):
        args = ["interface", "ipv4", "add", "route", self.destination_net]
        if self.gateway is not None:
            args.append(self.gateway)
        if self.interface is not None:
            args.append("interface=%s" % self.interface)
        if self.persist is True:
            args.append("store=persistent")
        else:
            args.append("store=active")
        SubCommand().run(NETSH, args)

class RouteV6Windows(Route):
    def delete(self):
        args = ["interface", "ipv6", "delete", "route", self.destination_net]
        if self.gateway is not None:
            args.append(self.gateway)
        if self.interface is not None:
            args.append("interface=%s" % self.interface)
        if self.persist is True:
            args.append("store=persistent")
        SubCommand().run(NETSH, args)

    def enable(self):
        args = ["interface", "ipv6", "add", "route", self.destination_net]
        if self.gateway is not None:
            args.append(self.gateway)
        if self.interface is not None:
            args.append("interface=%s" % self.interface)
        if self.persist is True:
            args.append("store=persistent")
        else:
            args.append("store=active")
        SubCommand().run(NETSH, args)

class RouteV4Macos(Route):
    def delete(self):
        cmd = ["-n", "delete", "-net"]
        #if self.interface is not None:
        #    cmd.extend(["-ifscope", self.interface])
        cmd.append(self.destination_net)
        if self.gateway is not None:
            cmd.append(self.gateway)
        SubCommand().run("route", cmd)

    def enable(self):
        cmd = ["-n", "add", "-net"]
        #if self.interface is not None:
        #    cmd.extend(["-ifscope", self.interface])
        cmd.append(self.destination_net)
        if self.gateway is not None:
            cmd.append(self.gateway)
        SubCommand().run("route", cmd)

class RouteV6Macos(Route):
    def delete(self):
        cmd = ["-n", "delete", "-inet6", self.destination_net]
        if self.interface is not None:
            cmd.extend(["-iface", self.interface])
        else:
            if self.gateway is not None:
                cmd.append(self.gateway)

        SubCommand().run("route", cmd)

    def enable(self):
        cmd =  ["-n", "add", "-inet6", self.destination_net]
        if self.interface is not None:
            cmd.extend(["-iface", self.interface])
        ##if self.gateway is not None:
        #    cmd.append(self.gateway)
        SubCommand().run("route", cmd)
