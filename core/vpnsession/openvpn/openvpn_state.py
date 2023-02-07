from core.libs.generic_state import GenericState


class OpenVPNState(GenericState):
    # OpenVPN states
    OPENVPN_STATE_CONNECTING = "CONNECTING"  # OpenVPN's initial state.
    OPENVPN_STATE_WAIT = "WAIT"              # (Client only) Waiting for initial response from server.
    OPENVPN_STATE_AUTH = "AUTH"              # (Client only) Authenticating with server.
    OPENVPN_STATE_GET_CONFIG = "GET_CONFIG"  # (Client only) Downloading configuration options from server.
    OPENVPN_STATE_ASSIGN_IP = "ASSIGN_IP"    # Assigning IP address to virtual network interface.
    OPENVPN_STATE_ADD_ROUTES = "ADD_ROUTES"  # Adding routes to system.
    OPENVPN_STATE_CONNECTED = "CONNECTED"    # Initialization Sequence Completed.
    OPENVPN_STATE_RECONNECTING = "RECONNECTING"  # A restart has occurred.
    OPENVPN_STATE_EXITING = "EXITING"        # A graceful exit is in progress.
    OPENVPN_STATE_RESOLVE = "RESOLVE"
    OPENVPN_STATE_SLEEP = "SLEEP"
    OPENVPN_STATE_TCP_CONNECT = "TCP_CONNECT"
    OPENVPN_STATE_UDP_CONNECT = "UDP_CONNECT"

    OPENVPN_STATE_DISCONNECTED = "DISCONNECTED"

    _OPENVPN_STATES_CONNECTING = [
        OPENVPN_STATE_CONNECTING,
        OPENVPN_STATE_WAIT,
        OPENVPN_STATE_AUTH,
        OPENVPN_STATE_GET_CONFIG,
        OPENVPN_STATE_ASSIGN_IP,
        OPENVPN_STATE_ADD_ROUTES,
        OPENVPN_STATE_RECONNECTING,
        OPENVPN_STATE_RESOLVE,
        OPENVPN_STATE_SLEEP,
        OPENVPN_STATE_TCP_CONNECT,
        OPENVPN_STATE_UDP_CONNECT
    ]
    _OPENVPN_STATES_CONNECTED = [
        OPENVPN_STATE_CONNECTED
    ]
    _OPENVPN_STATES_DISCONNECTING = [
        OPENVPN_STATE_EXITING
    ]

    _OPENVPN_STATES_DISCONNECTED = [
        OPENVPN_STATE_DISCONNECTED
    ]

    '''
    _OPENVPN_STATES_MESSAGES = {
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_CONNECTING: _("Connecting"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_WAIT: _("Waiting for server response"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_AUTH: _("Authenticating"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_GET_CONFIG: _("Getting configuration"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_ASSIGN_IP: _("Assigning IP address to virtual network interface"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_ADD_ROUTES: _("Adding routes to the system"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_CONNECTED: _("Connection established"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_RECONNECTING: _("Reconnecting"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_EXITING: _("Disconnecting"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_RESOLVE: _("Resolving domain name"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_SLEEP: _("Waiting for daemon process"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_TCP_CONNECT: _("Establishing TCP connection"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_UDP_CONNECT: _("Establishing UDP connection"),
        # TRANSLATOR: OpenVPN state
        OPENVPN_STATE_DISCONNECTED: _("Disconnected")
    }

    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.on_change = Signal()
        self.openvpn_state = self.OPENVPN_STATE_DISCONNECTED
        self.sub_message = None
        self.timestamp = None

    def send_state_changed_signal(self):
        self._logger.debug("openvpn connection state changed")
        self.on_change.send(self)

    def update(self, state, sub_message, timestamp, send_signal):
        self._logger.debug("openvpn state changed: {} ({}) -> {} ({})".format(
            self.openvpn_state, self.sub_message, state, sub_message))
        self.openvpn_state = state
        self.sub_message = sub_message
        self.timestamp = timestamp
        if send_signal:
            self.send_state_changed_signal()

    @property
    def message(self):
        message = self._OPENVPN_STATES_MESSAGES[self.openvpn_state]
        if self.sub_message:
            message = "{} ({})".format(message, self.sub_message)
        return message
    '''
    @property
    def is_disconnecting(self):
        return self.get() in self._OPENVPN_STATES_DISCONNECTING

    @property
    def is_connected(self):
        return self.get() in self._OPENVPN_STATES_CONNECTED

    @property
    def is_connecting(self):
        return self.get() in self._OPENVPN_STATES_CONNECTING

    @property
    def is_disconnected(self):
        return self.get() in self._OPENVPN_STATES_DISCONNECTED

