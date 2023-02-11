# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2014-2015 Perfect Privacy <support@perfect-privacy.com>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import logging
import math
import traceback
import json
from datetime import datetime
from core.libs.perpetual_timer import PerpetualTimer
from core.libs.permanent_property import PermanentProperty
from pyhtmlgui import Observable
from core.libs.web import WebRequest
from config.urls import TRAFFIC_JSON_URL


class TrafficDownloadState():
    IDLE = "IDLE"
    DOWNLOADING = "DOWNLOADING"

class TrafficDownload(Observable):

    def __init__(self, core, min_check_interval_seconds=20,
                 max_check_interval_seconds=60*60,
                 err_check_interval_seconds=10*60):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.core = core
        super(TrafficDownload, self).__init__()

        self.state = TrafficDownloadState.IDLE

        self.last_successful_check = PermanentProperty(self.__class__.__name__ + ".last_successful_check", 0)
        self.last_failed_check = PermanentProperty(self.__class__.__name__ + ".last_failed_check", 0)
        self._min_check_interval_seconds = min_check_interval_seconds
        self._max_check_interval_seconds = max_check_interval_seconds
        self._err_check_interval_seconds = err_check_interval_seconds

        self._timer = PerpetualTimer(
            self._download,
            self._max_check_interval_seconds if self.last_successful_check.get() else self._err_check_interval_seconds,
            self.last_successful_check.get())

        self.next_check = None

        self._on_data_updated = Observable()


    def _download(self):

        if self.state != TrafficDownloadState.IDLE:
            self._logger.debug("can not start traffic download: not idle")
            return
        if  self.core.allow_webrequests() is False:
            return

        now = datetime.now().timestamp()

        self.state = TrafficDownloadState.DOWNLOADING
        self.notify_observers()

        try:
            r = WebRequest().get(TRAFFIC_JSON_URL)
            r.raise_for_status()
            data = json.loads(r.content)
            self._on_data_updated.notify_observers(data=data)
            self.notify_observers()
            self._timer.last_call_timestamp = now
            self._timer.interval = int(self._timer.interval * 1.1)
            if self._timer.interval > self._max_check_interval_seconds:
                self._timer.interval = self._max_check_interval_seconds
            self.last_successful_check.set( math.floor(now))
        except Exception as e:
            self.last_failed_check.set(math.floor(now))
            self._timer.interval = self._err_check_interval_seconds
        self.next_check = math.floor(self._timer.last_call_timestamp + self._timer.interval)
        self.state = TrafficDownloadState.IDLE
        self.notify_observers()


    def enable(self):
        self._logger.debug("enabling")
        self._timer.interval = self._min_check_interval_seconds
        self._timer.enable()
        self.next_check = math.floor(self._timer.last_call_timestamp + self._timer.interval)
        self.notify_observers()

    def disable(self):
        self._logger.debug("disabling")
        self._timer.disable()
        self.next_check = None
        self.notify_observers()

    def check_now(self):
        self.enable()
        self._timer.call_now()
