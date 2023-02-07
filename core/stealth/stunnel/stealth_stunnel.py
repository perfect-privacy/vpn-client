import subprocess
import random
import tempfile
from threading import Thread
import time
import os
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
        if core.settings.vpn.openvpn.tls_method == OPENVPN_TLS_METHOD.tls_crypt:
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

    def start(self):
        f, self.configfile = tempfile.mkstemp(prefix="configfile")
        config = "client = yes\n"
        config += "[stealth]\n"
        config += "client = yes\n"
        config += "accept = 127.0.0.1:%s\n" %  self._stunnel_local_port
        config += "connect = %s:%s\n" % (self._stunnel_host, self._stunnel_port)
        with os.fdopen(f, "w") as f:
            f.write("".join(config))
        self._process = subprocess.Popen([STUNNEL, self.configfile], stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        self._stdout_read_tread = Thread(target=self._read_stdout_thread, daemon=True)
        self._stdout_read_tread.start()
        self._stderr_read_tread = Thread(target=self._read_stderr_thread, daemon=True)
        self._stderr_read_tread.start()
        time.sleep(2)
        return True


    def _read_stdout_thread(self):
        for line in iter(self._process.stdout.readline, b''):
            self._logger.debug("stdout:" + line.decode("UTF-8"))
        try:
            self._process.stdout.close()
        except:
            pass
        self._stdout_read_tread = None
        if os.path.exists(self.configfile):
            os.remove(self.configfile)

    def _read_stderr_thread(self):
        for line in iter(self._process.stderr.readline, b''):
            self._logger.debug("stderr:" + line.decode("UTF-8"))
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
        if os.path.exists(self.configfile):
            os.remove(self.configfile)
        self._process = None