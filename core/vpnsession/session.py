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
        self.last_connection_failed = False # so the ui can show if hop has failed last connection, because the actual connection and selected server will be removed after failure
        self.should_remove = False
        self._logger = logging.getLogger(self.__class__.__name__)

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
        if self.session._should_be_connected.get() is False and new_state == VpnConnectionState.IDLE:
            self.last_connection_failed = False
            self.after_disconnected()

        if self.session._should_be_connected.get() is True and self.should_remove == False:
            if new_state not in [VpnConnectionState.CONNECTED, VpnConnectionState.CONNECTING]:
                self.last_connection_failed = True
                if self.selected_server is not None:
                    self.selected_server.last_connection_failed = True

            if new_state in [VpnConnectionState.CONNECTED]:
                self.last_connection_failed = False
                if self.selected_server is not None:
                    self.selected_server.last_connection_failed = False

        self._logger.debug("Connection state changed for Hop %s, %s" % (self.servergroup.name, new_state))
        self.session.core.check_connection()
        self.notify_observers()

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
        if self.core.settings.startup.enable_background_mode.get() == True and self.core.settings.startup.connect_on_start.get() == True:
            self._should_be_connected.set(True)

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

    def _on_hop_changed(self, sender, **kwargs):
        self.notify_observers()

    def calculate_ports(self):
        if self.state.get() == SessionState.CONNECTED:
            try:
                ip = self.hops[-1].connection.ipv4_local_ip
                if ip != None:
                    p= ((int(ip.split(".")[2]) & 0x0f) << 8 ) | int(ip.split(".")[3])
                    p = ("%s" % p).zfill(4)
                    return ["1%s" % p, "2%s" % p, "3%s" % p]
            except:
                pass
        return None

    def _long_running_controller_thread(self):

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
                        hops_to_remove = [h for h in reversed(self.hops[indexes_to_disconnect[0]:])]
                        for hop in hops_to_remove:
                            self._disconnect_hop(hop)
                            if hasattr(hop, "should_remove") is True and hop.should_remove is True:
                                hop.detach_observer(self._on_hop_changed)
                                self.hops.remove(hop)
                                self._hops_stored.set(",".join([hop.servergroup.identifier for hop in self.hops]))
                                if len(self.hops) == 0 and self._should_be_connected.get() is True:
                                    self._should_be_connected.set(False)
                            self.notify_observers()
                        self.state.set(self.state.get(), "Removed %s hops" % len(indexes_to_disconnect))

                    if self._get_number_of_connected_vpn_connections() != len(self.hops):
                        self._logger.info("connecting")

                        if self._get_number_of_non_idle_connections() == 0:
                            self.state.set(SessionState.CONNECTING,"Connecting to %s" % ",".join([hop.servergroup.name for hop in self.hops]))
                        else:
                            self.state.set(SessionState.CONNECTING,"Reconnecting to %s" % ",".join([hop.servergroup.name for hop in self.hops]))

                        if len(self.hops) > 0:
                            try:
                                self._update_low_level_cascade()
                            except Exception as e:
                                self._logger.debug(traceback.format_exc())
                                self._logger.error("unable to create the cascade: {}".format(e))
                                self.state.set(SessionState.CONNECTING, "Unable to connect %s" % ",".join([hop.servergroup.name for hop in self.hops]))
                            else:
                                try:
                                    self._logger.debug("connecting all")
                                    self._connect_all()
                                    self._logger.debug("all connected")
                                except VPNConnectionError:
                                    self._logger.info("connecting failed, retrying in a few moments")
                                    self.state.set(self.state.get(), "Connecting failed. Retrying in a few moments.")
                                except:
                                    self._logger.info("connecting failed, retrying in a few moments")
                                    self._logger.debug(traceback.format_exc())
                                    self.state.set(self.state.get(), "Connecting failed. Retrying in a few moments.")
                                    self._disconnect_all()
                                else:
                                    self._logger.info("all connected")
                                    self.state.set(SessionState.CONNECTED, "Connection established to %s" % ",".join([hop.servergroup.name for hop in self.hops]))

                        else:
                            self.state.set(SessionState.IDLE, "VPN Idle %s" % ",".join([hop.servergroup.name for hop in self.hops]))
                    else:
                        if len(self.hops) > 0:
                            if len([hop for hop in self.hops if  hop.connection is not None and hop.connection.state.get() == VpnConnectionState.CONNECTED]) == len(self.hops):
                                if self.state.get() != SessionState.CONNECTED:
                                    self.state.set(SessionState.CONNECTED, "Connection established to %s" % ",".join([hop.servergroup.name for hop in self.hops]))

                else:
                    if self._get_number_of_non_idle_connections() != 0:
                        self._logger.info("disconnecting")
                        self.state.set(SessionState.DISCONNECTING, "Disconnecting from %s" % ",".join([hop.servergroup.name for hop in self.hops]))
                        self._disconnect_all()
                        if self._get_number_of_non_idle_connections() == 0:
                            self.state.set(SessionState.IDLE, "VPN Idle %s" % ",".join([hop.servergroup.name for hop in self.hops]))
                    elif self.state != SessionState.IDLE and self._get_number_of_non_idle_connections() == 0:
                        #self._logger.info("all connections are already disconnected")
                        self.state.set(SessionState.IDLE, "VPN Idle %s" % ",".join([hop.servergroup.name for hop in self.hops]))

            except Exception as e:
                self._logger.error("unexpected exception: {}".format(e))
                self._logger.debug(traceback.format_exc())

            if self._running is True:
                self._controller_thread_wakeup_event.wait(timeout=5)
                self._controller_thread_wakeup_event.clear()

        self._logger.debug("stopped")

    def get_random_paths(self, hop_list, limit = 1):
        vpn_servers_per_hop = []
        for hop in hop_list:
            if hop.connection is not None and hop.selected_server is not None:
                vpn_servers_per_hop.append([hop.selected_server])
            else:
                vpnservers = hop.servergroup.get_vpn_servers()
                random.shuffle(vpnservers)
                vpn_servers_per_hop.append(vpnservers)

        paths_good = []
        paths_all = []
        for path in self._get_next_hops([], vpn_servers_per_hop):
            if len(path) != len(hop_list):
                continue
            if not False in [s.is_online and (s.last_connection_failed is False or random.randint(0,10) == 1) for s in path]:
                paths_good.append(path)
            else:
                paths_all.append(path)
            if len(paths_good) >= limit:
                break
        if len(paths_good) > 0:
            return paths_good
        return paths_all

    def _get_next_hops(self, current_path, vpn_servers_for_next_hops):
        for vpn_server_for_next_hop in vpn_servers_for_next_hops[0]:
            if vpn_server_for_next_hop not in current_path:
                if len(vpn_servers_for_next_hops) == 1:
                    yield [vpn_server_for_next_hop]
                else:
                    for next_hops in self._get_next_hops(current_path + [vpn_server_for_next_hop], vpn_servers_for_next_hops[1:]):
                        yield [vpn_server_for_next_hop] + next_hops
        return []

    def _update_low_level_cascade(self):
        paths = self.get_random_paths(self.hops,limit=1)
        if not paths:
            raise Exception("couldn't find a valid cascade for the selected locations")
        path = random.choice(paths)
        self._logger.debug("Selected path %s" % path)
        i = 0
        for selected_vpn_server_group in path:
            if self.hops[i].connection is None or self.hops[i].selected_server is None:
                self.hops[i].set_selected_server(selected_vpn_server_group)
                self._logger.debug("Selected Hop %s Server %s" % (i, selected_vpn_server_group))
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
            return len(self.get_random_paths(tmp_hops, limit=1)) > 0

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
        hop_to_remove = self.hops[index]
        hop_to_remove.should_remove = True
        if hop_to_remove.connection is None or hop_to_remove.connection.state.get() == VpnConnectionState.IDLE:
            hop_to_remove.detach_observer(self._on_hop_changed)
            del self.hops[index]
            self._hops_stored.set(",".join([hop.servergroup.identifier for hop in self.hops]))
            self.notify_observers()
        hop_to_remove.notify_observers()
        if len(self.hops) == 0 and self._should_be_connected.get() is True:
            self._should_be_connected.set(False)
        self._controller_thread_wakeup_event.set()
        self._connecting_state_changed_event.set()

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
            if hop.connection is None:
                self._logger.debug("Hop %s has no connection, connect all failed for now" % hop_number)
                return
            if hop.selected_server is None:
                self._logger.debug("Hop %s has no selected server, connect all failed for now" % hop_number)
                return

            hop_number += 1
            self.state.set(self.state.get(),"Connecting to {}".format(hop.selected_server.name))

            if hop.connection.state.get() == VpnConnectionState.CONNECTED:
                self._logger.debug("Hop #{} ({}) is already connected".format(hop_number, hop.selected_server.name))
                continue

            self._logger.debug("connecting to hop #{} ({})".format(hop_number, hop.selected_server.name))

            if hop_number > 1:  # wait on lower hops to get stable
                time.sleep(3)

            hop.connection.connect(hop.selected_server, hop_number)
            self._connecting_state_changed_event.clear()

            if hop.connection is None:
                self._logger.debug("Hop #{} connection removed".format(hop_number))
                self._disconnect_hop(hop)
                raise VPNConnectionError()

            hop.connection.state.attach_observer(self._wait_for_state_change)
            started_waiting = time.time()
            CONNECT_TIMEOUT = 45
            while hop.connection.state.get() not in [VpnConnectionState.CONNECTED, VpnConnectionState.IDLE] and self._should_be_connected.get() == True:
                if hop.should_remove is True:
                    break
                if len([h for h in self.hops[0:self.hops.index(hop)] if h.should_remove is True]) > 0:
                    break
                self._logger.debug("waiting for state change")
                signal_received = self._connecting_state_changed_event.wait(timeout=CONNECT_TIMEOUT)
                self._connecting_state_changed_event.clear()
                if not signal_received or time.time() - started_waiting >= CONNECT_TIMEOUT:
                    break
            hop.connection.state.detach_observer(self._wait_for_state_change)
            if hop.connection.state.get() != VpnConnectionState.CONNECTED:
                self._logger.error("Couldn't connect within {} seconds".format(CONNECT_TIMEOUT))
                self._disconnect_hop(hop)
                raise VPNConnectionError()
            self.state.set(self.state.get(),"Connected to {}".format(hop.selected_server.name))

    def _wait_for_state_change(self, sender, new_state, **kwargs):
        self._connecting_state_changed_event.set()

    def connect(self):
        if self.state.get() == VpnConnectionState.IDLE:
            self.state.set(SessionState.CONNECTING, "Connection startup requested")
        self._should_be_connected.set(True)
        self._controller_thread_wakeup_event.set()
        self.notify_observers()

    def disconnect(self):
        if self.state.get() in [VpnConnectionState.CONNECTED, VpnConnectionState.CONNECTING, SessionState.DISCONNECTING]:
            self.state.set(SessionState.DISCONNECTING, "Disconnect requested")
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
