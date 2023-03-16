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
from config.paths import CONFIG_DIR
from config.files import OPENVPN
from core.stealth import StealthHttp, StealthSocks, StealthStunnel, StealthSSH, StealthObfs
from core.vpnsession.common import VpnConnectionState, VPNConnection, VPNConnectionError
from .management_interface_parser import ManagementInterfaceParser

try:
    from signal import SIGKILL
except:
    from signal import CTRL_C_EVENT as SIGKILL


class OpenVPNConnection(VPNConnection):
    def __init__(self, identifier, core):
        super(OpenVPNConnection, self).__init__(identifier, core)

        self._openvpn_process = None
        self._parser = None

        self.servergroup = None
        self.hop_number = 0
        self.type = "openvpn"
        self.stealth_plugin = None


    def _connect(self, servergroup, hop_number):

        self.servergroup = servergroup
        self.hop_number = hop_number

        if ((self._parser is not None and self._parser.is_alive())):
            self._logger.debug("connecting cancelled: still alive")
            raise VPNConnectionError()

        interface = None
        if self.core.deviceManager is not None:
            if self.hop_number == 1:
                self.core.deviceManager.update() # check tun/tap adapters
            interface = self.core.deviceManager.get_device_by_hop(self.hop_number)
            if interface is None:
                self._logger.error("starting OpenVPN process failed: no device found")
                self.state.set(VpnConnectionState.IDLE, _("Connecting failed"))
                raise VPNConnectionError()

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

        if self.hop_number == 1:
            if PLATFORM == PLATFORMS.macos:
                os.system("killall pp.obfs4proxy pp.openvpn pp.stunnel")
            if PLATFORM == PLATFORMS.windows:
                os.system("TaskKill /IM pp.openvpn.exe /F")
                os.system("TaskKill /IM pp.obfs4proxy.exe /F")
                os.system("TaskKill /IM pp.tstunnel.exe /F")
                os.system("TaskKill /IM pp.plink.exe /F")

        self.state.set(VpnConnectionState.CONNECTING, _("Connecting: Starting OpenVPN process"))

        if self.stealth_plugin is not None:
            time.sleep(2) # wait some time for firewall
            if self.stealth_plugin.start() is False:
                self._logger.error("failed to start stealth")
                self.state.set(VpnConnectionState.IDLE, _("Connecting failed"))
                raise VPNConnectionError()


        management_port = self._get_free_tcp_port()
        if not os.path.exists(os.path.join(CONFIG_DIR, "mpass")):
            open(os.path.join(CONFIG_DIR, "mpass"), "w").write("%s" % uuid.uuid4())
        management_password = open(os.path.join(CONFIG_DIR, "mpass"), "r").read()

        args = [
            OPENVPN,
            "--cd"        , CONFIG_DIR,
            "--config"    , "common.conf",
            "--proto"     , openvpn_protocol,
            "--management", "127.0.0.1", str(management_port), "mpass",
            "--cipher"    , self.core.settings.vpn.openvpn.cipher.get(),
            "--remote"    , openvpn_remote_host, str(openvpn_remote_port),
            "--cert"      , "cl.%s.crt" % self.servergroup.vpn_server_config.groupname,
            "--key"       , "cl.%s.key" % self.servergroup.vpn_server_config.groupname,
        ]

        if interface is not None:
            args.extend(["--dev-node", "{%s}" % interface.guid])

        if openvpn_tls_method == OPENVPN_TLS_METHOD.tls_crypt:
            args.extend(["--tls-crypt", "ta.tls-crypt.key"])
            args.extend(["--tun-mtu-extra", "32"])

        #tun_mtu = 1500 - ((self.hop_number-1) * 84)
        args.extend(["--tun-mtu", "1500"])

        if openvpn_tls_method == OPENVPN_TLS_METHOD.tls_auth:
            args.extend(["--tls-auth", "ta.tls-auth.%s.key" % self.servergroup.vpn_server_config.groupname, "1"])
            args.extend(["--compress"])
            if openvpn_protocol == OPENVPN_PROTOCOLS.udp:
                args.extend(["--fragment", "1300"])

        if openvpn_protocol == OPENVPN_PROTOCOLS.udp:
            args.extend(["--mssfix", "1300"])

        if self.core.settings.vpn.openvpn.driver.get() == OPENVPN_DRIVER.wintun and PLATFORM == PLATFORMS.windows:
            args.extend(["--windows-driver", "wintun"])

        if self.stealth_plugin is not None:
            args.extend(self.stealth_plugin.openvpn_arguments)

        self._logger.debug("starting openvpn client: {}".format(" ".join(args)))

        try:
            self._openvpn_process = subprocess.Popen(args, start_new_session=True)
        except OSError as e:  # ie. file not found
            self._logger.error("starting OpenVPN process failed")
            self._logger.debug(str(e))
            self.state.set(VpnConnectionState.IDLE, _("Connecting failed"))
            raise VPNConnectionError()
        except CalledProcessError as e:  # return_code != 0
            self._logger.error("starting OpenVPN process failed: non-zero exit code {}".format(e.returncode))
            self._logger.debug(str(e))
            self.state.set(VpnConnectionState.IDLE, _("Connecting failed"))
            raise VPNConnectionError()

        self._logger.debug("connecting to management interface")
        self.state.set(VpnConnectionState.CONNECTING, _("Connecting: Connecting to management interface"))

        number_of_attempts = 0
        while number_of_attempts <= 10:
            if self.core.session._should_be_connected is False:
                self.state.set(VpnConnectionState.IDLE, _("Connecting failed"))
                return
            try:
                number_of_attempts += 1
                self._logger.debug("attempt #{}".format(number_of_attempts))
                management_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                management_socket.connect(("127.0.0.1", management_port))
                self._logger.debug("attempt #{} succeeded".format(number_of_attempts))
                break
            except socket.error:
                self._logger.debug("attempt #{} failed".format(number_of_attempts))
                time.sleep(0.1 * number_of_attempts)
        else:
            self._logger.error("Couldn't connect to management interface: maximum number of retries exceeded")
            self.state.set(VpnConnectionState.IDLE, _("Connecting failed"))
            raise VPNConnectionError()

        self._logger.debug("starting management interface parser")
        self._parser = ManagementInterfaceParser(
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

    @staticmethod
    def _get_free_tcp_port():
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind(("127.0.0.1", 0))
        host, port = tcp.getsockname()
        tcp.close()
        time.sleep(0.1)
        return port

    def _connect_parser_signals(self):
        self._logger.debug("connecting parser signals")
        self._parser.openvpn_state.attach_observer(self._on_openvpn_state_changed)
        self._parser.on_invalid_credentials_detected.attach_observer(self._on_invalid_credentials_detected)
        self._parser.on_connection_closed.attach_observer(self._on_parser_connection_closed)
        self._parser.on_ipv4_local_ip_change.attach_observer(self._on_ipv4_local_ip_change)
        self._parser.on_ipv4_local_netmask_change.attach_observer(self._on_ipv4_local_netmask_change)
        self._parser.on_ipv4_remote_gateway_change.attach_observer(self._on_ipv4_remote_gateway_change)
        self._parser.on_ipv4_dns_servers_change.attach_observer(self._on_ipv4_dns_servers_change)
        self._parser.on_ipv6_local_ip_change.attach_observer(self._on_ipv6_local_ip_change)
        self._parser.on_ipv6_local_netmask_change.attach_observer(self._on_ipv6_local_netmask_change)
        self._parser.on_ipv6_remote_gateway_change.attach_observer(self._on_ipv6_remote_gateway_change)
        self._parser.on_device_change.attach_observer(self._on_device_change)

    def _disconnect_parser_signals(self):
        self._logger.debug("disconnecting parser signals")
        self._parser.openvpn_state.attach_observer(self._on_openvpn_state_changed)
        self._parser.on_invalid_credentials_detected.detach_observer(self._on_invalid_credentials_detected)
        self._parser.on_connection_closed.detach_observer(self._on_parser_connection_closed)
        self._parser.on_ipv4_local_ip_change.detach_observer(self._on_ipv4_local_ip_change)
        self._parser.on_ipv4_local_netmask_change.detach_observer(self._on_ipv4_local_netmask_change)
        self._parser.on_ipv4_remote_gateway_change.detach_observer(self._on_ipv4_remote_gateway_change)
        self._parser.on_ipv4_dns_servers_change.detach_observer(self._on_ipv4_dns_servers_change)
        self._parser.on_ipv6_local_ip_change.detach_observer(self._on_ipv6_local_ip_change)
        self._parser.on_ipv6_local_netmask_change.detach_observer(self._on_ipv6_local_netmask_change)
        self._parser.on_ipv6_remote_gateway_change.detach_observer(self._on_ipv6_remote_gateway_change)
        self._parser.on_device_change.detach_observer(self._on_device_change)

    def _on_openvpn_state_changed(self, sender, **kwargs):
        self._logger.debug("openvpn connection state changed")
        if sender.is_connecting:
            self.state.set(VpnConnectionState.CONNECTING, VpnConnectionState.CONNECTING)
        elif sender.is_connected:
            self.state.set(VpnConnectionState.CONNECTED, VpnConnectionState.CONNECTED)
        elif sender.is_disconnecting:
            self.state.set(VpnConnectionState.DISCONNECTING, VpnConnectionState.DISCONNECTING)
        elif sender.is_disconnected:
            self.state.set(VpnConnectionState.IDLE, VpnConnectionState.IDLE)

    def _on_invalid_credentials_detected(self, sender):
        self.on_invalid_credentials_detected.notify_observers()

    def _on_parser_connection_closed(self, sender):
        self._logger.debug("parser connection closed")
        self._disconnect_parser_signals()
        if  self.stealth_plugin is not None:
            self.stealth_plugin.stop()
        self.stealth_plugin = None
        self.state.set(VpnConnectionState.IDLE, _("Not connected"))


    def _on_ipv4_local_ip_change(self, sender, address):
        self.ipv4_local_ip = address

    def _on_ipv4_local_netmask_change(self, sender, netmask):
        self.ipv4_local_netmask = netmask

    def _on_ipv4_remote_gateway_change(self, sender, address):
        self.ipv4_remote_gateway = address

    def _on_ipv4_dns_servers_change(self, sender, dns_servers):
        self._logger.debug("got new DNS servers: {}".format(dns_servers))
        self.ipv4_dns_servers = dns_servers
        #self.on_dns_servers_changed.send(self, dns_servers=self.dns_servers)

    def _on_ipv6_local_ip_change(self, sender, address):
        self.ipv6_local_ip = address

    def _on_ipv6_local_netmask_change(self, sender, netmask):
        self.ipv6_local_netmask = netmask

    def _on_ipv6_remote_gateway_change(self, sender, address):
        self.ipv6_remote_gateway = address

    def _on_remote_ip_available(self, sender, address):
        self._remote_ip_address = address

    def _on_device_change(self, sender, interface):
        self.interface = interface

    def _disconnect(self):
        self._logger.debug("sending disconnect request to openvpn process")

        if self._parser:
            self._parser.request_disconnect()

            self._logger.debug("waiting for parser to finish")
            self._parser.join(10)
            if self._parser.is_alive():
                self._logger.error("OpenVPN process didn't shut down within 10 sec")
                if self._parser.pid is not None:
                    self._logger.error("sending SIGKILL to PID {}".format(self._parser.pid))
                    try:
                        os.kill(self._parser.pid, SIGKILL)
                    except OSError:
                        self._logger.critical("killing zombie OpenVPN process with PID {} failed".format(self._parser.pid))
                        raise VPNConnectionError()
                else:
                    self._logger.critical("unable to kill zombie OpenVPN process: unknown PID")
                    raise VPNConnectionError()
            else:
                self._logger.debug("parser quit successfully")
        else:
            self._logger.debug("there's no openvpn parser")

        try:
            if self._openvpn_process and self._openvpn_process.poll() is None:
                self._logger.debug("waiting for openvpn process to finish")
                self._openvpn_process.wait(5)
                if self._openvpn_process.poll() is None:
                    self._logger.info("main OpenVPN process is still running. terminating.")
                    self._openvpn_process.terminate()
                    time.sleep(5)
                    if self._openvpn_process.poll() is None:
                        self._logger.error("main OpenVPN process didn't terminate within 5 seconds. sending SIGKILL")
                        os.kill(self._openvpn_process.pid, SIGKILL)
                        self._openvpn_process.kill()
                        time.sleep(5)
                        if self._openvpn_process.poll() is None:
                            self._logger.critical("main OpenVPN process (PID {}) didn't quit 5 seconds after sending SIGKILL. Please restart your computer.".format(self._openvpn_process.pid))
                            raise VPNConnectionError()
        except Exception as e:
            self._logger.debug(traceback.format_exc())

        if  self.stealth_plugin is not None:
            self.stealth_plugin.stop()

        if self._openvpn_process:
            if self._openvpn_process.poll() is not None:
                self._logger.debug("main OpenVPN process (PID {}) exited with return code {}".format( self._openvpn_process.pid, self._openvpn_process.returncode))
            else:
                self._logger.error("main OpenVPN process did not exit")
        else:
            self._logger.debug("there's no openvpn process")
            self.state.set(VpnConnectionState.IDLE, _("Not connected"))


    def __repr__(self):
        return "OpenVPNConnection identifier='{}', state='{}'".format( str(self._identifier), self.state.get())
