import logging
import threading
from threading import RLock, Thread, Event
from datetime import datetime, timedelta
import json
import requests
from collections import namedtuple
import queue

from pyhtmlgui import ObservableDict, Observable, ObservableList

from core.libs.web.webrequest import WebRequest

from .trackstop import TrackStop
from .customportforwardings import CustomPortForwardings
from .remote_property import RemoteProperty
import time

from ..libs.permanent_property import PermanentProperty


class UserAPIError(Exception):
    pass


PortForwarding = namedtuple("PortForwarding", "pf_id, server_group_name, src_port, dest_port, valid_until")



class RequestQueue():
    def __init__(self):
        self.requests = []
        self._lock = threading.Lock()
        self._wakeup_event = threading.Event()
        self.is_active = True

    def close(self):
        self.is_active = False
        self._wakeup_event.set()

    def get(self, timeout=None):
        self._wakeup_event.wait(timeout)
        self._wakeup_event.clear()
        if self.is_active is False:
            return None
        self._lock.acquire()
        try:
            r = {}
            for request in self.requests[:]:
                for key in [k for k in request.keys()]:
                    if key not in r:
                        r[key] = request[key]
                        del request[key]
                    else:
                        break
                if len(request.keys()) == 0:
                    self.requests.remove(request)
            if len(self.requests) > 0:
                self._wakeup_event.set()
        finally:
            self._lock.release()
        return r

    def cancel(self, key_value_dict):
        self._lock.acquire()
        try:
            for key in key_value_dict:
                exiting_requests = [r for r in self.requests if key in r]
                for exiting_request in exiting_requests:
                    if exiting_request[key] == key_value_dict[key]:
                        self.requests.remove(exiting_request)
        finally:
            self._lock.release()
        self._wakeup_event.set()

    def put(self, key_value_dict):
        self._lock.acquire()
        try:
            self.requests.append(key_value_dict)
        finally:
            self._lock.release()
        self._wakeup_event.set()

    def update(self, key_value_dict):
        self._lock.acquire()
        try:
            for key in key_value_dict:
                exiting_requests = [r for r in self.requests if key in r]
                if len(exiting_requests) > 0:
                    for exiting_request in exiting_requests:
                        exiting_request[key] = key_value_dict[key]
                else:
                    self.requests.append({key: key_value_dict[key]})
        finally:
            self._lock.release()
        self._wakeup_event.set()


