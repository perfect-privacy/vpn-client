import logging
import time
from threading import Thread, Event
import json
import uuid
import os
from pathlib import Path
import platform
import requests
try:
    from config.config import BRANCH
except:
    BRANCH = "release"
try:
    from config.config import APP_VERSION, BRANCH, APP_BUILD
except:
    APP_VERSION, BRANCH, APP_BUILD = "unknown", "release", "0"

REPORT_URL = "https://www.perfect-privacy.com/api/client.php"
REPORT_FILE = os.path.join(Path.home(),".perfect_privacy.reports")
INSTALL_ID  = os.path.join(Path.home(),".perfect_privacy.instid")


class Reporter():
    def __init__(self):
        self.reports = []
        self.reports_send = 0
        self._logger = logging.getLogger(self.__class__.__name__)
        self.installation_id = "%s" % uuid.uuid4()
        try:
            with open(INSTALL_ID, "r") as f:
                self.installation_id = f.read()
        except:
            try:
                with open(INSTALL_ID, "w") as f:
                    f.write(self.installation_id)
            except:
                pass
        self.from_disk()
        self._enabled = True
        self._wakeup_event = Event()
        self._report_thread = Thread(target=self._report_thread_run, daemon=True)
        self._report_thread.start()
        if len(self.reports) > 0:
            self._wakeup_event.set()

    def report(self, name, data = '', noid = False):
        report = {
            "id":  "" if noid is True else self.installation_id,
            "osversion": " ; ".join(platform.system_alias(platform.system(), platform.release(), "" if noid is True else platform.version())),
            "clientversion": " ; ".join([APP_VERSION, BRANCH, APP_BUILD]),
            "configversion": "",
            "action": name,
            "meta": json.dumps(data)
        }
        if BRANCH != "release":
            self._logger.error(report)
            return
        self.reports.append(report)
        self.to_disk()
        self._wakeup_event.set()

    def to_disk(self):
        try:
            d = json.dumps({
                "reports" : self.reports,
                "reports_send" : self.reports_send
            })
            with open(REPORT_FILE, "w") as f:
                f.write(d)
        except:
            pass

    def from_disk(self):
        try:
            with open(REPORT_FILE, "r") as f:
                d = json.loads(f.read())
                self.reports = d["reports"]
                self.reports_send = d["reports_send"]
        except:
            pass

    def shutdown(self):
        if len(self.reports) > 0:
            self._wakeup_event.set()
            time.sleep(3)
        self._enabled = False
        self._wakeup_event.set()
        self._report_thread.join()

    def _report_thread_run(self):
        while self._enabled:
            self._wakeup_event.wait()
            self._wakeup_event.clear()
            if not self._enabled:
                break
            while len(self.reports) > 0 and self._enabled is True:
                try:
                    requests.post(url=REPORT_URL, data=self.reports[0], timeout=5)
                    self._logger.error("crashreport send: %s" % self.reports[0])
                    self.reports_send += 1
                    del self.reports[0]
                    self.to_disk()
                except Exception as e:
                    print(e)
                    if self._enabled is True:
                        time.sleep(10)


ReporterInstance = Reporter()