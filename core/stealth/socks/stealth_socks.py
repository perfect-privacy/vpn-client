import random
from core.stealth.common.stealth_common import StealthCommon
from config.constants import STEALTH_PORTS

class StealthSocks(StealthCommon):
    def __init__(self, core, servergroup, openvpn_remote_ip, openvpn_remote_port):
        super().__init__(core, servergroup, openvpn_remote_ip, openvpn_remote_port)
        self.proxy_username = None
        self.proxy_password = None

        if self._core.settings.stealth.stealth_custom_node.get() is True:
            self._proxy_host = self._core.settings.stealth.stealth_custom_hostname.get()
            self._proxy_port = self._core.settings.stealth.stealth_custom_port.get()
            if self._core.settings.stealth.stealth_custom_require_auth.get() is True:
                self.proxy_username =  self._core.settings.stealth.stealth_custom_auth_username.get()
                self.proxy_password =  self._core.settings.stealth.stealth_custom_auth_password.get()
        else:
            self._proxy_host    = servergroup.vpn_server_config.primary_ipv4
            self._proxy_port    = self._core.settings.stealth.stealth_port.get()
            if self._proxy_port not in STEALTH_PORTS.socks :
                self._proxy_port = random.choice(STEALTH_PORTS.socks)


            self.proxy_username = self._core.settings.account.username.get()
            self.proxy_password = self._core.settings.account.password.get()

        self.openvpn_arguments = [
            "--socks-proxy", self._proxy_host, str(self._proxy_port), "stdin"
        ]
        self.remote_host = self._openvpn_remote_ip   # the ip or host the openvpn process actually connects to
        self.remote_port = self._openvpn_remote_port
        self.external_host_ip = self._proxy_host
        self.external_host_port = self._proxy_port
