import ipaddress
import logging
import threading

from pyhtmlgui import Observable

from config.config import PLATFORM
from config.constants import PLATFORMS

if PLATFORM == PLATFORMS.windows:
    from core.routing.routes import RoutesV4Windows as RoutesV4
    from core.routing.routes import RoutesV6Windows as RoutesV6
if PLATFORM == PLATFORMS.macos:
    from core.routing.routes import RoutesV4Macos as RoutesV4
    from core.routing.routes import RoutesV6Macos as RoutesV6


class Routing(Observable):
    def __init__(self, core):
        super().__init__()
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)

        self.routes_ipv4 = RoutesV4(core)
        self.routes_ipv6 = RoutesV6(core)
        self._wakeup_event = threading.Event()
        if self.core is not None:
            self.__worker_threadv4 = threading.Thread(target=self._worker_threadV4, daemon=True)
            self.__worker_threadv4.start()
            self.__worker_threadv6 = threading.Thread(target=self._worker_threadV6, daemon=True)
            self.__worker_threadv6.start()

    def update_async(self):
        self._wakeup_event.set()

    def shutdown(self):
        self._is_running = False
        self._wakeup_event.set()
        self.__worker_threadv4.join()
        self.__worker_threadv6.join()

    def _worker_threadV4(self):
        while self._is_running is True:
            self.routes_ipv4.update()
            self._wakeup_event.wait()
            self._wakeup_event.clear()

    def _worker_threadV6(self):
        while self._is_running is True:
            self.routes_ipv6.update()
            self._wakeup_event.wait()
            self._wakeup_event.clear()


