import logging
import time
from datetime import datetime

from .ipcheck_result import IPCheckerResult
from .ipchecker_tor import TorIPChecker
from .ipchecker_pp import PerfectPrivacyIPChecker
import math
from core.libs.perpetual_timer import PerpetualTimer
from pyhtmlgui import Observable
from core.libs.permanent_property import PermanentProperty


class IPCheckerState():
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"

class IpCheck(Observable):

    def __init__(self, core, min_check_interval_seconds=10 * 60, max_check_interval_seconds=60 * 60,   err_check_interval_seconds=10 * 60):
        self.core = core
        super(IpCheck, self).__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

        self.last_successful_check = PermanentProperty(self.__class__.__name__ + ".last_successful_check", 0)
        self.last_failed_check = PermanentProperty(self.__class__.__name__ + ".last_failed_check", 0)
        self._min_check_interval_seconds = min_check_interval_seconds
        self._max_check_interval_seconds = max_check_interval_seconds
        self._err_check_interval_seconds = err_check_interval_seconds
        self.next_check = None
        self._check_timer = PerpetualTimer(self._run_check, self._min_check_interval_seconds if self.last_successful_check.get() else self._err_check_interval_seconds, self.last_successful_check.get())
        self.state = IPCheckerState.IDLE

        self._ip_checker = PerfectPrivacyIPChecker(fallback_checker=TorIPChecker())
        self.result4 = IPCheckerResult("Ipv4")
        self.result6 = IPCheckerResult("Ipv6")
        self.result4.attach_observer(self.on_result_updated)
        self.result6.attach_observer(self.on_result_updated)

    def on_result_updated(self):
        self.notify_observers()

    @property
    def vpn_connected(self):
        """
        :return: whether the VPN is connected (calculated from v4 and v6 check)
        :rtype: bool
        """
        """
        4       6       =
        None    None    None
        False   None    False
        True    None    True
        None    False   False
        False   False   False
        True    False   False
        None    True    True
        False   True    False
        True    True    True
        """
        if self.result4.vpn_connected is False or self.result6.vpn_connected is False:
            # comparison with False!
            return False
        if self.result4.vpn_connected is True or self.result6.vpn_connected is True:
            return True
        return False

    @property
    def leak_detected(self):
        return (self.result4.vpn_connected is False and self.result6.vpn_connected is True ) or \
               (self.result4.vpn_connected is True  and self.result6.vpn_connected is False)

    def _run_check(self):
        for i in range(15):
            if self.core.allow_webrequests() is True:
                break
            time.sleep(1)
        if self.core.allow_webrequests() is False:
            self.clear()
            return

        self.state = IPCheckerState.ACTIVE
        self.notify_observers()
        now = datetime.now().timestamp()
        try:
            self._ip_checker.check( expected_ipv4_addresses=self.core.vpnGroupPlanet.get_ipv4s(), expected_ipv6_addresses=self.core.vpnGroupPlanet.get_ipv6s(), result4=self.result4, result6=self.result6)
            self.last_successful_check.set(math.floor(now))
            self._check_timer.interval = int(self._check_timer.interval * 1.1)
            if self._check_timer.interval > self._max_check_interval_seconds:
                self._check_timer.interval = self._max_check_interval_seconds
            return True
        except:
            self.last_failed_check.set(math.floor(now))
            self._check_timer.interval = self._err_check_interval_seconds
            return False
        finally:
            self.state = IPCheckerState.IDLE
            self.notify_observers()


    def enable(self):
        if self.state != IPCheckerState.IDLE:
            return
        self._check_timer.enable()
        self.next_check = math.floor(self._check_timer.last_call_timestamp + self._check_timer.interval)
        self.notify_observers()

    def disable(self):
        self._check_timer.disable()
        self.next_check = None
        self.notify_observers()

    def check_now(self):
        self.enable()
        self._check_timer.interval = self._min_check_interval_seconds
        self._check_timer.call_now()

    def clear(self):
        changed = self.result4.clear()
        changed = self.result6.clear() or changed
        return changed