class UserAPI(Observable):

    def __init__(self, core):
        super().__init__()
        self.core = core
        self._logger = logging.getLogger(self.__class__.__name__)

        self.credentials_valid = PermanentProperty(self.__class__.__name__ + ".credentials_valid", None)
        self.account_expired = None
        self.account_disabled = None

        self.base_url = "https://www.perfect-privacy.com/api/user"
        self.last_update = None

        self._server_groups = ObservableList()
        self._server_groups_last_checked = 0

        self.request_queue = RequestQueue()
        self.trackstop = TrackStop(self.request_queue)
        self.customPortForwardings = CustomPortForwardings(self.request_queue)
        self.valid_until   = RemoteProperty("validUntil", self.request_queue,readonly=True,)
        self.email_address = RemoteProperty("emailAddress", self.request_queue,readonly=True)

        self.random_exit_ip = RemoteProperty("randomExit", self.request_queue)
        self.neuro_routing  = RemoteProperty("neuroRouting", self.request_queue)
        self.default_port_forwarding = RemoteProperty("defaultPortForwarding", self.request_queue)

        self.auto_renew_port_forwarding    = RemoteProperty("autorenew_pf", self.request_queue)
        self.email_port_forwarding_updates = RemoteProperty("emailPortForwarding", self.request_queue)
        self.gpg_mail_only = RemoteProperty("pgpOnly", self.request_queue)

        self._worker_thread_running = True
        self._worker_thread = Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

        self.unvalidated_username = ""
        self.unvalidated_password = ""

    def new_credentials(self, username, password):
        self.unvalidated_username = username
        self.unvalidated_password = password
        self.request_update()

    def shutdown(self):
        self.request_queue.close()
        self._worker_thread_running = False
        self._worker_thread.join(timeout=10)
        if self._worker_thread.is_alive():
            self._logger.error("Unable to shut down worker thread")

    def request_update(self):
        self.request_queue.put({})

    def _worker(self):
        while self._worker_thread_running:
            while self.core.allow_webrequests() is False and self._worker_thread_running is True:
                time.sleep(2)

            request = self.request_queue.get()
            if request is None:
                break
            for key,item in request.items():
                if item is False: request[key] = 0
                if item is True: request[key] = 1
            try:
                #self._logger.debug("Requesting from API: %s" % request)
                payload, response = self._request_api(request)
                self._handle_api_response(payload, response)
            except UserAPIError as e:
                pass
            except Exception as e:
                self._logger.debug("Request failed: %s" % e )

    def _request_api(self, payload):
        username = self.unvalidated_username if self.unvalidated_username != "" else self.core.settings.account.username.get()
        password = self.unvalidated_password if self.unvalidated_password != "" else self.core.settings.account.password.get()

        if username is None or username == "" or password is None or password == "":
            self._logger.debug("Credentials not set. ")
            self.credentials_valid.set(None)
            raise UserAPIError()

        if time.time() - self._server_groups_last_checked > 3600:
            payload["getServerGroups"] = ""

        payload["username"] = username
        payload["password"] = password

        try:
            # there may be keys that can be used multiple times (like setPortForwarding[])
            payload_tuples = []
            for key, val in payload.items():
                if type(val) is list:
                    for item in val:
                        payload_tuples.append((key, item))
                else:
                    payload_tuples.append((key, val))

            response = WebRequest().post(url=self.base_url, data=payload_tuples)
        except requests.exceptions.ConnectionError:
            self._logger.error("network problem")
            raise UserAPIError()
        except requests.exceptions.HTTPError:
            self._logger.error("invalid HTTP response")
            raise UserAPIError()
        except requests.exceptions.Timeout:
            self._logger.error("request timeout")
            raise UserAPIError()
        except requests.exceptions.TooManyRedirects:
            self._logger.error("too many redirects")
            raise UserAPIError()
        except requests.exceptions.RequestException:
            self._logger.error("undefined network error")
            raise UserAPIError()

        if response.status_code != 200:
            self._logger.error("invalid status code: %s", response.status_code)
            raise UserAPIError()

        try:
            response_dict = json.loads(response.content.decode())
        except:
            self._logger.error("invalid response: API didn't return valid JSON")

            raise UserAPIError()

        return payload, response_dict

    def _handle_api_response(self, request, response):
        self._response_check_error(response)
        self._response_get_server_groups(request, response)
        self._actual_values = response

        all_requested = False
        if len(request.keys()) == 2: # only username and password send
            all_requested = True

        if "customPorts" in response and ("setPortForwarding" in request or "deletePortForwarding" in request or all_requested is True):
            self.customPortForwardings.update(response["customPorts"])

        if "trackstop" in response:
            if "blockkids" in request or all_requested is True:
                self.trackstop.block_kids.update(response["trackstop"]["kids"])
            if "blockads" in request or all_requested is True:
                self.trackstop.block_social.update(response["trackstop"]["ads"])
            if "blockfraud" in request or all_requested is True:
                self.trackstop.block_fraud.update(response["trackstop"]["fraud"])
            if "blockfakenews" in request or all_requested is True:
                self.trackstop.block_fakenews.update(response["trackstop"]["fakenews"])
            if "blockfacebook" in request or all_requested is True:
                self.trackstop.block_facebook.update(response["trackstop"]["facebook"])
            if "blockgoogle" in request or all_requested is True:
                self.trackstop.block_google.update(response["trackstop"]["google"])
            if "blocksocial" in request or all_requested is True:
                self.trackstop.block_social.update(response["trackstop"]["social"])

        if "validUntil" in response:
            self.valid_until.update(response["validUntil"])
        if "emailAddress" in response:
            self.email_address.update(response["emailAddress"])

        if "randomExit" in response and ("randomExit" in request or all_requested is True):
            self.random_exit_ip.update(response["randomExit"])
        if "neuroRouting" in response and ("neuroRouting" in request or all_requested is True):
            self.neuro_routing.update(response["neuroRouting"])
        if "defaultPortForwarding" in response and ("defaultPortForwarding" in request or all_requested is True):
            self.default_port_forwarding.update(response["defaultPortForwarding"])

        if "autorenew_pf" in response and ("autorenew_pf" in request or all_requested is True):
            self.auto_renew_port_forwarding.update(response["autorenew_pf"])
        if "emailPortForwarding" in response and ("emailPortForwarding" in request or all_requested is True):
            self.email_port_forwarding_updates.update(response["emailPortForwarding"])
        if "pgpOnly" in response and ("pgpOnly" in request or all_requested is True):
            self.gpg_mail_only.update(response["pgpOnly"])

        if self.unvalidated_password != "" and self.unvalidated_username != "":
            self.core.settings.account.username.set(self.unvalidated_username)
            self.core.settings.account.password.set(self.unvalidated_password)
            self.unvalidated_username = ""
            self.unvalidated_password = ""

        self.credentials_valid.set(True)
        self.account_expired = False
        self.account_disabled = False
        self.last_update = datetime.now()

    def _response_check_error(self, response_dict):
        if "error" in response_dict:
            if response_dict["error"] == "errorUsernamePassword":
                self.credentials_valid.set(False, force_notify = True)
                self._logger.warning("login failed")
                raise UserAPIError()
            elif response_dict["error"] == "errorInvalidchars":
                self.credentials_valid.set(False, force_notify = True)
                self._logger.warning("login failed: invalid chars in username")
                raise UserAPIError()
            elif response_dict["error"] == "errorExpired":
                self.account_expired = True
                self._logger.warning("account expired")
                raise UserAPIError()
            elif response_dict["error"] == "errorDisabled":
                self._logger.warning("account disabled")
                self.account_disabled = True
                raise UserAPIError()
            elif response_dict["error"] == "errorApiCallLimit":
                self._logger.warning("API call limit exceeded")
                raise UserAPIError()
            else:
                self._logger.error("unknown error: '%s'", response_dict["error"])
                raise UserAPIError()

    def _response_get_server_groups(self, payload, response_dict):
        if "serverGroups" not in response_dict:
            if "getServerGroups" in payload:
                self._logger.error("despite requested, API didn't return server groups")
            return
        self._server_groups.clear()
        self._server_groups.extend( response_dict["serverGroups"])
        self._server_groups_last_checked = time.time()

