
import ipaddress
import logging
import threading
from pyhtmlgui import Observable
from config.config import PLATFORM
from config.constants import PLATFORMS, PROTECTION_SCOPES
from core.libs.powershell import getPowershellInstance
from core.libs.subcommand import SubCommand
from core.vpnsession.common import VpnConnectionState

if PLATFORM == PLATFORMS.windows:
    from core.routing.route import RouteV4Windows as RouteV4
    from core.routing.route import RouteV6Windows as RouteV6
if PLATFORM == PLATFORMS.macos:
    from core.routing.route import RouteV4Macos as RouteV4
    from core.routing.route import RouteV6Macos as RouteV6


class Routing(Observable):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)
        self._lock = threading.Lock()

        self._wakeup_event = threading.Event()
        self._is_running = True

        self.routing_table_ipv4 = []
        self.routing_table_ipv6 = []

        if self.core is not None:
            self.__worker_thread = threading.Thread(target=self._worker_thread, daemon=True)
            self.__worker_thread.start()

    def update_async(self):
        self._wakeup_event.set()

    def shutdown(self):
        self._is_running = False
        self._wakeup_event.set()
        self.__worker_thread.join()

    def _worker_thread(self):
        while self._is_running is True:
            self._update()
            self._wakeup_event.wait()
            self._wakeup_event.clear()

    def receive_routing_table(self):
        raise NotImplementedError()

    def _update(self):
        try:
            self._lock.acquire()
            self._logger.debug("Checking and updating routing table")
            self.receive_routing_table()
            self._update_ipv4()
            self._update_ipv6()
        finally:
            self._lock.release()

    def _update_ipv4(self):
        target_routes = []
        all_server_ips = []
        default_gateway = None
        default_gateway_interface = None


        [all_server_ips.extend(item.vpn_server_config.all_ips) for _, item in self.core.vpnGroupPlanet.servers.items()]

        default_routes = [r for r in self.routing_table_ipv4 if r.destination_ip == "0.0.0.0" and r.destination_mask == "0.0.0.0"]
        if len(default_routes) > 0:
            default_gateway = default_routes[0].gateway
            default_gateway_interface = default_routes[0].interface

        # routing exception for vpn server ips
        for index, hop in enumerate(self.core.session.hops):
            if hop.connection is None or hop.connection.external_host_ip is None:
                break
            if index == 0:
                target_routes.append(RouteV4(destination_ip=hop.connection.external_host_ip, destination_mask="255.255.255.255", gateway=default_gateway, interface=default_gateway_interface))  # route vpn connection around vpn route
            elif self.core.session.hops[index - 1].connection.ipv4_remote_gateway != None:
                target_routes.append(RouteV4(destination_ip=hop.connection.external_host_ip, destination_mask="255.255.255.255", gateway=self.core.session.hops[index - 1].connection.ipv4_remote_gateway, interface=self.core.session.hops[index-1].connection.interface))  # route vpn connection around vpn route
            else:
                break  # not connected

        connected_hops = self.get_connected_hops()
        if len(connected_hops) > 0:
            for i in [0, 64, 128, 192]:
                target_routes.append(RouteV4(destination_ip="%s.0.0.0" % i, destination_mask="192.0.0.0", gateway=connected_hops[-1].connection.ipv4_remote_gateway,interface=connected_hops[-1].connection.interface))

        if self._should_enable_deadrouting() is True:
            interface = "1" if PLATFORM == PLATFORMS.windows else "lo"
            target_routes.append(RouteV4(destination_ip=  "0.0.0.0", destination_mask="128.0.0.0", gateway="10.255.255.255", interface=interface, persist=True ))
            target_routes.append(RouteV4(destination_ip="128.0.0.0", destination_mask="128.0.0.0", gateway="10.255.255.255", interface=interface, persist=True ))

        for existing_route in self.routing_table_ipv4:
            if existing_route.destination_mask == "255.255.255.255" and existing_route.destination_ip in all_server_ips: # clean old routing entrys to server ips
                if not self.route_ipv4_exists(target_routes, existing_route):
                    existing_route.delete()
                    continue
            if existing_route.destination_ip.endswith(".0.0.0") and existing_route.destination_mask.endswith(".0.0.0") and existing_route.gateway.startswith("10."): # check our routes
                if (existing_route.destination_ip.split(".")[0] in ["0", "64", "128", "192"] and existing_route.destination_mask == "192.0.0.0") or  ( existing_route.destination_ip.split(".")[0] in ["0", "128"] and  existing_route.destination_mask == "128.0.0.0" and existing_route.gateway == "10.255.255.255"):
                    if not self.route_ipv4_exists(target_routes, existing_route):
                        existing_route.delete()
                        continue

        for target_route in target_routes:
            if not self.route_ipv4_exists(self.routing_table_ipv4, target_route):
                target_route.enable()

    def _update_ipv6(self):
        target_routes = []
        connected_hops = self.get_connected_hops()

        if len(connected_hops) > 0:
            for i in ["2000", "2800", "3000", "3800"]:
                target_routes.append(RouteV6(destination_net="%s::/5" % i, gateway="fe80::8", interface=connected_hops[-1].connection.interface))

        if self._should_enable_deadrouting() is True:
            interface = "1" if PLATFORM == PLATFORMS.windows else "lo"
            target_routes.append(RouteV6(destination_net="2000::/4", gateway="::", interface=interface, persist=True))
            target_routes.append(RouteV6(destination_net="3000::/4", gateway="::", interface=interface, persist=True))

        for existing_route in self.routing_table_ipv6:
            if existing_route.destination_net in ["2000::/4", "3000::/4"]: # our deadrouting
                if not self.route_ipv6_exists(target_routes, existing_route):
                    existing_route.delete()  # route does not exist as target
                    continue
            if existing_route.gateway == "fe80::8": # check cascading routes
                for i in ["2000", "2800", "3000", "3800"]:
                    if existing_route.destination_net == "%s::/5" % i: # is our cascading route
                        if not self.route_ipv6_exists(target_routes, existing_route):
                            existing_route.delete() #route does not exist as target
                            continue

        for target_route in target_routes:
            if not self.route_ipv6_exists(self.routing_table_ipv6, target_route):
                target_route.enable()

    def route_ipv4_exists(self, routes, route):
        for existing_route in routes:
            if route.destination_ip == existing_route.destination_ip and \
                route.destination_mask == existing_route.destination_mask and \
                    (route.gateway is None or existing_route.gateway is None or
                     route.gateway == existing_route.gateway) and ( route.interface is None or existing_route.interface is None or route.interface == existing_route.interface):
                    return True
        return False

    def route_ipv6_exists(self, routes, route):
        for existing_route in routes:
            if route.destination_net == existing_route.destination_net and ( route.gateway is None or existing_route.gateway is None or route.gateway == existing_route.gateway) and ( route.interface is None or existing_route.interface is None or route.interface == existing_route.interface):
                return True
        return False

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
            if hop.connection is None or hop.connection.state.get() != VpnConnectionState.CONNECTED or hop.connection.interface is None:
                break  # not connected
            hops.append(hop)
        print("Connected Hops", hops)
        return hops

    def get_active_hops(self):
        hops = []
        for index, hop in enumerate(self.core.session.hops):
            if hop.connection is None or hop.connection.external_host_ip is None:
                break  # not connected or connecting
            hops.append(hop)
        return hops

    def _should_enable_deadrouting(self):
        if self.core.settings.leakprotection.enable_deadrouting.get() is False:
            return False
        scope = self.core.settings.leakprotection.leakprotection_scope.get()
        if scope == PROTECTION_SCOPES.disabled:
            return False
        if scope == PROTECTION_SCOPES.program and (self.core.session._should_be_connected.get() is True or self.core.frontend_active is True or self.core.settings.startup.enable_background_mode.get() is True):
            return True
        if scope == PROTECTION_SCOPES.tunnel and self.core.session._should_be_connected.get() is True:
           return True
        if scope == PROTECTION_SCOPES.permanent:
            return True
        return False


