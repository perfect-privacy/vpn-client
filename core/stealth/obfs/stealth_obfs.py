import subprocess
import random
import tempfile
from threading import Thread
import time
import os

from core.stealth.common.stealth_common import StealthCommon
from core.stealth.common.stealth_state import StealthState
from config.constants import STEALTH_PORTS, OPENVPN_TLS_METHOD
from config.files import OBFS

class StealthObfs(StealthCommon):
    def __init__(self, core, servergroup, openvpn_remote_ip, openvpn_remote_port):
        super().__init__(core, servergroup, openvpn_remote_ip, openvpn_remote_port)

        self._obfs_local_port = None  # parsed from output after launch
        self._process = None

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


    def start(self):
        pt_state = os.path.join(tempfile.gettempdir(),"pt_state")
        env = os.environ.copy()
        env.update({
            "TOR_PT_STATE_LOCATION"        : pt_state,
            "TOR_PT_MANAGED_TRANSPORT_VER" : "1",
            "TOR_PT_EXIT_ON_STDIN_CLOSE"   : "1",
            "TOR_PT_CLIENT_TRANSPORTS"     : "obfs3",
        })
        self._logger.info("obfs:" + OBFS )
        self._process = subprocess.Popen([OBFS], stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
        self._stdout_read_tread = Thread(target=self._read_stdout_thread, daemon=True)
        self._stdout_read_tread.start()
        self._stderr_read_tread = Thread(target=self._read_stderr_thread, daemon=True)
        self._stderr_read_tread.start()

        for i in range(10):
            if self._obfs_local_port is not None or self._stdout_read_tread is None:
                break
            self._logger.info("waiting for obfs to connect")
            time.sleep(1.5)
        self.openvpn_arguments = [
            "--socks-proxy", "127.0.0.1", self._obfs_local_port
        ]
        return self._obfs_local_port != None

    def _read_stdout_thread(self):
        for line in iter(self._process.stdout.readline, b''):
            self._logger.info("stdout:" + line.decode("UTF-8"))
            if line.find(b"CMETHOD ") > -1:
                parts = line.split(b' ')
                if (parts[1].decode("UTF-8") == "obfs3"):
                    self._obfs_local_port = "%s" % int(parts[3].split(b':')[1].decode("UTF-8"))
        try:
            self._process.stdout.close()
        except:
            pass
        self._stdout_read_tread = None

    def _read_stderr_thread(self):
        for line in iter(self._process.stderr.readline, b''):
            self._logger.info("stderr:" + line.decode("UTF-8"))
        try:
            self._process.stderr.close()
        except:
            pass
        self._stderr_read_tread = None

    def stop(self):
        try:
            self._process.stdin.close()
        except:
            pass
        try:
            self._process.kill()
        except:
            pass
        self._process = None