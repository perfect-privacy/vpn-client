import ipaddress
import logging
import threading

from config.config import PLATFORM
from config.constants import PLATFORMS
from core.libs.permanent_property import PermanentProperty
from core.libs.powershell import getPowershellInstance
from core.libs.subcommand import SubCommand
from config.files import ROUTE, NETSH

if PLATFORM == PLATFORMS.windows:
    from core.routing.route import RouteV4Windows as RouteV4
    from core.routing.route import RouteV6Windows as RouteV6
if PLATFORM == PLATFORMS.macos:
    from core.routing.route import RouteV4Macos as RouteV4
    from core.routing.route import RouteV6Macos as RouteV6

class Routes():
    def __init__(self, core):
        self.core = core
        self._lock = threading.Lock()

    def get_routing_table(self):
        raise NotImplementedError()

    def _is_ip(self, str):
        try:
            ip = ipaddress.ip_address(str)
            return True
        except:
            pass
        return False

    def get_connected_hops(self):
        hops = []
        for index, hop in enumerate(self.core.session.hops):
            if hop.connection is None or hop.connection.remote_ip is None or hop.connection.ipv4_remote_gateway is None or hop.connection.openvpn_device == "" or hop.connection.openvpn_device is None:
                break  # not connected
            hops.append(hop)
        return hops

class RoutesV4(Routes):
    def __init__(self, core):
        self.core = core
        self.cascading_nets = [ 128, 64, 32, 16]
        self._lock = threading.Lock()

    def get_routing_table(self):
        raise NotImplementedError()

    def _is_ip(self, str):
        try:
            ip = ipaddress.ip_address(str)
            return True
        except:
            pass
        return False

    def update(self):
        try:
            self._lock.acquire()
            self._logger.debug("Checking routing state")
            self._update()
        finally:
            self._lock.release()

    def _update(self):
        all_server_ips = []
        [all_server_ips.extend(item.vpn_server_config.all_ips) for _, item in self.core.vpnGroupPlanet.servers.items()]

        existing_routes = self.get_routing_table()
        default_routes = [r for r in existing_routes if r.destination_ip == "0.0.0.0" and r.destination_mask == "0.0.0.0"]
        default_gateway = None
        if len(default_routes) > 0:
            default_gateway = default_routes[0].gateway

        target_routes = []

        connected_hops = self.get_connected_hops()

        for index, hop in enumerate(connected_hops):
            target_routes.append(RouteV4(destination_ip=hop.connection.remote_ip, destination_mask="255.255.255.255", gateway=default_gateway if index == 0 else connected_hops[index-1].connection.ipv4_remote_gateway))  # route vpn connection around vpn route

        if len(connected_hops) > 0:
            for i in [0, 64, 128, 192]:
                target_routes.append(RouteV4(destination_ip="%s.0.0.0" % i, destination_mask="64.0.0.0", gateway=connected_hops[-1].connection.ipv4_remote_gateway, interface=connected_hops[-1].connection.openvpn_device))

        if True: # deadrouting
            target_routes.append(RouteV4(destination_ip=  "0.0.0.0", destination_mask="128.0.0.0", gateway="10.255.255.255", persist=True ))
            target_routes.append(RouteV4(destination_ip="128.0.0.0", destination_mask="128.0.0.0", gateway="10.255.255.255", persist=True ))

        for existing_route in existing_routes:
            if existing_route.destination_mask == "255.255.255.255" and existing_route.destination_ip in [all_server_ips]: # clean old routing entrys to server ips
                if not self.route_exists(target_routes, existing_route):
                    existing_route.delete()
                    continue
            if existing_route.destination_ip.endswith(".0.0.0") and existing_route.destination_mask.endswith(".0.0.0") and existing_route.gateway.startswith("10."): # check our routes
                if (existing_route.destination_ip.split(".")[0] in ["0", "64", "128", "192"] and existing_route.destination_mask == "64.0.0.0") or  ( existing_route.destination_ip.split(".")[0] in ["0", "128"] and  existing_route.destination_mask == "128.0.0.0" and existing_route.gateway == "10.255.255.255"):
                    if not self.route_exists(target_routes, existing_route):
                        existing_route.delete() #route does not exist as target
                        continue

        for target_route in target_routes:
            if not self.route_exists(existing_routes, target_route):
                target_route.enable()

    def route_exists(self, routes, route):
        for existing_route in routes:
            if route.destination_ip == existing_route.destination_ip and \
                route.destination_mask == existing_route.destination_mask and \
                route.gateway == existing_route.gateway and ( route.interface is None or existing_route.interface is None or route.interface == existing_route.interface):
                    return True
        return False