class RoutingWindows(Routing):
    def receive_routing_table(self):
        self.routing_table_ipv4 = []
        self.routing_table_ipv6 = []

        routing_table = getPowershellInstance().execute("Get-NetRoute | Select-Object -Property ifIndex,DestinationPrefix,NextHop", as_data=True)

        for route in routing_table:
            if "::" in route["NextHop"]:
                self.routing_table_ipv6.append(RouteV6(
                    destination_net = "%s" % route["DestinationPrefix"],
                    gateway         = "%s" % route["NextHop"],
                    interface       = "%s" % route["ifIndex"]
                ))
            elif "." in route["NextHop"]:
                if route["DestinationPrefix"] == "255.255.255.255/32" or route["DestinationPrefix"].startswith("127.") or route["DestinationPrefix"].startswith("192.168"):
                    continue
                self. routing_table_ipv4.append(RouteV4(
                    destination_ip   = "%s" % ipaddress.IPv4Network(route["DestinationPrefix"]).network_address,
                    destination_mask = "%s" % ipaddress.IPv4Network(route["DestinationPrefix"]).netmask,
                    gateway          = "%s" % route["NextHop"],
                    interface        = "%s" % route["ifIndex"]
                ))

    def receive_routing_table_fallback(self):
        self.routing_table_ipv4 = []
        self.routing_table_ipv6 = []

        success, stdout, stderr = SubCommand().run("route", ["print"])
        for line in stdout.split(b"\n"):
            if not b"::" in line and not b"." in line:
                continue
            while b"  " in line:
                line = line.replace(b"  ", b" ")
            if b"::" in line:
                try:
                    parts = line.strip().split(b" ")
                    if len(parts) != 4:
                        continue
                    interface = parts[0].strip().decode("UTF-8")
                    metric =  parts[1].strip().decode("UTF-8")
                    destination_net = parts[2].strip().decode("UTF-8")
                    try:
                        gateway = parts[3].strip().decode("UTF-8")
                    except:
                        continue
                    if not self._is_ip(gateway):
                        continue
                    self.routing_table_ipv6.append(RouteV6(
                        destination_net=destination_net,
                        gateway=gateway,
                        interface=interface
                    ))
                except:
                    pass
            elif b"." in line:
                try:
                    parts = b' '.join(line.split()).strip().split(b" ")
                    if len(parts) != 5:
                        continue
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
                    #interface = parts[4].strip().decode("UTF-8") # is interface ip, so dont use, we need interface id
                    #metric = parts[4].strip().decode("UTF-8")
                    self.routing_table_ipv4.append(RouteV4(
                        destination_ip=destination_ip,
                        destination_mask=destination_mask,
                        gateway=gateway,
                        interface=None
                    ))
                except:
                    pass


class RoutingMacos(Routing):
    def receive_routing_table(self):
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

