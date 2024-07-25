from core.libs.powershell import getPowershellInstance
from core.vpnsession.common import VpnConnectionState, VPNConnection
import threading
import time
from core.libs.subcommand import SubCommand
from config.files import NETSH

class IpsecConnection(VPNConnection):
    """
    :type _parser: core.core.vpn.openvpn_management_interface_parser.OpenVPNManagementInterfaceParser
    """
    def __init__(self, identifier, core):
        super(IpsecConnection, self).__init__(identifier, core)
        self.state.set(VpnConnectionState.IDLE)
        self.is_active = False
        self.type = "ipsec"
        self.interface = None
        self.interfaceAlias =  "PerfectPrivacyVPN" # for whatever reason, spaces don't work
        self._worker = None

    def _connect(self, servergroup, hop_number):
        self.servergroup = servergroup
        self.external_host_ip =  self.servergroup.vpn_server_config.primary_ipv4
        self.hop_number = hop_number
        self.is_active = True
        self.state.set(VpnConnectionState.CONNECTING)
        self._disconnect_device()
        self._remove_device()
        self._install_device()
        self._connect_device()
        if self._worker is None:
            self._worker = threading.Thread(target=self._worker_thread, daemon=True)
            self._worker.start()
        self._read_state()

    def _disconnect(self):
        self.is_active = False
        self._logger.debug("Sending disconnect request to ipsec process")
        self._disconnect_device()
        self._remove_device()
        self._read_state()

    def _install_device(self):
        cmd = ['Add-VpnConnection',
                '-Name'                 , '"%s"' % self.interfaceAlias,
                '-ServerAddress'        , self.external_host_ip,
                '-AllUserConnection'    , '$true',
                '-TunnelType'           , 'automatic',
                '-EncryptionLevel'      , '"Maximum"',
                '-AuthenticationMethod' , 'mschapv2',
                '-Force' ,
        ]
        r = getPowershellInstance().execute(" ".join(cmd))
        cmd = ['Set-VpnConnectionIPsecConfiguration',
               '-ConnectionName'                  , '"%s"' % self.interfaceAlias,
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
        r = getPowershellInstance().execute(" ".join(cmd))

    def _remove_device(self):
        cmd = ['Remove-VpnConnection',
                '-Name', '"%s"' % self.interfaceAlias,
                '-AllUserConnection',
                '-Force',
        ]
        getPowershellInstance().execute(" ".join(cmd))

    def _connect_device(self):
        self._logger.debug("Connecting Ipsec")
        output = getPowershellInstance().execute('c:\\Windows\\system32\\rasdial.exe "%s" "%s" "%s"' % ( self.interfaceAlias, self.core.settings.account.username.get(), self.core.settings.account.password.get())).strip()
        self._logger.debug("Ipsec connect output: %s" % output)

    def _disconnect_device(self):
        self._logger.debug("Disconnecting Ipsec")
        output = getPowershellInstance().execute('c:\\Windows\\system32\\rasdial.exe "%s" /DISCONNECT' % self.interfaceAlias).strip()
        self._logger.debug("Ipsec disconnect output: %s" % output)

    def _read_state(self):
        state = getPowershellInstance().execute('(Get-VpnConnection -Name "%s" -AllUserConnection).ConnectionStatus' % self.interfaceAlias).strip()
        if state == b"Connected":
            if self.interface is None or self.ipv4_local_ip is None :
                self._get_interface_data()
            self.state.set(VpnConnectionState.CONNECTED)
        elif state == b"Connecting":
            self.state.set(VpnConnectionState.CONNECTING)
        elif state == b"Disconnected":
            self.state.set(VpnConnectionState.IDLE)
        elif state == b"Disconnecting":
            self.state.set(VpnConnectionState.DISCONNECTING)
        else:
            self.state.set(VpnConnectionState.IDLE)

    def _get_interface_data(self):
        routing_table = getPowershellInstance().execute("Get-NetRoute | Select-Object -Property ifIndex,DestinationPrefix,NextHop,InterfaceAlias | ConvertTo-Csv ")
        if routing_table is not None:
            for line in routing_table.split(b"\n"):
                try:
                    if b"PerfectPrivacyVPN" in line:
                        ifIndex, destinationPrefix, nextHop, interfaceAlias = line.decode("utf-8").strip().split(",")
                        self.interface = ifIndex[1:-1]
                        destinationPrefix = destinationPrefix[1:-1]
                        nextHop = nextHop[1:-1]
                        if destinationPrefix.startswith("10.") and destinationPrefix.endswith("/32") and nextHop.startswith(
                                "0.0.0.0"):  # our ip found
                            self.ipv4_local_ip = destinationPrefix.split("/")[0]
                except Exception as e:
                    pass

    def _worker_thread(self):
        while self.is_active is True:
            if self.state.get() in [VpnConnectionState.CONNECTING, VpnConnectionState.DISCONNECTING]:
                time.sleep(3)
            elif self.state.get() in [VpnConnectionState.CONNECTED]:
                time.sleep(30)
            else:
                time.sleep(10)
            self._read_state()
        self._worker = None

    def __repr__(self):
        return "IPSECConnection identifier='{}', state='{}, {}'".format( str(self._identifier), self.state, self.state)


