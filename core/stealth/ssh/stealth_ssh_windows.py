import random
import time

from core.stealth.common.stealth_common import StealthCommon
from config.constants import STEALTH_PORTS
from config.files import SSH
import subprocess
from threading import Thread

from core.stealth.ssh.stealth_ssh_common import StealthSSHCommon


class StealthSSHWindows(StealthSSHCommon):
    def start(self):
        self._cmd = [
            SSH,
            "-ssh", "-batch", "-4", "-noagent", "-N", "-T", "-x", "-a",
            "-l"  , self._ssh_username,
            "-pw" , self._ssh_password,
            "-P"  , str(self._ssh_port),
            "-L"  , "%s:%s:%s" % (self._ssh_local_port, self._openvpn_remote_ip, self._openvpn_remote_port),
        ]
        if self._ssh_fingerprint != "":
            self._cmd.extend([ "-hostkey", "%s" % self._ssh_fingerprint ])
        self._cmd.append(self._ssh_host)
        self._logger.info("ssh:" + " ".join(self._cmd))
        self._process = subprocess.Popen( self._cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        self._stdout_read_tread = Thread(target=self._read_stdout_thread, daemon=True)
        self._stdout_read_tread.start()
        self._stderr_read_tread = Thread(target=self._read_stderr_thread, daemon=True)
        self._stderr_read_tread.start()
        time.sleep(2)

