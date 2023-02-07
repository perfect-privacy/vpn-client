from core.libs.generic_state import GenericState

class StealthState(GenericState):
    IDLE       = "IDLE"
    CONNECTING = "CONNECTING"
    CONNECTED  = "CONNECTED"
    _DEFAULT = IDLE
