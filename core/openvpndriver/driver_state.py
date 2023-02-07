from core.libs.generic_state import GenericState


class OpenVpnDriverState(GenericState):
    IDLE         = "IDLE"
    WORKING      = "WORKING"
    _DEFAULT = IDLE