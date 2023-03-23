import os
import random
import socket
import subprocess
import time
import traceback
import uuid
from gettext import gettext as _
from subprocess import CalledProcessError

from config.config import PLATFORM
from config.constants import OPENVPN_PORTS, OPENVPN_PROTOCOLS, STEALTH_METHODS, OPENVPN_TLS_METHOD, OPENVPN_DRIVER
from config.constants import PLATFORMS
from config.paths import CONFIG_DIR, APP_VAR_DIR
from config.files import OPENVPN
from core.stealth import StealthHttp, StealthSocks, StealthStunnel, StealthSSH, StealthObfs
from core.vpnsession.common import VpnConnectionState, VPNConnection, VPNConnectionError
from .management_interface_parser import ManagementInterfaceParser
from ...libs.subcommand import MySubProcess

try:
    from signal import SIGKILL
except:
    from signal import CTRL_C_EVENT as SIGKILL


class OpenVPNConnection(VPNConnection):
    def __init__(self, identifier, core):
        super(OpenVPNConnection, self).__init__(identifier, core)

        self._openvpn_process = None
        self._parser = None

        self.hop_number = 0
        self.type = "openvpn"
        self.openvpn_device_guid = None
        self.stealth_plugin = None
        self.external_host_protocol = None
        self.external_host_port = None

    def _connect(self, servergroup, hop_number):

        self.servergroup = servergroup
        self.hop_number = hop_number

        if ((self._parser is not None and self._parser.is_alive())):
            self._logger.debug("Connecting cancelled: still alive")
            raise VPNConnectionError()

        interface = None
        if self.core.deviceManager is not None:
            if self.hop_number == 1:
                self.core.deviceManager.update() # check tun/tap adapters
            interfaces = self.core.deviceManager.get_devices()
            interfaces_in_use = [h.connection.openvpn_device_guid for h in self.core.session.hops if h.connection is not None ]
            interfaces_avail = [i for i in interfaces if i.guid not in interfaces_in_use]
            if len(interfaces_avail) == 0:
                self._logger.error("Starting OpenVPN process failed: no device found")
                self.state.set(VpnConnectionState.IDLE, _("Connecting failed"))
                raise VPNConnectionError()
            else:
                interface = interfaces_avail[0]
                self.openvpn_device_guid = interface.guid

        openvpn_tls_method = self.core.settings.vpn.openvpn.tls_method.get()
        openvpn_protocol = self.core.settings.vpn.openvpn.protocol.get()
        if self.core.settings.stealth.stealth_method.get() != STEALTH_METHODS.no_stealth:
            openvpn_protocol = OPENVPN_PROTOCOLS.tcp

        openvpn_ports = []
        if openvpn_protocol == OPENVPN_PROTOCOLS.tcp and openvpn_tls_method == OPENVPN_TLS_METHOD.tls_crypt: openvpn_ports = OPENVPN_PORTS.TLSCRYPT.tcp
        if openvpn_protocol == OPENVPN_PROTOCOLS.tcp and openvpn_tls_method == OPENVPN_TLS_METHOD.tls_auth:  openvpn_ports = OPENVPN_PORTS.TLSAUTH.tcp
        if openvpn_protocol == OPENVPN_PROTOCOLS.udp and openvpn_tls_method == OPENVPN_TLS_METHOD.tls_crypt: openvpn_ports = OPENVPN_PORTS.TLSCRYPT.udp
        if openvpn_protocol == OPENVPN_PROTOCOLS.udp and openvpn_tls_method == OPENVPN_TLS_METHOD.tls_auth:  openvpn_ports = OPENVPN_PORTS.TLSAUTH.udp
        if self.core.settings.vpn.openvpn.port.get() not in openvpn_ports:
            openvpn_port = random.choice(openvpn_ports)
        else:
            openvpn_port = self.core.settings.vpn.openvpn.port.get()

        if self.hop_number == 1:
            if PLATFORM == PLATFORMS.macos:
                os.system("killall pp.obfs4proxy pp.openvpn pp.stunnel")
            if PLATFORM == PLATFORMS.windows:
                os.system("TaskKill /IM pp.openvpn.exe /F")
                os.system("TaskKill /IM pp.obfs4proxy.exe /F")
                os.system("TaskKill /IM pp.tstunnel.exe /F")
                os.system("TaskKill /IM pp.plink.exe /F")
            if self.core.settings.stealth.stealth_method.get() == STEALTH_METHODS.ssh:
                self.stealth_plugin = StealthSSH(self.core, servergroup, servergroup.vpn_server_config.primary_ipv4, openvpn_port)
            elif self.core.settings.stealth.stealth_method.get() == STEALTH_METHODS.http:
                self.stealth_plugin = StealthHttp(self.core, servergroup, servergroup.vpn_server_config.primary_ipv4, openvpn_port)
            elif self.core.settings.stealth.stealth_method.get() == STEALTH_METHODS.stunnel:
                self.stealth_plugin = StealthStunnel(self.core, servergroup, servergroup.vpn_server_config.primary_ipv4, openvpn_port)
            elif self.core.settings.stealth.stealth_method.get() == STEALTH_METHODS.obfs:
                self.stealth_plugin = StealthObfs(self.core, servergroup, servergroup.vpn_server_config.primary_ipv4, openvpn_port)
            elif self.core.settings.stealth.stealth_method.get() == STEALTH_METHODS.socks:
                self.stealth_plugin = StealthSocks(self.core, servergroup, servergroup.vpn_server_config.primary_ipv4, openvpn_port)

        if self.stealth_plugin is None:
            openvpn_remote_host = servergroup.vpn_server_config.primary_ipv4
            openvpn_remote_port = openvpn_port
            self.external_host_ip = openvpn_remote_host
            self.external_host_port = openvpn_remote_port
        else:
            openvpn_remote_host = self.stealth_plugin.remote_host
            openvpn_remote_port = self.stealth_plugin.remote_port
            self.external_host_ip = self.stealth_plugin.external_host_ip
            self.external_host_port = self.stealth_plugin.external_host_port
        self.external_host_protocol = openvpn_protocol

        self.state.set(VpnConnectionState.CONNECTING, _("Connecting: Starting OpenVPN process"))

        if self.stealth_plugin is not None:
            time.sleep(2) # wait some time for firewall
            if self.stealth_plugin.start() is False:
                self._logger.error("Failed to start stealth")
                self._disconnect()
                #self.state.set(VpnConnectionState.IDLE, _("Connecting failed"))
                raise VPNConnectionError()


        management_port = self._get_free_tcp_port()
        if not os.path.exists(os.path.join(APP_VAR_DIR, "mpass")):
            open(os.path.join(APP_VAR_DIR, "mpass"), "w").write("%s" % uuid.uuid4())
        management_password = open(os.path.join(APP_VAR_DIR, "mpass"), "r").read()

        args = [
            "--cd"        , APP_VAR_DIR,
            "--config"    , os.path.join("configs", "common.conf"),
            "--proto"     , openvpn_protocol,
            "--management", "127.0.0.1", str(management_port), "mpass",
            "--cipher"    , self.core.settings.vpn.openvpn.cipher.get(),
            "--remote"    , openvpn_remote_host, str(openvpn_remote_port),
            "--cert"      , os.path.join("configs", "cl.%s.crt" % self.servergroup.vpn_server_config.groupname),
            "--key"       , os.path.join("configs", "cl.%s.key" % self.servergroup.vpn_server_config.groupname),
            "--ca"        , os.path.join("configs", "ca.openvpn.crt"),
            "--tun-mtu"   , "1500",
        ]

        if interface is not None:
            args.extend(["--dev-node", "{%s}" % interface.guid])

        if openvpn_tls_method == OPENVPN_TLS_METHOD.tls_crypt:
            args.extend(["--tls-crypt", os.path.join("configs", "ta.tls-crypt.key")])
            args.extend(["--tun-mtu-extra", "32"])
        elif openvpn_tls_method == OPENVPN_TLS_METHOD.tls_auth:
            args.extend(["--tls-auth", os.path.join("configs", "ta.tls-auth.%s.key" % self.servergroup.vpn_server_config.groupname), "1"])
            args.extend(["--compress"])
            if openvpn_protocol == OPENVPN_PROTOCOLS.udp:
                args.extend(["--fragment", "1300"])

        if openvpn_protocol == OPENVPN_PROTOCOLS.udp:
            args.extend(["--mssfix", "1300"])

        if self.core.settings.vpn.openvpn.driver.get() == OPENVPN_DRIVER.wintun and PLATFORM == PLATFORMS.windows:
            args.extend(["--windows-driver", "wintun"])

        if self.stealth_plugin is not None:
            args.extend(self.stealth_plugin.openvpn_arguments)

        self._logger.debug("Starting openvpn: {}".format(" ".join(args)))

        try:
            self._openvpn_process = MySubProcess(command=OPENVPN, args=args)
            self._openvpn_process.on_output_event.attach_observer(self._on_openvpn_process_output)
            self._openvpn_process.on_exited_event.attach_observer(self._on_openvpn_process_exited)
            self._openvpn_process.start()
        except Exception as e:
            self._logger.error("Starting OpenVPN failed: %s" % str(e))
            self._disconnect()
            raise VPNConnectionError()

        self.state.set(VpnConnectionState.CONNECTING, _("Connecting: Connecting to management interface"))

        number_of_attempts = 0
        while number_of_attempts <= 10:
            if self.core.session._should_be_connected is False:
                self._disconnect()
                return
            try:
                number_of_attempts += 1
                management_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                management_socket.connect(("127.0.0.1", management_port))
                self._logger.debug("Attempt #{} succeeded".format(number_of_attempts))
                break
            except socket.error:
                self._logger.debug("Attempt #{} failed".format(number_of_attempts))
                time.sleep(0.1 * number_of_attempts)
            if self._openvpn_process.check_exited() is True:
                self._logger.error("OpenVPN process exited, please check log for errors: %s\n%s " % (self._openvpn_process.get_stdout(),self._openvpn_process.get_stderr()))
                self._disconnect()
                raise VPNConnectionError()
        else:
            self._logger.error("Couldn't connect to management interface: maximum number of retries exceeded")
            self._disconnect()
            raise VPNConnectionError()

        self._parser = ManagementInterfaceParser(
            connection     = self,
            identifier     = self._identifier,
            socket         = management_socket,
            username       = self.core.settings.account.username.get(),
            password       = self.core.settings.account.password.get(),
            proxy_username = self.stealth_plugin.proxy_username if self.stealth_plugin is not None else None,
            proxy_password = self.stealth_plugin.proxy_password if self.stealth_plugin is not None else None,
            management_password = management_password
        )

        self._connect_parser_signals()
        self._parser.start()

    def _on_openvpn_process_exited(self):
        self._logger.debug("OpenVPN process exited")

    def _on_openvpn_process_output(self, _, source, data):
        if source == "stderr":
            self._logger.debug("OpenVPN %s: %s" % (source, data.decode("utf-8")))

    @staticmethod
    def _get_free_tcp_port():
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind(("127.0.0.1", 0))
        host, port = tcp.getsockname()
        tcp.close()
        time.sleep(0.1)
        return port

    def _connect_parser_signals(self):
        self._parser.openvpn_state.attach_observer(self._on_openvpn_state_changed)
        self._parser.on_parser_closed.attach_observer(self._on_parser_closed)

    def _disconnect_parser_signals(self):
        self._parser.openvpn_state.attach_observer(self._on_openvpn_state_changed)
        self._parser.on_parser_closed.detach_observer(self._on_parser_closed)

    def _on_openvpn_state_changed(self, sender, **kwargs):
        self._logger.debug("State changed to '%s'", sender.get() )
        if sender.is_connecting:
            self.state.set(VpnConnectionState.CONNECTING, VpnConnectionState.CONNECTING)
        elif sender.is_connected:
            self.state.set(VpnConnectionState.CONNECTED, VpnConnectionState.CONNECTED)
        elif sender.is_disconnecting:
            self.state.set(VpnConnectionState.DISCONNECTING, VpnConnectionState.DISCONNECTING)
        elif sender.is_disconnected:
            self._cleanup_processes()

    def _on_parser_closed(self, sender):
        self._logger.debug("Management Interface Parser closed")
        self._disconnect_parser_signals()
        self._cleanup_processes()

    def _disconnect(self):
        if self._parser:
            self._parser.request_disconnect()
            self._logger.debug("Waiting for management interface parser to finish")
            self._parser.join(10)
        self._cleanup_processes()

    def _cleanup_processes(self):
        if self.stealth_plugin is not None:
            self.stealth_plugin.stop()
        if self._openvpn_process is not None:
            self._openvpn_process.stop()
        self.state.set(VpnConnectionState.IDLE, VpnConnectionState.IDLE)

    def __repr__(self):
        return "OpenVPNConnection identifier='{}', state='{}'".format( str(self._identifier), self.state.get())
