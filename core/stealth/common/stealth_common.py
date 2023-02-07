import logging

from pyhtmlgui import ObservableDict, Observable

class StealthCommon(Observable):
    def __init__(self, core, servergroup, openvpn_remote_ip, openvpn_remote_port):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

        self._core = core
        self._servergroup = servergroup
        self._openvpn_remote_ip = openvpn_remote_ip
        self._openvpn_remote_port = openvpn_remote_port

        self.openvpn_arguments = []  # openvpn args we need, like proxy settings, openvpn processes uses theses if filled
        self.remote_host = None   # the ip or host the openvpn process actually connects to
        self.remote_port = None   # port that openvpn connects to
        self.external_host_ip = None # ip of vpn or proxy or ssh server, on the internet, we need to whitelist this in our firewall
        self.external_host_port = None # port of vpn or proxy or ssh server, on the internet, we need to whitelist this in our firewall

        self.proxy_username = None
        self.proxy_password = None

    def start(self):
        pass

    def stop(self):
        pass