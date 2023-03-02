import logging
import traceback

from config.constants import PROTECTION_SCOPES
import threading
from pyhtmlgui import  Observable
from core.libs.generic_state import GenericState
from core.libs.web.reporter import ReporterInstance


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
        self._is_running = True
        self.state = LeakProtectionState()
        self._lock = threading.Lock()
        self._wakeup_event = threading.Event()
        if self.core is not None:
            self.__worker_thread = threading.Thread(target=self._worker_thread, daemon=True)
            self.__worker_thread.start()

    def whitelist_server(self, public_ip_address, port, protocol):
        self._whitelisted_server = [public_ip_address, port, protocol]
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
            self._logger.debug("Checking leakprotection state")
            scope = self.core.settings.leakprotection.leakprotection_scope.get()
            if scope == PROTECTION_SCOPES.disabled:
                self.__disable()
            elif scope == PROTECTION_SCOPES.program:
                if self.core.session._should_be_connected.get() is True or self.core.frontend_active is True or self.core.settings.startup.enable_background_mode.get() is True:
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
        try:
            self._disable()
        except Exception as e:
            ReporterInstance.report("leakprotection_disabled_failed", traceback.format_exc())
        self.state.set(LeakProtectionState.DISABLED)
        self.notify_observers()

    def __enable(self):
        self.state.set(LeakProtectionState.ENABLEING)
        self.notify_observers()
        try:
            self._enable()
        except Exception as e:
            ReporterInstance.report("leakprotection_enable_failed", traceback.format_exc())
        self.state.set(LeakProtectionState.ENABLED)
        self.notify_observers()


    def _enable(self):
        raise NotImplementedError()

    def _disable(self):
        raise NotImplementedError()

