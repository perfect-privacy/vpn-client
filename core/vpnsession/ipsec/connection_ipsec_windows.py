from core.vpnsession.common import VpnConnectionState, VPNConnection
import threading
import time
import os
from core.libs.subcommand import SubCommand

class IpsecConnection(VPNConnection):
    """
    :type _parser: core.core.vpn.openvpn_management_interface_parser.OpenVPNManagementInterfaceParser
    """
    def __init__(self, identifier, core):
        super(IpsecConnection, self).__init__(identifier, core)
        self.state.set(VpnConnectionState.IDLE)
        self.state.attach_observer(self._on_state_changed)
        self.should_be_connected = False
        self.hop_number = 0
        self.hop_name = ""
        self.ipv4_local_ip       = None  # local vpn adapter ipv4 pushed by openvpn server dhcp

        self._worker = threading.Thread(target=self._worker_thread, daemon=True)

    def _connect(self, servergroup, hop_number):
        self.servergroup = servergroup
        self.hop_number = hop_number
        self.hop_name = "PerfectPrivacyVPN" # for whatever reason, spaces don't work
        self.should_be_connected = True
        self.state.set(VpnConnectionState.CONNECTING)
        self._disconnect_device()
        self._remove_device()
        self._install_device()
        self._connect_device()
        self._worker.start()
        self._read_state()

    def _disconnect(self):
        self.should_be_connected = False
        self._logger.debug("sending disconnect request to ipsec process")
        self._disconnect_device()
        self._remove_device()
        self._read_state()

    def _install_device(self):
        cmd = ['Add-VpnConnection',
                '-Name'                 , '"%s"' % self.hop_name,
                '-ServerAddress'        , self.servergroup.vpn_server_config.primary_ipv4,
                '-AllUserConnection'    , '$true',
                '-TunnelType'           , 'automatic',
                '-EncryptionLevel'      , '"Maximum"',
                '-AuthenticationMethod' , 'mschapv2',
                '-Force' ,
        ]
        r = self.core.powershell.execute(" ".join(cmd))
        print("foobar", r)

        cmd = ['Set-VpnConnectionIPsecConfiguration',
               '-ConnectionName'                  , '"%s"' % self.hop_name,
                '-EncryptionMethod'                , 'AES256'   ,  # DES,DES3,AES128,AES192,AES256,GCMAES128, GCMAES256
                '-IntegrityCheckMethod'            , 'SHA256'   ,  # MD5, SHA1, SHA256, SHA384
                '-PfsGroup'                        , 'None'     ,  # None, PFS1, PFS2, PFS2048, ECP256, ECP384, PFSMM, PFS24
                '-DHGroup'                         , 'ECP256'   ,  # None, Group1, Group2, Group14, ECP256, ECP384, Group24
                '-CipherTransformConstants'        , 'AES256'   ,  # DES, DES3, AES128, AES192, AES256, GCMAES128, GCMAES192, GCMAES256, None
                '-AuthenticationTransformConstants', 'SHA256128'     ,  # MD596, SHA196, SHA256128, GCMAES128, GCMAES192, GCMAES256, None
                '-AllUserConnection',
                '-PassThru',
                '-Force'   ,
        ]
        r = self.core.powershell.execute(" ".join(cmd))

    def _remove_device(self):
        cmd = ['Remove-VpnConnection',
                '-Name', '"%s"' % self.hop_name,
                '-AllUserConnection',
                '-Force',
        ]
        self.core.powershell.execute(" ".join(cmd))

    def _connect_device(self):
        self._logger.debug("Connecting Ipsec")
        output = self.core.powershell.execute('c:\\Windows\\system32\\rasdial.exe "%s" "%s" "%s"' % ( self.hop_name, self.core.settings.account.username.get(), self.core.settings.account.password.get())).strip()
        self._logger.debug("Ipsec connect output: %s" % output)

        print(output)

    def _disconnect_device(self):
        self._logger.debug("Disconnecting Ipsec")
        output = self.core.powershell.execute('c:\\Windows\\system32\\rasdial.exe "%s" /DISCONNECT' % self.hop_name).strip()
        self._logger.debug("Ipsec disconnect output: %s" % output)

    def _read_state(self):
        state = self.core.powershell.execute('(Get-VpnConnection -Name "%s" -AllUserConnection).ConnectionStatus' % self.hop_name).strip()
        if state == b"Connected":
            self.state.set(VpnConnectionState.CONNECTED)
        elif state == b"Connecting":
            self.state.set(VpnConnectionState.CONNECTING)
        elif state == b"Disconnected":
            self.state.set(VpnConnectionState.IDLE)
        elif state == b"Disconnecting":
            self.state.set(VpnConnectionState.DISCONNECTING)
        else:
            self.state.set(VpnConnectionState.IDLE)

    def _worker_thread(self):
        while self.should_be_connected is True:
            time.sleep(10)
            self._read_state()

    def _on_state_changed(self, sender, new_state, **kwargs):
        if new_state == VpnConnectionState.IDLE:
            self._delete_route()

        if new_state == VpnConnectionState.CONNECTED:
            self._add_route()

    def _add_route(self):
        success, stdout, stderr = SubCommand().run("netsh", ["interface","ipv6", "add", "route",    "2000::/4", 'interface="%s"' % self.hop_name ])
        success, stdout, stderr = SubCommand().run("netsh", ["interface","ipv6", "add", "route",    "3000::/4", 'interface="%s"' % self.hop_name ])
        success, stdout, stderr = SubCommand().run("netsh", ["interface","ipv4", "add", "route",   "0.0.0.0/1", 'interface="%s"' % self.hop_name ])
        success, stdout, stderr = SubCommand().run("netsh", ["interface","ipv4", "add", "route", "128.0.0.0/1", 'interface="%s"' % self.hop_name ])

    def _delete_route(self):
        pass

    #def _on_invalid_credentials_detected(self, sender):
    #    self.on_invalid_credentials_detected.send(self)

    #def _on_dns_servers_pushed(self, sender, dns_servers):
    #    self._logger.debug("got new DNS servers: {}".format(dns_servers))
    #    self.dns_servers = dns_servers
    #    #self.on_dns_servers_changed.send(self, dns_servers=self.dns_servers)

    #def _on_local_ip_available(self, sender, address):
    #    self._local_ip_address = address

    #def _on_remote_ip_available(self, sender, address):
    #    self._remote_ip_address = address

    def __repr__(self):
        return "IPSECConnection identifier='{}', state='{}, {}'".format( str(self._identifier), self.state, self.state)


