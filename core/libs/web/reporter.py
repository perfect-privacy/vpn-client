import logging
import traceback
from collections import deque
from threading import Thread, Event, Timer
import json
import os
from datetime import datetime

import requests.exceptions as request_exceptions

from config.config import BRANCH
from config.constants import BRANCHES
from .webrequest import WebRequest

REPORT_TYPE_ERROR = "error"
REPORT_TYPE_CRASH = "crash"
REPORT_TYPE_INSTALL = "install"
REPORT_TYPE_UNINSTALL = "uninstall"
REPORT_TYPE_UPDATE = "update"


class Reporter(object):
    """
    :type _system_information: daemon.os_specific.macos_system_information.MacOsSystemInformation
    """

    REPORT_URL = "https://www.perfect-privacy.com/api/client.php"

    def __init__(self, installation_id, client_version, config_version, report_file):
        self._logger = logging.getLogger(self.__class__.__name__)
        if BRANCH != BRANCHES.dev:
            self._logger.propagate = False

        self._reports = deque()
        # self._system_information = system_information
        self._installation_id = installation_id
        self._client_version = client_version
        self._config_version = config_version
        self._report_file = report_file
        self._retry_timer = None

        self._read_reports_from_disk()

        self._is_running = True
        self._cancel_pause_event = Event()
        self._wakeup_event = Event()
        self._report_thread = Thread(target=self._report_thread_run, daemon=True)
        self._report_thread.start()

    def enable(self):
        self._logger.debug("enabling")
        self._cancel_pause_event.set()
        self._wakeup_event.set()

    def disable(self):
        self._logger.debug("disabling")
        self._cancel_pause_event.clear()
        self._wakeup_event.set()

    def _report_thread_run(self):
        while self._is_running:
            self._logger.debug("waiting...")
            self._cancel_pause_event.wait()
            self._wakeup_event.wait()
            self._wakeup_event.clear()

            if not self._is_running or not self._cancel_pause_event.is_set():
                continue

            report_to_send = None
            try:
                report_to_send = self._reports.pop()
                self._send_report(report_to_send)
                if len(self._reports) > 0:
                    self._wakeup_event.set()
            except IndexError:  # no reports in list
                continue
            except request_exceptions.RequestException:
                self._logger.debug("reporting failed, retry in 10 seconds")
                if report_to_send:
                    self._reports.append(report_to_send)
                if self._retry_timer:
                    self._retry_timer.cancel()
                self._retry_timer = Timer(10, self._wakeup_event.set)
                self._retry_timer.start()
                continue
            except:
                self._logger.debug("reporting failed: unexpected exception")
                self._logger.debug(traceback.format_exc())
                if report_to_send:
                    self._reports.append(report_to_send)
                continue

    def _send_report(self, report):
        self._logger.debug("reporting: {}".format(report))
        if BRANCH == BRANCHES.dev:
            self._logger.info("report cancelled: DEV system")
            return
        r = WebRequest().post(url=self.REPORT_URL, data=report)
        r.raise_for_status()
        return r

    def add_report(self, report_type, meta_dict=None):
        if not meta_dict:
            meta_dict = {}
        meta_dict["timestamp"] = round(datetime.now().timestamp(), 3)
        meta_dict["openvpn_version"] = 23 # TODO self._system_information.openvpn_version_number
        meta_dict["openssh_version"] = 23 # TODO self._system_information.openssh_version_number
        report = {
            "id": self._installation_id,
            "osversion": "macOS {}".format(23), # TODO self._system_information.system_version_number),
            "clientversion": self._client_version,
            "configversion": self._config_version,
            "action": report_type,
            "meta": json.dumps(meta_dict)
        }
        self._logger.debug("added report: {}".format(report))
        self._reports.appendleft(report)
        self._wakeup_event.set()

    def _read_reports_from_disk(self):
        return # FIXME
        filed_reports = []
        try:
            if os.path.exists(self._report_file):
                with open(self._report_file, "r") as f:
                    filed_reports = json.load(f)
                os.remove(self._report_file)
        except:
            self._logger.debug("an error occurred while reading the reports from disk")
            self._logger.debug(traceback.format_exc())
        for report in filed_reports:
            try:
                new_report = {
                    "id": report["id"],
                    "osversion": report["osversion"],
                    "clientversion": report["clientversion"],
                    "configversion": report["configversion"],
                    "action": report["action"],
                    "meta": report["meta"]
                }
                self._reports.append(new_report)
            except:
                self._logger.debug("can not restore invalid report")

    def _write_reports_to_disk(self):
        if len(self._reports) > 0:
            try:
                with open(self._report_file, "w") as f:
                    json.dump(list(self._reports), f)
            except:
                self._logger.debug("an error occurred while writing the reports to disk")
                self._logger.debug(traceback.format_exc())

    def shutdown(self):
        self._is_running = False
        try:
            if self._retry_timer:
                self._retry_timer.cancel()
                self._retry_timer.join()
        except:
            pass
        self._cancel_pause_event.set()
        self._wakeup_event.set()
        self._report_thread.join()
        self._write_reports_to_disk()


_reporter = None


def init(installation_id, client_version, config_version, report_file):
    global _reporter
    _reporter = Reporter(
        #system_information=system_information,
        installation_id=installation_id,
        client_version=client_version,
        config_version=config_version,
        report_file=report_file)


def report_error(**kwargs):
    _report(REPORT_TYPE_ERROR, kwargs)


def report_crash(**kwargs):
    _report(REPORT_TYPE_CRASH, kwargs)


def report_install(**kwargs):
    _report(REPORT_TYPE_INSTALL, kwargs)


def report_uninstall(**kwargs):
    _report(REPORT_TYPE_UNINSTALL, kwargs)


def report_update(**kwargs):
    _report(REPORT_TYPE_UPDATE, kwargs)


def _report(report_type, meta_dict):
    global _reporter
    if _reporter:
        _reporter.add_report(report_type, meta_dict)
    else:
        print("ERROR: ignored report (reporter not initialized)")


def enable():
    global _reporter
    if _reporter:
        _reporter.enable()
    else:
        print("ERROR: reporter not initialized")


def disable():
    global _reporter
    if _reporter:
        _reporter.disable()
    else:
        print("ERROR: reporter not initialized")


def shutdown():
    global _reporter
    if _reporter:
        _reporter.shutdown()
