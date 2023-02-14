import logging
from datetime import datetime
from pyhtmlgui import Observable, ObservableList
from threading import Thread, Event
import traceback
import random
from core.libs.generic_state import GenericState
from config.constants import VPN_PROTOCOLS
from core.vpnsession.openvpn import OpenVPNConnection
import time
from core.vpnsession.common import VpnConnectionState, VPNConnectionError
from core.libs.permanent_property import PermanentProperty
from config.config import PLATFORM
from config.constants import PLATFORMS

if PLATFORM == PLATFORMS.windows:
    from core.vpnsession.ipsec import IpsecConnection


class SessionHop(Observable):
    def __init__(self, session, servergroup):
        super().__init__()
        self.session = session
        self.servergroup = servergroup
        self.selected_server = None
        self.connection = None

    def set_selected_server(self, selected_vpn_server_group):
        self.selected_server = selected_vpn_server_group
        if self.connection is not None:
            try:
                self.connection.state.detach_observer(self._on_connection_state_changed)  # detach old obs
            except:
                pass

        if self.session.core.settings.vpn.vpn_protocol.get() == VPN_PROTOCOLS.openvpn:
            self.connection = OpenVPNConnection(identifier=selected_vpn_server_group.identifier, core=self.session.core)
        if PLATFORM == PLATFORMS.windows:
            if self.session.core.settings.vpn.vpn_protocol.get() == VPN_PROTOCOLS.ipsec:
                self.connection = IpsecConnection(identifier=selected_vpn_server_group.identifier, core=self.session.core)

        self.connection.state.attach_observer(self._on_connection_state_changed)
        self.notify_observers()

    def _on_connection_state_changed(self, sender, new_state, **kwargs):
        self.notify_observers()
        if self.session._should_be_connected.get() is False and  new_state == VpnConnectionState.IDLE:
            self.after_disconnected()

    def after_disconnected(self):
        if self.connection is not None:
            self.connection.state.detach_observer(self._on_connection_state_changed)  # detach old obs
        self.connection = None
        self.selected_server = None
        self.notify_observers()

    def __repr__(self):
        return "SessionHop: %s" % self.servergroup.identifier

class SessionState(GenericState):
    IDLE = "idle"
    CONNECTING  = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    _DEFAULT = IDLE


