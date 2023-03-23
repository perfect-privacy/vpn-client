import subprocess
import random
import tempfile
from threading import Thread
import time
import os

from core.libs.subcommand import MySubProcess
from core.stealth.common.stealth_common import StealthCommon
from core.stealth.common.stealth_state import StealthState
from config.constants import STEALTH_PORTS, OPENVPN_TLS_METHOD
from config.files import STUNNEL


class StealthStunnel(StealthCommon):

    def __init__(self, core, servergroup, openvpn_remote_ip, openvpn_remote_port):
        super().__init__(core, servergroup, openvpn_remote_ip, openvpn_remote_port)

        if self._core.settings.stealth.stealth_custom_node.get() is True:
            self._stunnel_host = self._core.settings.stealth.stealth_custom_hostname.get()
            self._stunnel_port = self._core.settings.stealth.stealth_custom_port.get()
        else:
            self._stunnel_host =  self._servergroup.vpn_server_config.stunnel_ip
            self._stunnel_port = self._core.settings.stealth.stealth_port.get()
        if core.settings.vpn.openvpn.tls_method.get() == OPENVPN_TLS_METHOD.tls_crypt:
            ports = STEALTH_PORTS.stunnel_tlscrypt
        else:
            ports = STEALTH_PORTS.stunnel
        if self._stunnel_port not in ports:
            self._stunnel_port = random.choice(ports)

        self._stunnel_local_port = "1111"
        self._process = None
        self.configfile = None

        self.openvpn_arguments = []
        self.remote_host = "127.0.0.1"  # the ip or host the openvpn process actually connects to
        self.remote_port = self._stunnel_local_port
        self.external_host_ip = self._stunnel_host
        self.external_host_port = self._stunnel_port
        self.should_be_active = False

    def start(self):
        self.should_be_active = True
        f, self.configfile = tempfile.mkstemp(prefix="configfile")
        config = "client = yes\n"
        config += "[stealth]\n"
        config += "client = yes\n"
        config += "accept = 127.0.0.1:%s\n" %  self._stunnel_local_port
        config += "connect = %s:%s\n" % (self._stunnel_host, self._stunnel_port)
        with os.fdopen(f, "w") as f:
            f.write("".join(config))

        self._process = MySubProcess(STUNNEL, [self.configfile])
        self._process.on_output_event.attach_observer(self._on_process_output)
        self._process.on_exited_event.attach_observer(self._on_process_exited)
        self._process.start()
        time.sleep(2)
        if self._process is None:
            return False
        return True

    def _on_process_output(self, _, source, data):
        self._logger.debug("%s: %s" % (source, data.decode("utf-8")))

    def _on_process_exited(self):
        if self.configfile is not None and os.path.exists(self.configfile):
            try:
                os.remove(self.configfile)
            except:
                pass
        if self._process is not None:
            self._process.on_exited_event.detach_observer(self._on_process_exited)
            self._process.on_output_event.detach_observer(self._on_process_output)
            self._process = None

    def stop(self):
        self.should_be_active = False
        if self._process is not None:
            self._process.stop()