import logging
import time
from threading import Thread, Event
import json
import uuid
import os
from pathlib import Path
import platform
import requests
from pyhtmlgui import Observable

try:
    from config.config import BRANCH
except:
    BRANCH = "release"
try:
    from config.config import APP_VERSION, BRANCH, APP_BUILD
except:
    APP_VERSION, BRANCH, APP_BUILD = "unknown", "release", "0"
try:
    from config.files import APP_DIR
except:
    APP_DIR = None


REPORT_URL = "https://www.perfect-privacy.com/api/client.php"
REPORT_FILE = os.path.join(Path.home(),".perfect_privacy.reports")


class Reporter(Observable):
    def __init__(self):
        super().__init__()
        self.reports = []
        self.reports_send = 0
        self.latest_reports = []
        self._logger = logging.getLogger(self.__class__.__name__)
        self.installation_id = ""
        self.new_id = False
        self.send_crashreports = None
        self.last_report_send = 0

        tmp_dir = "/tmp" if platform.system() != "Windows" else "C:\\Users\\Public"
        if APP_DIR is not None and os.path.exists(os.path.join(APP_DIR, "var", ".perfect_privacy.instid")):
            self.installation_id = open(os.path.join(APP_DIR, "var", ".perfect_privacy.instid"), "r").read().strip()
            if os.path.exists(os.path.join(tmp_dir, ".perfect_privacy.instid")):
                try:
                    os.remove(os.path.join(tmp_dir, ".perfect_privacy.instid"))
                except: pass
        if os.path.exists(os.path.join(Path.home(), ".perfect_privacy.instid")) and self.installation_id == "":
            self.installation_id = open(os.path.join(Path.home(), ".perfect_privacy.instid"), "r").read().strip()
        if os.path.exists(os.path.join(tmp_dir, ".perfect_privacy.instid"))  and self.installation_id == "":
            self.installation_id = open(os.path.join(tmp_dir, ".perfect_privacy.instid"), "r").read().strip()
        if self.installation_id == "":
            self.new_id = True
            self.installation_id = "%s" % uuid.uuid4()

        if not os.path.exists(os.path.join(Path.home(), ".perfect_privacy.instid")) or self.new_id is True:
            open(os.path.join(Path.home(), ".perfect_privacy.instid"), "w").write(self.installation_id)
        if APP_DIR is not None and (not os.path.exists(os.path.join(APP_DIR, "var", ".perfect_privacy.instid")) or self.new_id is True):
            try:
                open(os.path.join(APP_DIR, "var", ".perfect_privacy.instid"), "w").write(self.installation_id)
            except:
                if not os.path.exists(os.path.join(tmp_dir, ".perfect_privacy.instid")) or self.new_id is True:
                    open(os.path.join(tmp_dir, ".perfect_privacy.instid"), "w").write(self.installation_id)

        self.from_disk()
        self._enabled = True
        self._wakeup_event = Event()
        self._report_thread = Thread(target=self._report_thread_run, daemon=True)
        self._report_thread.start()
        if len(self.reports) > 0:
            self._wakeup_event.set()

    def clear(self):
        self.reports_send = 0
        self.latest_reports = []
        self.to_disk()
        self.notify_observers()


    def report(self, name, data = '', noid = False):
        try:
            data = json.dumps(data)
        except Exception as e:
            data = "failed to encode report data: %s" % e
        report = {
            "id":  "" if noid is True else self.installation_id,
            "osversion": " ; ".join(platform.system_alias(platform.system(), platform.release(), "" if noid is True else platform.version())),
            "clientversion": " ; ".join([APP_VERSION, BRANCH, APP_BUILD]),
            "configversion": "",
            "action": name,
            "meta": data
        }
        self._logger.error(report)

        if self.send_crashreports is not None and self.send_crashreports.get() == False:
            return
        if (self.reports_send > 5 or len(self.reports) > 5) and self.last_report_send + 3600 < time.time()  and self.last_report_send < time.time() - 20:
            # always send first 5 reports, send max 1 report per hour, burst reports within 20 seconds
            return

        self.last_report_send = time.time()
        self.reports.append(report)
        self.to_disk()
        self._wakeup_event.set()

    def report_stats(self, data):
        try:
            data = json.dumps(data)
        except Exception as e:
            data = "stats_failed_to_encode:%s" % e
        report = {
            "id":  "",
            "osversion": " ; ".join(platform.system_alias(platform.system(), platform.release(), "")),
            "clientversion": " ; ".join([APP_VERSION, BRANCH, APP_BUILD]),
            "configversion": "",
            "action": "usage_stats",
            "meta": data
        }
        self.reports.append(report)
        self.to_disk()
        self._wakeup_event.set()

    def to_disk(self):
        try:
            d = json.dumps({
                "reports" : self.reports,
                "reports_send" : self.reports_send,
                "last_report_send" : self.last_report_send,
                "latest_reports" : self.latest_reports
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
                self.last_report_send = d["last_report_send"]
                self.latest_reports = d["latest_reports"]
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
            if self.send_crashreports is not None and self.send_crashreports.get() == False:
                return
            if not self._enabled:
                break
            while len(self.reports) > 0 and self._enabled is True:
                try:
                    requests.post(url=REPORT_URL, data=self.reports[0], timeout=5)
                    self._logger.error("crashreport send: %s" % self.reports[0])
                    self.latest_reports.append(self.reports[0])
                    self.latest_reports = self.latest_reports[-30:]
                    self.reports_send += 1
                    del self.reports[0]
                    self.to_disk()
                    self.notify_observers()
                except Exception as e:
                    print(e)
                    if self._enabled is True:
                        time.sleep(10)


ReporterInstance = Reporter()