class Session(Observable):
    def __init__(self, core):
        """
        :type core: core.Core
        """
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.core = core

        self.hops = ObservableList()
        self._controller_thread_wakeup_event = Event()
        self._connecting_state_changed_event = Event()
        self._should_be_connected = PermanentProperty(self.__class__.__name__ + "._should_be_connected", False)
        self._hops_stored = PermanentProperty(self.__class__.__name__ + "._hops_stored", None)
        self._running = True
        self.state = SessionState()
        self.state.attach_observer(self._on_state_changed)

        self.last_state_change_time = None
        self._number_of_connected_clients = 0

        if self._hops_stored.get() is not None:
            identifiers = self._hops_stored.get().split(",")
            for identifier in identifiers:
                servergroup = self.core.vpnGroupPlanet.search_by_identifier(identifier)
                if servergroup is not None and self.can_add_hop(servergroup):
                    self.add_hop(servergroup)
        self._hops_stored.set(",".join([hop.servergroup.identifier for hop in self.hops]))

        self._controller_thread = Thread(target=self._long_running_controller_thread, daemon=True)

    def _on_state_changed(self, sender, new_state, **kwargs):
        self._logger.debug("connection controller state changed: {}".format(new_state))
        self.last_state_change_time = datetime.now()
        self.core.leakprotection.update_async()

    def _on_hop_changed(self, sender, **kwargs):
        self.notify_observers()

    def calculate_ports(self):
        if self.state.get() == SessionState.CONNECTED:
            ip = self.hops[-1].connection.ipv4_local_ip
            if ip != None:
                p= ((int(ip.split(".")[2]) & 0x0f) << 8 ) | int(ip.split(".")[3])
                p = ("%s" % p).zfill(4)
                return ["1%s" % p, "2%s" % p, "3%s" % p]
        return None

    def _long_running_controller_thread(self):
        self._logger.debug("started")

        loop_is_running = True

        while loop_is_running:
            try:
                if not self._running:
                    if self._get_number_of_non_idle_connections() == 0:
                        self._logger.debug("exiting controller")
                        loop_is_running = False
                        break
                    else:
                        self._logger.error("couldn't exit controller: there are still connections alive")


                if self._should_be_connected.get() == True and self._running:

                    indexes_to_disconnect = [index for index, hop in enumerate(self.hops) if hasattr(hop, "should_remove") is True and hop.should_remove is True ]
                    if len(indexes_to_disconnect) > 0:
                        for hop in [h for h in reversed(self.hops[indexes_to_disconnect[0]:])]:
                            self._disconnect_hop(hop)
                            if hasattr(hop, "should_remove") is True and hop.should_remove is True:
                                hop.detach_observer(self._on_hop_changed)
                                self.hops.remove(hop)
                                self._hops_stored.set(",".join([hop.servergroup.identifier for hop in self.hops]))
                                if len(self.hops) == 0 and self._should_be_connected.get() is True:
                                    self._should_be_connected.set(False)
                            self.notify_observers()

                    if self._get_number_of_connected_vpn_connections() != len(self.hops):
                        self._logger.info("connecting")

                        if self._get_number_of_non_idle_connections() == 0:
                            self.state.set(SessionState.CONNECTING,"Connecting")
                        else:
                            self.state.set(SessionState.CONNECTING,"Reconnecting")

                        if len(self.hops) > 0:
                            try:
                                self._update_low_level_cascade()
                                #self._create_new_low_level_cascade()
                            except Exception as e:
                                self._logger.debug(traceback.format_exc())
                                self._logger.error("unable to create the cascade: {}".format(e))
                                self.state.set(SessionState.CONNECTING, "Unable to connect")
                            else:
                                try:
                                    self._logger.debug("connecting all")
                                    self._connect_all()
                                    self._logger.debug("all connected")
                                except VPNConnectionError:
                                    self._logger.info("connecting failed, retrying in a few moments")
                                    self.state.set(self.state.get(), "Connecting failed. Retrying in a few moments.")
                                    self._disconnect_all()
                                except:
                                    self._logger.info("connecting failed, retrying in a few moments")
                                    self._logger.debug(traceback.format_exc())
                                    self.state.set(self.state.get(), "Connecting failed. Retrying in a few moments.")
                                    self._disconnect_all()
                                else:
                                    self._logger.info("all connected")
                                    self.state.set(SessionState.CONNECTED, "Connection established")

                        else:
                            self.state.set(SessionState.IDLE)
                else:
                    if self._get_number_of_non_idle_connections() != 0:
                        self._logger.info("disconnecting")
                        self.state.set(SessionState.DISCONNECTING, "Disconnecting")
                        self._disconnect_all()

                        if self._get_number_of_non_idle_connections() == 0:
                            self.state.set(SessionState.IDLE)
                    elif self.state != SessionState.IDLE and self._get_number_of_non_idle_connections() == 0:
                        #self._logger.info("all connections are already disconnected")
                        self.state.set(SessionState.IDLE)

            except Exception as e:
                self._logger.error("unexpected exception: {}".format(e))
                self._logger.debug(traceback.format_exc())

            if self._running is True:
                self._controller_thread_wakeup_event.wait(timeout=5)
                self._controller_thread_wakeup_event.clear()

        self._logger.debug("stopped")

    def get_number_of_paths(self, hop_list=None):
        """
        :type vpn_groups: list[core.vpn.vpn_groups.VpnServerOrVpnServerCollection]
        """
        return len(self.get_all_possible_paths(hop_list))

    def get_all_possible_paths(self, hop_list, limit = 10):
        """
        :type vpn_groups: list[core.vpn.vpn_groups.VpnServerOrVpnServerCollection]
        :rtype: list[list[core.vpn.vpn_groups.VpnServer]]
        """
        if len(hop_list) == 0:
            return []

        # get a list of the lowest level vpn groups (country1 -> a1, a2, a3, b1, c1, c2)
        vpn_servers = []
        for hop in hop_list:
            vpnservers = hop.servergroup.get_vpn_servers()
            random.shuffle(vpnservers)
            vpn_servers.append(vpnservers)
        if not vpn_servers:
            raise Exception("an error occurred while getting the servers")
        paths = [[g] for g in vpn_servers[0]]
        for i in range(1, len(vpn_servers)):
            new_paths = []
            new_paths_length = 0
            for group in vpn_servers[i]:
                for path in paths:
                    if group not in path:
                        new_path = path[:]
                        new_path.append(group)
                        new_paths.append(new_path)
                        new_paths_length = len(new_paths)
                        if new_paths_length >= limit: break
                if new_paths_length >= limit: break
            paths = new_paths
        return paths

    def _create_new_low_level_cascade(self):
        if self._get_number_of_non_idle_connections() > 0:
            raise Exception("at least one connection not idle")

        # FIXME: set failed connections to lower priority
        all_possible_paths = self.get_all_possible_paths(self.hops)
        if not all_possible_paths:
            raise Exception("couldn't find a valid cascade for the selected locations")
        self._logger.debug("all possible paths: {}".format(all_possible_paths))
        path = random.choice(all_possible_paths)
        self._logger.debug(path)
        assert len(path) == len(self.hops)

        i = 0
        for selected_vpn_server_group in path:
            self.hops[i].set_selected_server(selected_vpn_server_group)
            i += 1
        self.notify_observers()

    def _update_low_level_cascade(self):
        # FIXME: set failed connections to lower priority
        all_possible_paths = self.get_all_possible_paths(self.hops)
        if not all_possible_paths:
            raise Exception("couldn't find a valid cascade for the selected locations")
        self._logger.debug("all possible paths: {}".format(all_possible_paths))
        path = random.choice(all_possible_paths)
        self._logger.debug(path)
        assert len(path) == len(self.hops)
        i = 0
        for selected_vpn_server_group in path:
            if self.hops[i].connection is None or self.hops[i].selected_server is None:
                self.hops[i].set_selected_server(selected_vpn_server_group)
            i += 1
        self.notify_observers()

    def can_add_hop(self, servergroup):
        """
        :type vpn_group: core.vpn.vpn_groups.VpnServerOrVpnServerCollection
        """
        if self.core.settings.vpn.vpn_protocol.get() == VPN_PROTOCOLS.ipsec:
            return len(self.hops) == 0
        elif len(self.hops) == 0:
            return True
        elif len(self.hops) >= self.core.settings.vpn.openvpn.cascading_max_hops.get():
            return False
        else:
            tmp_hops = self.hops[:]
            tmp_hops.append(SessionHop(self, servergroup))
            return len(self.get_all_possible_paths(tmp_hops, limit=1)) > 0

    def add_hop(self, servergroup):
        if not self.can_add_hop(servergroup):
            raise Exception("no more free hops available")
        hop = SessionHop(self, servergroup)
        hop.attach_observer(self._on_hop_changed)
        self.hops.append(hop)
        self._hops_stored.set(",".join([hop.servergroup.identifier for hop in self.hops]))
        self._controller_thread_wakeup_event.set()
        self.notify_observers()

    def add_hop_at_index(self, servergroup, index):
        if not self.can_add_hop(servergroup):
            raise Exception("no more free hops available")
        hop = SessionHop(self, servergroup)
        hop.attach_observer(self._on_hop_changed)
        self.hops.insert(index, hop)
        self._hops_stored.set(",".join([hop.servergroup.identifier for hop in self.hops]))
        self._controller_thread_wakeup_event.set()
        self.notify_observers()

    def remove_hop_by_index(self, index):
        if self.hops[index].connection is not None and self.hops[index].connection.state.get() !=  VpnConnectionState.IDLE:
            self.hops[index].should_remove = True
            self._controller_thread_wakeup_event.set()
        else:
            self.hops[index].detach_observer(self._on_hop_changed)
            del self.hops[index]
            self._hops_stored.set(",".join([hop.servergroup.identifier for hop in self.hops]))
            self.notify_observers()
        if len(self.hops) == 0 and self._should_be_connected.get() is True:
            self._should_be_connected.set(False)

    def _get_number_of_non_idle_connections(self):
        return len([hop for hop in self.hops if hop.connection is not None and hop.connection.state.get() !=  VpnConnectionState.IDLE ])

    def _get_number_of_connected_vpn_connections(self):
        return len([hop for hop in self.hops if hop.connection is not None and hop.connection.state.get() ==  VpnConnectionState.CONNECTED ])

    def _disconnect_all(self):
        self._logger.debug("disconnecting all")
        for hop in reversed(self.hops):
            self._disconnect_hop(hop)

    def _disconnect_hop(self, hop):
        try:
            if hop.connection is not None:
                if hop.connection.state.get() not in [VpnConnectionState.IDLE, VpnConnectionState.DISCONNECTING]:
                    self._logger.debug("disconnecting {}".format(hop.connection))
                    hop.connection.disconnect()
                else:
                    hop.after_disconnected()
                    self._logger.debug("disconnecting {} not necessary".format(hop.connection))
        except:
            self._logger.critical("Unable to disconnect. This is a serious error! You may want to reboot your computer.")
            self._logger.debug(traceback.format_exc())

    def _connect_all(self):
        hop_number = 0
        for hop in self.hops:
            hop_number += 1
            self.state.set(self.state.get(),"Connecting to {}".format(hop.selected_server.name))
            if hop.connection is None:
                raise Exception("Hops has no connection")

            if hop.connection.state.get() == VpnConnectionState.CONNECTED:
                self._logger.debug("Hop #{} ({}) is already connected".format(hop_number, hop.selected_server.name))
                continue

            self._logger.debug("connecting to hop #{} ({})".format(hop_number, hop.selected_server.name))

            hop.connection.connect(hop.selected_server, hop_number)
            self._connecting_state_changed_event.clear()

            if hop.connection is None:
                self._logger.debug("Hop #{} connection removed".format(hop_number))
                raise VPNConnectionError()

            hop.connection.state.attach_observer(self._wait_for_state_change)
            started_waiting = time.time()
            CONNECT_TIMEOUT = 60
            while hop.connection.state.get() not in [VpnConnectionState.CONNECTED, VpnConnectionState.IDLE] and self._should_be_connected.get() == True:
                self._logger.debug("waiting for state change")
                signal_received = self._connecting_state_changed_event.wait(timeout=CONNECT_TIMEOUT)
                self._connecting_state_changed_event.clear()
                if not signal_received or time.time() - started_waiting >= CONNECT_TIMEOUT:
                    break
            hop.connection.state.detach_observer(self._wait_for_state_change)
            if hop.connection.state.get() != VpnConnectionState.CONNECTED:
                self._logger.error("Couldn't connect within {} seconds".format(CONNECT_TIMEOUT))
                raise VPNConnectionError()

            highest_connected_hop = [hop for hop in self.hops if hop.connection is not None and hop.connection.state.get() == VpnConnectionState.CONNECTED][-1]
            if highest_connected_hop.connection.ipv4_local_ip is not None:
                highest_hop_ipv4 = highest_connected_hop.connection.ipv4_local_ip
                highest_hop_ipv6 = highest_connected_hop.connection.ipv6_local_ip
                self.core.leakprotection.set_highest_hop_local_ip(highest_hop_ipv4, highest_hop_ipv6)

    def _wait_for_state_change(self, sender, new_state, **kwargs):
        self._connecting_state_changed_event.set()

    def connect(self):
        self._logger.debug("received connect request")
        self._should_be_connected.set(True)
        self._controller_thread_wakeup_event.set()
        self.notify_observers()

    def disconnect(self):
        self._logger.debug("received disconnect request")
        self._should_be_connected.set(False)
        self._controller_thread_wakeup_event.set()
        self._connecting_state_changed_event.set()
        self.notify_observers()

    def start(self):
        self._controller_thread.start()

    def quit(self):
        self._logger.debug("quit")
        self._running = False
        #self.disconnect() # don't call disconnect here, disconnect is for user button and sets self._should_be_connected to false,
        #we don't want that on quit, only us user explicitly reqested a disconnect, firewall and other stuff use _should_be_connected to determine what they should do

        self._controller_thread_wakeup_event.set()
        self._connecting_state_changed_event.set()

        self._logger.debug("waiting for controller thread to shut down")
        self._controller_thread.join(20)
        if self._controller_thread.is_alive():
            self._logger.error("controller thread didn't shut down within 20 seconds")
        else:
            self._logger.debug("controller thread did shut down successfully")
