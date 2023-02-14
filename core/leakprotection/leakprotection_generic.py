import logging
from config.constants import PROTECTION_SCOPES
import threading
from pyhtmlgui import  Observable
from core.libs.generic_state import GenericState


class LeakProtectionState(GenericState):
    ENABLED    = "ENABLED"
    ENABLEING  = "ENABLEING"
    DISABLED   = "DISABLED"
    DISABLING  = "DISABLING"
    _DEFAULT = DISABLED

class LeakProtection_Generic(Observable):
    def __init__(self, core=None):
        super().__init__()
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)
        self._whitelisted_server = None
        self._highest_hop_ipv4_local_ip = None
        self._highest_hop_ipv6_local_ip = None
        self._is_running = True
        self.state = LeakProtectionState()
        self._lock = threading.Lock()
        self._wakeup_event = threading.Event()
        self.__worker_thread = threading.Thread(target=self._worker_thread, daemon=True)
        self.__worker_thread.start()

    def whitelist_server(self, public_ip_address, port, protocol):
        self._whitelisted_server = [public_ip_address, port, protocol]
        self.update_async()

    def set_highest_hop_local_ip(self, ipv4, ipv6):
        self._highest_hop_ipv4_local_ip = ipv4
        self._highest_hop_ipv6_local_ip = ipv6
        self.update_async()

    def update(self):
        self._update()

    def update_async(self):
        self._wakeup_event.set()

    def shutdown(self):
        self._is_running = False
        self._wakeup_event.set()
        self.__worker_thread.join()

    def _worker_thread(self):
        while self._is_running is True:
            self._update()
            self._wakeup_event.wait()
            self._wakeup_event.clear()

    def _update(self):
        try:
            self._lock.acquire()
            self._logger.debug("updating leakprotection state")
            scope = self.core.settings.leakprotection.leakprotection_scope.get()
            if scope == PROTECTION_SCOPES.disabled:
                self.__disable()
            elif scope == PROTECTION_SCOPES.program:
                if self.core.session._should_be_connected.get() is True or self.core.frontend_active is True:
                    self.__enable()
                else:
                    self.__disable()
            elif scope == PROTECTION_SCOPES.tunnel:
                if self.core.session._should_be_connected.get() is True:
                    self.__enable()
                else:
                    self.__disable()
            elif scope == PROTECTION_SCOPES.permanent:
                self.__enable()
            else:
                self._logger.error("invalid traffic leak protection setting")
        finally:
            self._lock.release()
        self.notify_observers()

    def __disable(self):
        self.state.set(LeakProtectionState.DISABLING)
        self.notify_observers()
        self._disable()
        self.state.set(LeakProtectionState.DISABLED)
        self.notify_observers()

    def __enable(self):
        self.state.set(LeakProtectionState.ENABLEING)
        self.notify_observers()
        self._enable()
        self.state.set(LeakProtectionState.ENABLED)
        self.notify_observers()


    def _enable(self):
        raise NotImplementedError()

    def _disable(self):
        raise NotImplementedError()


'''
class LeakProtection_Generic(object):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._enabled = False
        self._primary_interface = ""
        self._hops = []
        self.number_of_hops_in_current_cascading = 0
        self._is_blocking_all_internet_traffic = False
        self.on_change = Signal()
        self._enable_disable_lock = RLock()

    def _log_current_config(self):
        self._logger.debug("current config: enabled: {}, primary interface: {}, hops: {}".format(
            self._enabled, self.primary_interface, self._hops))

    @property
    def primary_interface(self):
        return self._primary_interface

    @primary_interface.setter
    def primary_interface(self, value):
        self._primary_interface = value
        self._log_current_config()

    @property
    def is_blocking_all_internet_traffic(self):
        return self._is_blocking_all_internet_traffic

    def add_hop(self, public_ip_address, port, transport_protocol, interface=None):
        self._hops.append(Hop(len(self._hops) + 1, public_ip_address, port, transport_protocol, interface))
        self._log_current_config()

    def modify_hop(self, hopid, interface):
        self._logger.debug("modify hop {} to interface {}".format(hopid, interface))
        if hopid-1 < 0 or hopid-1 >= len(self._hops):
            self._logger.error("unknown hopid {}".format(hopid))
            reporter.report_error(msg="unknown hopid {}".format(hopid))
            return
        mod_hop = self._hops[hopid-1]
        self._hops[hopid-1] = Hop(mod_hop.hop_id, mod_hop.public_ip_address, mod_hop.port,
                                  mod_hop.transport_protocol, interface)
        self._log_current_config()

    def clear_hops(self):
        self.number_of_hops_in_current_cascading = 0
        self._hops.clear()
        self._log_current_config()

    def enable(self):
        with self._enable_disable_lock:
            self._logger.debug("enabling")
            if self._enabled:
                self._logger.debug("already enabled")
                return
            self._enabled = True
            self._update_firewall()

    def apply_changes(self):
        with self._enable_disable_lock:
            self._logger.debug("apply changes")
            self._update_firewall()

    def disable(self):
        with self._enable_disable_lock:
            self._logger.debug("disabling")
            if not self._enabled:
                self._logger.debug("already disabled")
                return
            self._disable_firewall()
            self._enabled = False

    def _update_firewall(self):
        return
        raise NotImplementedError()

    def _disable_firewall(self):
        return
        raise NotImplementedError()
'''