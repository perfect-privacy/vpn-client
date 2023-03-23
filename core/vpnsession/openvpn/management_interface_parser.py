import logging
from threading import Thread, Event, RLock
from gettext import gettext as _
from datetime import datetime
import sys
import traceback
import time
import re

from pyhtmlgui import Observable
from .openvpn_state import OpenVPNState

class ManagementInterfaceParser(Thread):
    # reading modes
    _READING_MODE_NORMAL = 0
    _READING_MODE_BULK_LOG = 1
    _READING_MODE_BULK_STATE = 2

    def __init__(self, connection, identifier, socket, username, password, proxy_username=None, proxy_password=None, management_password=""):
        """
        :type socket: socket.socket
        """
        super(ManagementInterfaceParser, self).__init__()

        self._logger = logging.getLogger(self.__class__.__name__ + " ({})".format(identifier))
        self.connection = connection
        self._socket = socket
        self._username = username
        self._password = password
        self._proxy_username = proxy_username
        self._proxy_password = proxy_password
        self._management_password = management_password

        self.openvpn_state = OpenVPNState()
        self.pid = None
        self._init_step = 0

        self._reading_mode = self._READING_MODE_NORMAL

        self.on_parser_closed = Observable()
        self._send_lock = RLock()

    def run(self):
        self._logger.debug("Starting to parse management interface")
        self._send_command(self._management_password)
        try:
            for line in self._get_line_from_socket():
                try:
                    self._process_line(line)
                except:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    tb = traceback.format_exception(exc_type, exc_value,exc_traceback, limit=2)
                    self._logger.error(tb)

            self._logger.debug("no more lines left")
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb = traceback.format_exception(exc_type, exc_value, exc_traceback, limit=2)
            self._logger.debug("".join(tb))
        finally:
            try:
                self._logger.debug("closing socket to management interface")
                self._socket.close()
            except:
                pass

        self.openvpn_state.set(OpenVPNState.OPENVPN_STATE_DISCONNECTED)

        self.on_parser_closed.notify_observers()
        self._logger.debug("Exited parser process")

    def _next_init_step(self):
        if self._init_step == 0:
            self._send_command("pid") # get pid
        elif self._init_step == 1:
            self._send_command("log on all")  # log in real time and bulk-log all previous log entries
        elif self._init_step == 2:
            self._send_command("state on all")
        elif self._init_step == 3:
            self._send_command("hold off") # don't hold on future restart
        elif self._init_step == 4:
            self._send_command("hold release") # let openvpn start its business
        else:
            self._logger.error("initializing already done, still trying to initialize")

        self._init_step += 1

    def _send_command(self, command):
        self._logger.debug("sending: '{}'".format(self._replace_secrets(command)))
        command = command.strip() + "\r\n"
        with self._send_lock:
            try:
                self._socket.sendall(command.encode())
            except:
                self._logger.debug("sending '{}' failed".format(self._replace_secrets(command)))

    def _get_line_from_socket(self):
        buff = ""
        done = False
        try:
            buff = self._socket.recv(1024)
            buff = buff.decode("UTF-8", errors="replace")
        except Exception as e:
            self._logger.debug("Socket recv failed '{}' failed".format(e))
            done = True

        while not done or buff:
            if "\n" in buff:
                (line, buff) = buff.split("\n", 1)
                yield line + "\n"
            else:
                more = None
                try:
                    more = self._socket.recv(1024)
                    more = more.decode("UTF-8", errors="replace")
                except Exception as e:
                    self._logger.debug("Socket recv1 failed '{}' failed".format(e))
                    done = True

                if not more:
                    done = True
                else:
                    buff = buff + more

        if buff:
            yield buff

    def _process_line(self, line):
        line = line.strip()
        self._logger.debug(self._replace_secrets(line))
        try:
            if "Opened utun device " in line:
                self.connection.interface = line.split("Opened utun device ")[1].split(" ")[0].strip()
            elif "ARP Flush on interface [" in line:
                self.connection.interface = line.split("ARP Flush on interface [")[1].split("]")[0].strip()
            elif "interface ipv6 set address " in line:
                self.connection.interface = line.split("interface ipv6 set address ")[1].split(" ")[0].strip()
            elif " MTU set to " in line:
                self.connection.interface = line.split(" on interface ")[1].split(" ")[0].strip()
            elif "TUN/TAP device " in line:
                self.connection.interface = line.split("TUN/TAP device ")[1].split(" opened")[0].strip()
        except:
            pass

        if line.startswith(">HOLD:Waiting for hold release"):
            self._next_init_step()
        elif line.startswith("SUCCESS: pid="):
            self.pid = int(line.replace("SUCCESS: pid=", "").strip())
            self._next_init_step()
        elif line == "SUCCESS: real-time log notification set to ON":
            self._reading_mode = self._READING_MODE_BULK_LOG
        elif line == "SUCCESS: real-time state notification set to ON":
            self._reading_mode = self._READING_MODE_BULK_STATE
        elif line == "END": # we only read the log/state in bulk mode on initial "log/state on all" command
            if self._reading_mode in [self._READING_MODE_BULK_LOG, self._READING_MODE_BULK_STATE]:
                self._next_init_step()
            if self._reading_mode == self._READING_MODE_BULK_STATE: # state: send state changed signal on last change only
                self.openvpn_state.notify_observers()
            self._reading_mode = self._READING_MODE_NORMAL  # reset reading mode

        elif (line.startswith(">STATE:") or self._reading_mode == self._READING_MODE_BULK_STATE):
            (timestamp, openvpn_state, description, tun_tap_ip, remote_ip) = line.replace(">STATE:", "", 1).split(",", 4)
            if (openvpn_state == OpenVPNState.OPENVPN_STATE_RECONNECTING and description == "auth-failure"):
                self.openvpn_state.set(openvpn_state)   # auth-failure: delete user/pass to ask for new one
                self._logger.debug("Server rejected Username/Password")
                self._username = None
                self._password = None
            elif openvpn_state == OpenVPNState.OPENVPN_STATE_CONNECTED:
                pass
            self.openvpn_state.set(openvpn_state)

        elif line.startswith(">LOG:") or self._reading_mode == self._READING_MODE_BULK_LOG:
            (timestamp, message_type, message) = line.replace(">LOG:", "", 1).split(",", 2)
            if message == "MANAGEMENT: CMD 'state all'":
                self._reading_mode = self._READING_MODE_BULK_STATE
            elif message == "MANAGEMENT: CMD 'hold off'":
                self._next_init_step()
            elif "PUSH_REPLY" in message:
                reply_message = ""
                for reply_part in message.split("'"):
                    if reply_part.startswith("PUSH_REPLY,"):
                        reply_message = reply_part.replace("PUSH_REPLY,", "")
                        break

                dns = []
                for opt in reply_message.split(","):
                    if opt.startswith("ifconfig "):
                        cmd, self.connection.ipv4_local_ip, self.connection.ipv4_local_netmask = opt.split(" ")
                    if opt.startswith("route-gateway "):
                        self.connection.ipv4_remote_gateway = opt.replace("route-gateway ","")
                    if opt.startswith("ifconfig-ipv6 "):
                        cmd, ipv6_local_ipNM, self.connection.ipv6_remote_gateway = opt.split(" ")
                        self.connection.ipv6_local_ip, self.connection.ipv6_local_netmask  = ipv6_local_ipNM.split("/")
                if dns:
                    self.ipv4_dns_servers = dns

        elif line == ">PASSWORD:Need 'Auth' username/password":
            self._send_command("username \"Auth\" {}".format(self._username))
            time.sleep(0.5)
            self._send_command("password \"Auth\" {}".format(self._password))

        elif line == ">PASSWORD:Need 'HTTP Proxy' username/password":
            self._send_command("username \"HTTP Proxy\" {}".format(self._proxy_username))
            time.sleep(0.5)
            self._send_command("password \"HTTP Proxy\" {}".format(self._proxy_password))

        elif line == ">PASSWORD:Need 'SOCKS Proxy' username/password":
            self._send_command("username \"SOCKS Proxy\" {}".format(self._proxy_username))
            time.sleep(0.5)
            self._send_command("password \"SOCKS Proxy\" {}".format(self._proxy_password))

    def request_disconnect(self):
        self._send_command("signal SIGTERM")

    def _replace_secrets(self, string):
        if self._management_password in string:
            string = string.replace(self._management_password, "PASSWORD-REMOVED")
        if self._username is not None and self._username != "":
            string = string.replace(self._username, "USERNAME-REMOVED")
        if self._password is not None and self._password != "":
            string = string.replace(self._password, "PASSWORD-REMOVED")
        if self._proxy_username is not None and self._proxy_username != "":
            string = string.replace(self._proxy_username, "USERNAME-REMOVED")
        if self._proxy_password is not None and self._proxy_password != "":
            string = string.replace(self._proxy_password, "PASSWORD-REMOVED")
        return string

    def __del__(self):
        try:
            if self.is_alive():
                self.request_disconnect()
        except:
            pass

