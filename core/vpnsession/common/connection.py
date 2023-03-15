import logging
from threading import RLock
from .connection_state import VpnConnectionState
from pyhtmlgui import Observable

class VPNConnection(Observable):

    def __init__(self, identifier, core):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__ + " ({})".format(identifier))
        self._identifier = identifier
        self.core = core
        self.state = VpnConnectionState()

        self.hop_number = None
        self.external_host_ip  = None
        self.interface = None

        self.ipv4_local_ip       = None  # local vpn adapter ipv4
        self.ipv4_local_netmask  = None  # local vpn adapter netmask
        self.ipv4_remote_gateway = None  # vpn adapter gateway ipv4 (a 10.x.x.x ip on vpn server)
        self.ipv4_dns_servers    = []    # dns servers pushed by openvpn server
        self.ipv6_local_ip       = None  # local vpn adapter ipv6
        self.ipv6_local_netmask  = None  # local vpn adapter netmask
        self.ipv6_remote_gateway = None  # vpn adapter gateway ipv6 (a 10.x.x.x ip on vpn server)


        self._connect_disconnect_lock = RLock()
        self.on_invalid_credentials_detected = Observable()

    def connect(self, servergroup, hop_number):
        self._logger.info("connecting VPN")
        with self._connect_disconnect_lock:
            if self.state.get() != VpnConnectionState.IDLE:
                self._logger.warning("connecting cancelled: VPN is already active")
                raise VPNConnectionError()
            self.hop_number = hop_number
            self._connect(servergroup, hop_number)

    def disconnect(self):
        self._logger.info("disconnecting")
        with self._connect_disconnect_lock:
            if self.state.get() == VpnConnectionState.IDLE:
                self._logger.warning("disconnecting cancelled: VPN is already inactive")
                return
            elif self.state.get() == VpnConnectionState.DISCONNECTING:
                self._logger.warning("disconnecting cancelled: VPN is already disconnecting")
                return
            self._disconnect()

    def _connect(self, servergroup, hop_number):
        raise NotImplementedError()

    def _disconnect(self):
        raise NotImplementedError()


class VPNConnectionError(Exception):
    def __init__(self, message="General VPN connection error"):
        super(VPNConnectionError, self).__init__(message)