class RoutesV4Windows(RoutesV4):
    def get_routing_table(self):
        routes = []
        routing_table = getPowershellInstance().execute("Get-NetRoute|  Select-Object -Property ifIndex,DestinationPrefix,NextHop", as_data=True)

        for route in routing_table:
            if not "." in route["NextHop"] or route["NextHop"] == "0.0.0.0":
                continue
            if route["DestinationPrefix"] == "255.255.255.255/32" or route["DestinationPrefix"].startswith("127.") or route["DestinationPrefix"].startswith("192.168"):
                continue
            routes.append(RouteV4(
                destination_ip   = ipaddress.IPv4Network(route["DestinationPrefix"]).netmask,
                destination_mask = ipaddress.IPv4Network(route["DestinationPrefix"]).network_address,
                gateway          = route["NextHop"],
                interface        = route["ifIndex"]
            ))
        return routes

    def get_routing_table_fallback(self):
        routes = []
        success, stdout, stderr = SubCommand().run("route", ["print", "-4"])
        lines = stdout.split(b"\n")
        for line in lines:
            try:
                parts = b' '.join(line.split()).strip().split(b" ")
                destination_ip = parts[0].strip().decode("UTF-8")
                if destination_ip == "255.255.255.255" or destination_ip.startswith("127.") or destination_ip.startswith("192.168"):
                    continue
                destination_mask = parts[1].strip().decode("UTF-8")
                try:
                    gateway = parts[2].strip().decode("UTF-8")
                except:
                    continue
                if not self._is_ip(gateway):
                    continue
                #metric = parts[4].strip().decode("UTF-8")
                routes.append(RouteV4(
                    destination_ip=destination_ip,
                    destination_mask=destination_mask,
                    gateway=gateway,
                    interface=None
                ))
            except:
                pass
        return routes

class RoutesV4Macos(RoutesV4):
    def get_routing_table(self):
        routes = []
        success, stdout, stderr = SubCommand().run("netstat", ["-rn", ])
        stdout = stdout.decode("UTF-8")
        while "  " in stdout:
            stdout = stdout.replace("  ", " ")
        lines = stdout.split("\n")
        for line in lines:
            try:
                if "::" in line:
                    continue
                parts = line.split(" ")
                if len(parts) < 4:
                    continue
                destination_ip = parts[0].strip()
                if destination_ip.startswith("255.255.255.255") or destination_ip.startswith("127") or destination_ip.startswith("192.168"):
                    continue
                if destination_ip == "default":
                    destination_ip = "0.0.0.0/0"
                if "/" not in destination_ip:
                    continue
                destination_mask = ipaddress.IPv4Network(destination_ip).netmask
                destination_ip = destination_ip.split("/")[0]
                gateway = parts[1].strip()
                if not self._is_ip(gateway):
                    continue
                flags = parts[2].strip()
                interface = parts[3].strip()
                routes.append(RouteV4(
                    destination_ip=destination_ip,
                    destination_mask=destination_mask,
                    gateway=gateway,
                    interface=interface
                ))
            except:
                pass
        return routes


class RoutesV6(Routes):

    def update(self):
        existing_routes = self.get_routing_table()

        target_routes = []

        connected_hops = self.get_connected_hops()
        if len(connected_hops) > 0:
            for i in ["2000", "2800", "3000", "3800"]:
                target_routes.append(RouteV6( destination_net="%s::/5" % i, gateway="fe80::8", interface=connected_hops[-1].connection.openvpn_device))

        if True: # deadrouting
            target_routes.append(RouteV6(destination_net="2000::/4", gateway=None, interface="1", persist=True,))
            target_routes.append(RouteV6(destination_net="3000::/4", gateway=None, interface="1", persist=True))

        for existing_route in existing_routes:
            if existing_route.destination_net in ["2000::/4", "3000::/4"]: # our deadrouting
                if not self.route_exists(target_routes, existing_route):
                    existing_route.delete()  # route does not exist as target
                    continue
            if existing_route.gateway == "fe80::8": # check cascading routes
                for i in ["2000", "2800", "3000", "3800"]:
                    if existing_route.destination_net == "%s::/5" % i: # is our cascading route
                        if not self.route_exists(target_routes, existing_route):
                            existing_route.delete() #route does not exist as target
                            continue

        for target_route in target_routes:
            if not self.route_exists(existing_routes, target_route):
                target_route.enable()

    def route_exists(self, routes, route):
        for existing_route in routes:
            if route.destination_net == existing_route.destination_net and route.gateway == existing_route.gateway and ( route.interface is None or existing_route.interface is None or route.interface == existing_route.interface):
                return True
        return False

class RoutesV6Windows(RoutesV6):
    def get_routing_table(self):
        routes = []
        routing_table = getPowershellInstance().execute("Get-NetRoute | Select-Object -Property ifIndex,DestinationPrefix,NextHop", as_data=True)
        for route in routing_table:
            if not "::" in route["NextHop"]:
                continue
            routes.append(RouteV6(
                destination_net  = route["DestinationPrefix"],
                gateway          = route["NextHop"],
                interface        = route["ifIndex"]
            ))
        return routes

    def get_routing_table_fallback(self):
        routes = []
        success, stdout, stderr = SubCommand().run("route", ["print", "-6"])
        lines = stdout.split(b"\n")
        for line in lines:
            try:
                if b"::" not in line:
                    continue
                while b"  " in line:
                    line = line.replace(b"  ", b" ")
                parts = line.strip().split(b" ")
                interface =  parts[0].strip().decode("UTF-8")
                #metric =  parts[1].strip().decode("UTF-8")
                destination_net =  parts[2].strip().decode("UTF-8")
                try:
                    gateway = parts[3].strip().decode("UTF-8")
                except:
                    continue
                destination_ip = parts[0].strip().decode("UTF-8")

                if not self._is_ip(gateway):
                    continue
                routes.append(RouteV6(
                    destination_net=destination_net,
                    gateway=gateway,
                    interface=interface
                ))
            except:
                pass
        return routes

