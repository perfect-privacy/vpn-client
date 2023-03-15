from config.config import PLATFORM
from config.constants import PLATFORMS

if PLATFORM == PLATFORMS.windows:
    from core.routing.routing import RoutingWindows as Routing
if PLATFORM == PLATFORMS.macos:
    from core.routing.routing import RoutingMacos as Routing

