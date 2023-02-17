import logging
from threading import RLock

from pyhtmlgui import Observable


class IPCheckerResult(Observable):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.vpn_connected = None
        self.public_ip = None
        self.public_rdns = None
        self.public_city = None
        self.public_country = None
        self._lock = RLock()

    def update(self, vpn_connected=None, public_ip=None, public_rdns=None, public_city=None, public_country=None):
        with self._lock:
            prev_vpn_connected = self.vpn_connected
            prev_public_ip = self.public_ip
            prev_public_rdns = self.public_rdns
            prev_public_city = self.public_city
            prev_public_country = self.public_country

            self.vpn_connected = vpn_connected
            self.public_ip = public_ip
            self.public_rdns = public_rdns
            self.public_city = public_city
            self.public_country = public_country

            if self.vpn_connected != prev_vpn_connected \
                    or self.public_ip != prev_public_ip \
                    or self.public_rdns != prev_public_rdns \
                    or self.public_city != prev_public_city \
                    or self.public_country != prev_public_country:
                self._logger.debug("IP Check changed: {}".format(repr(self)))
                self.notify_observers()
                return True

            return False

    def clear(self):
        return self.update()

    def __eq__(self, other):
        if other is None:
            return False

        return other.vpn_connected == self.vpn_connected \
            and other.public_ip == self.public_ip \
            and other.public_rdns == self.public_rdns \
            and other.public_city == self.public_city \
            and other.public_country == self.public_country

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "IPCheckerResult(connected={vpn_connected})".format(vpn_connected=self.vpn_connected,)
