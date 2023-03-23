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
from config.files import OBFS

class StealthObfs(StealthCommon):
    def __init__(self, core, servergroup, openvpn_remote_ip, openvpn_remote_port):
        super().__init__(core, servergroup, openvpn_remote_ip, openvpn_remote_port)

        self._obfs_local_port = None  # parsed from output after launch
        self._process = None
        self.pt_state_file = None
        self.openvpn_arguments = [   ]
        self.remote_host = self._servergroup.vpn_server_config.obfs3_ip  # the ip or host the openvpn process actually connects to
        self.remote_port = self._core.settings.stealth.stealth_port.get()
        if core.settings.vpn.openvpn.tls_method.get() == OPENVPN_TLS_METHOD.tls_crypt:
            ports = STEALTH_PORTS.obfs_tlscrypt
        else:
            ports = STEALTH_PORTS.obfs
        if self.remote_port not in ports:
            self.remote_port = random.choice(ports)

        self.external_host_ip = self.remote_host
        self.external_host_port = self.remote_port
        self.should_be_active = False

    def start(self):
        self.should_be_active = True
        self.pt_state_file = os.path.join(tempfile.gettempdir(),"pt_state")
        env = {
            "TOR_PT_STATE_LOCATION"        : self.pt_state_file,
            "TOR_PT_MANAGED_TRANSPORT_VER" : "1",
            "TOR_PT_EXIT_ON_STDIN_CLOSE"   : "1",
            "TOR_PT_CLIENT_TRANSPORTS"     : "obfs3",
        }
        self._process = MySubProcess(OBFS, [], env)
        self._process.on_output_event.attach_observer(self._on_process_output)
        self._process.on_exited_event.attach_observer(self._on_process_exited)
        self._process.start()

        for i in range(10):
            if self._obfs_local_port is not None:
                break
            if self._process is None or self._process.check_exited() is True:
                self._logger.error("Failed to start process")
                break
            if self.should_be_active is False:
                break
            self._logger.info("Waiting for obfs to connect")
            time.sleep(1.5)
        if  self._obfs_local_port != None:
            self.openvpn_arguments = ["--socks-proxy", "127.0.0.1", self._obfs_local_port]
            return True
        return False

    def _on_process_output(self, _, source, data):
        self._logger.debug("%s: %s" % (source, data.decode("utf-8")))
        if source == "stdout":
            try:
                if data.find(b"CMETHOD ") > -1:
                    parts = data.split(b' ')
                    if (parts[1].decode("UTF-8") == "obfs3"):
                        self._obfs_local_port = "%s" % int(parts[3].split(b':')[1].decode("UTF-8"))
                        self._logger.debug("Local port found: %s" % self._obfs_local_port)
            except:
                pass

    def _on_process_exited(self):
        if self.pt_state_file is not None and os.path.exists(self.pt_state_file):
            try:
                os.remove(self.pt_state_file)
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