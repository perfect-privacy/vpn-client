import logging
from datetime import datetime
from threading import Thread, Event
import traceback

from core.libs.web import reporter


class PerpetualTimer(object):
    def __init__(self, callback, interval, last_call_timestamp=None):
        self._logger = logging.getLogger(self.__class__.__name__)

        self._callback = callback
        self._interval = interval
        self.last_call_timestamp = last_call_timestamp

        now = datetime.now().timestamp()
        if not self.last_call_timestamp or self.last_call_timestamp < 0 or self.last_call_timestamp > now:
            self.last_call_timestamp = None

        self._is_running = True

        self._call_now = False

        self._wakeup_event = Event()
        self._cancel_pause_event = Event()
        self._timer_thread = Thread(target=self._timer_run, daemon=True)
        self._timer_thread.start()

    def _timer_run(self):
        while self._is_running:
            self._cancel_pause_event.wait()  # enable/disable

            if not self._is_running:
                break

            while self._is_running and not self._call_now and self._cancel_pause_event.is_set():
                wait_time = min(self._calculate_delay(), 3600)
                if wait_time > 0:
                    waiting_aborted = self._wakeup_event.wait(wait_time)  # False on timeout
                    self._wakeup_event.clear()
                else:
                    break

            if not self._is_running:
                break

            if not self._cancel_pause_event.is_set():  # has been disabled
                continue

            self._call_now = False

            self.last_call_timestamp = datetime.now().timestamp()
            try:
                self._callback()
            except:
                self._logger.error("error executing callback")
                self._logger.debug(traceback.format_exc())
                reporter.report_error(traceback=traceback.format_exc())

    def _calculate_delay(self):
        if self._call_now:
            delay = 0
        else:
            if self.last_call_timestamp:
                now = datetime.now().timestamp()
                delay = self.last_call_timestamp + self._interval - now
            else:
                delay = self._interval

        delay = max(0, delay)
        delay = min(self._interval, delay)
        return delay

    def enable(self):
        if not self._is_running:
            self._logger.debug("enabling cancelled: shutting down...")
            return
        if not self.last_call_timestamp:
            self.last_call_timestamp = datetime.now().timestamp()
        self._cancel_pause_event.set()
        self._wakeup_event.set()

    def disable(self):
        if not self._is_running:
            self._logger.debug("disabling cancelled: shutting down...")
            return
        self._cancel_pause_event.clear()
        self._wakeup_event.set()

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value
        self._wakeup_event.set()

    def call_now(self):
        self._call_now = True
        self._wakeup_event.set()

    def shutdown(self):
        self._logger.debug("shutting down...")
        self._is_running = False
        self._cancel_pause_event.set()
        self._wakeup_event.set()
        try:
            self._timer_thread.join(timeout=20)
        except RuntimeError:
            self._logger.debug("joining failed")
        if self._timer_thread.is_alive():
            self._logger.error("shutting down timer thread failed")
            reporter.report_error(msg="shutting down timer thread failed")
            raise RuntimeError()
        self._logger.debug("shut down finished")
