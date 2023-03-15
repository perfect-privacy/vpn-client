import ipaddress
import logging

from core.libs.subcommand import SubCommand
from config.files import ROUTE, NETSH

class RouteV6():
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

class RouteV6Macos(RouteV6):
    def delete(self):
        if self.interface is None:
            return
        SubCommand().run("route", ["-n", "delete", "-inet6", self.destination_net, "-iface", self.interface])

    def enable(self):
        if self.interface is None:
            return
        SubCommand().run("route", ["-n", "add", "-inet6", self.destination_net,"-iface",  self.interface])

class RouteV6Windows(RouteV6):
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



class RouteV4():
    def __init__(self, destination_ip, destination_mask, gateway = None, interface = None, persist = False):
        self.destination_ip = destination_ip
        self.destination_mask = destination_mask
        self.gateway = gateway
        self.interface = interface
        self.persist = persist

    def enable(self):
        raise NotImplementedError()
    def delete(self):
        raise NotImplementedError()

    def __repr__(self):
        return "%s/%s -> %s : %s" % (self.destination_ip, self.destination_mask, self.gateway, self.interface)


class RouteV4Windows(RouteV4):
    def delete(self):
        args = ["interface", "ipv4", "delete", "route", "%s/%s" % (self.destination_ip, ipaddress.IPv4Network('0.0.0.0/%s' % self.destination_mask).prefixlen)]
        if self.gateway is not None:
            args.append(self.gateway)
        if self.interface is not None:
            args.append("interface=%s" % self.interface)
        if self.persist is True:
            args.append("store=persistent")
        SubCommand().run(NETSH, args)

    def enable(self):
        args = ["interface", "ipv4", "add", "route", "%s/%s" % (self.destination_ip, ipaddress.IPv4Network('0.0.0.0/%s' % self.destination_mask).prefixlen)]
        if self.gateway is not None:
            args.append(self.gateway)
        if self.interface is not None:
            args.append("interface=%s" % self.interface)
        if self.persist is True:
            args.append("store=persistent")
        else:
            args.append("store=active")
        SubCommand().run(NETSH, args)
'''
    def delete(self):
        cmd =  ["delete", self.destination_ip, "mask", self.destination_mask]
        if self.gateway is not None:
            cmd.append(self.gateway)
        if self.interface is not None:
            cmd.extend(["IF", self.interface])
        SubCommand().run(ROUTE, cmd)

    def enable(self):
        cmd = ["add"]
        if self.persist is True:
            cmd.append("-p")
        cmd.extend([ self.destination_ip, "mask",  self.destination_mask])
        if self.gateway is not None:
            cmd.append(self.gateway)
        if self.interface is not None:
            cmd.extend(["IF", self.interface])
        SubCommand().run(ROUTE, cmd)
'''


class RouteV4Macos(RouteV4):
    def delete(self):
        cmd = ["-n", "delete", "-net", "%s/%s" % (self.destination_ip, ipaddress.IPv4Network('0.0.0.0/%s' % self.destination_mask).prefixlen)]
        if self.gateway is not None:
            cmd.append(self.gateway)
        SubCommand().run("route", cmd)

    def enable(self):
        cmd = ["-n", "add", "-net", "%s/%s" % (self.destination_ip, ipaddress.IPv4Network('0.0.0.0/%s' % self.destination_mask).prefixlen)]
        if self.gateway is not None:
            cmd.append(self.gateway)
        SubCommand().run("route",)

