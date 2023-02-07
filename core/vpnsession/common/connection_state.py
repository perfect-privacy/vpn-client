from core.libs.generic_state import GenericState

class VpnConnectionState(GenericState):
    IDLE = "idle"
    CONNECTING  = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"
    _DEFAULT = IDLE