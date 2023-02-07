from config.config import PLATFORM
from config.constants import PLATFORMS

if PLATFORM == PLATFORMS.windows:
    from .connection_ipsec_windows import IpsecConnection
