from pathlib import Path
import os, uuid
from pyhtmlgui import Observable
from core.libs.permanent_property import PermanentProperty

from config.constants import PROTECTION_SCOPES, OPENVPN_PROTOCOLS, VPN_PROTOCOLS, OPENVPN_CIPHER, STEALTH_METHODS,OPENVPN_DRIVER, OPENVPN_TLS_METHOD


class Settings_Leakprotection(Observable):
    def __init__(self):
        super().__init__()

        self.leakprotection_scope = PermanentProperty(self.__class__.__name__ + ".leakprotection_scope", PROTECTION_SCOPES.tunnel)
        self.leakprotection_scope.attach_observer(self._on_subitem_updated)

        self.allow_downloads_without_vpn = PermanentProperty(self.__class__.__name__ + ".allow_downloads_without_vpn", True)
        self.allow_downloads_without_vpn.attach_observer(self._on_subitem_updated)

        self.enable_ms_leak_protection = PermanentProperty(self.__class__.__name__ + ".enable_ms_leak_protection", True)
        self.enable_ms_leak_protection.attach_observer(self._on_subitem_updated)

        self.enable_wrong_way_protection = PermanentProperty(self.__class__.__name__ + ".enable_wrong_way_protection", True)
        self.enable_wrong_way_protection.attach_observer(self._on_subitem_updated)

        self.enable_snmp_upnp_protection = PermanentProperty(self.__class__.__name__ + ".enable_snmp_upnp_protection", True)
        self.enable_snmp_upnp_protection.attach_observer(self._on_subitem_updated)

        self.block_access_to_local_router = PermanentProperty(self.__class__.__name__ + ".block_access_to_local_router", True)
        self.block_access_to_local_router.attach_observer(self._on_subitem_updated)

        self.enable_ipv6_leak_protection = PermanentProperty(self.__class__.__name__ + ".enable_ipv6_leak_protection", True)
        self.enable_ipv6_leak_protection.attach_observer(self._on_subitem_updated)

        self.enable_deadrouting = PermanentProperty(self.__class__.__name__ + ".enable_deadrouting", True)
        self.enable_deadrouting.attach_observer(self._on_subitem_updated)

        self.enable_dnsleak_protection = PermanentProperty(self.__class__.__name__ + ".enable_dnsleak_protection", True )
        self.enable_dnsleak_protection.attach_observer(self._on_subitem_updated)
        self.enable_dnsleak_protection.attach_observer(self._set_default_enable_dnsleak_protection)

        self.use_custom_dns_servers = PermanentProperty(self.__class__.__name__ + ".use_custom_dns_servers", False )
        self.use_custom_dns_servers.attach_observer(self._on_subitem_updated)
        self.use_custom_dns_servers.attach_observer(self._set_default_use_custom_dns_servers)

        self.custom_dns_server_1        = PermanentProperty(self.__class__.__name__ + ".custom_dns_server_1", "")
        self.custom_dns_server_1.attach_observer(self._on_subitem_updated)

        self.custom_dns_server_2        = PermanentProperty(self.__class__.__name__ + ".custom_dns_server_2", "")
        self.custom_dns_server_2.attach_observer(self._on_subitem_updated)

    def _set_default_enable_dnsleak_protection(self,event):
        self.use_custom_dns_servers.set(False)

    def _set_default_use_custom_dns_servers(self,event):
        if self.use_custom_dns_servers.get() == False:
            self.custom_dns_server_1.set("")
            self.custom_dns_server_2.set("")

    def _on_subitem_updated(self, sender):
        self.notify_observers()


class Settings_Stealth(Observable):
    def __init__(self):
        super().__init__()
        self.stealth_method = PermanentProperty(self.__class__.__name__ + ".stealth_method", STEALTH_METHODS.no_stealth)
        self.stealth_method.attach_observer(self._on_subitem_updated)
        self.stealth_method.attach_observer(self._set_defaults_stealth_method)

        self.stealth_port = PermanentProperty(self.__class__.__name__ + ".stealth_port", "auto")
        self.stealth_port.attach_observer(self._on_subitem_updated)

        self.stealth_custom_node = PermanentProperty(self.__class__.__name__ + ".stealth_custom_node", False)
        self.stealth_custom_node.attach_observer(self._on_subitem_updated)
        self.stealth_custom_node.attach_observer(self._set_defaults_stealth_custom_node)

        self.stealth_custom_hostname = PermanentProperty(self.__class__.__name__ + ".stealth_custom_hostname", "")
        self.stealth_custom_hostname.attach_observer(self._on_subitem_updated)

        self.stealth_custom_port = PermanentProperty(self.__class__.__name__ + ".stealth_custom_port", "")
        self.stealth_custom_port.attach_observer(self._on_subitem_updated)

        self.stealth_custom_require_auth = PermanentProperty(self.__class__.__name__ + ".stealth_custom_require_auth", False)
        self.stealth_custom_require_auth.attach_observer(self._on_subitem_updated)
        self.stealth_custom_require_auth.attach_observer(self._set_defaults_stealth_custom_require_auth)

        self.stealth_custom_auth_username = PermanentProperty(self.__class__.__name__ + ".stealth_custom_auth_username", "")
        self.stealth_custom_auth_username.attach_observer(self._on_subitem_updated)

        self.stealth_custom_auth_password = PermanentProperty(self.__class__.__name__ + ".stealth_custom_auth_password", "")
        self.stealth_custom_auth_password.attach_observer(self._on_subitem_updated)

        self.stealth_custom_proxy_auth_use_ntlm = PermanentProperty(self.__class__.__name__ + ".stealth_custom_proxy_auth_use_ntlm", False)
        self.stealth_custom_proxy_auth_use_ntlm.attach_observer(self._on_subitem_updated)

        self.stealth_custom_ssh_fingerprint = PermanentProperty(self.__class__.__name__ + ".stealth_custom_ssh_fingerprint", False)
        self.stealth_custom_ssh_fingerprint.attach_observer(self._on_subitem_updated)

    def _set_defaults_stealth_method(self, event):
        if self.stealth_method.get() == STEALTH_METHODS.no_stealth:
            self.stealth_custom_node.set(False)
        if self.stealth_method.get() != STEALTH_METHODS.ssh:
            self.stealth_custom_ssh_fingerprint.set("")
            self.stealth_custom_require_auth.set(False)

    def _set_defaults_stealth_custom_node(self, event):
        if self.stealth_custom_node.get() is False:
            self.stealth_custom_hostname.set("")
            self.stealth_custom_port.set("")
            self.stealth_custom_require_auth.set(False)
            self.stealth_custom_ssh_fingerprint.set("")

    def _set_defaults_stealth_custom_require_auth(self, event):
        if self.stealth_custom_require_auth.get() is False:
            self.stealth_custom_auth_username.set("")
            self.stealth_custom_auth_password.set("")
            self.stealth_custom_proxy_auth_use_ntlm.set(False)

    def _on_subitem_updated(self, sender):
        self.notify_observers()


class Settings_Vpn_OpenVPN(Observable):
    def __init__(self):
        super().__init__()
        self.protocol = PermanentProperty(self.__class__.__name__ + ".protocol", OPENVPN_PROTOCOLS.udp)
        self.protocol.attach_observer(self._on_subitem_updated)

        self.cipher = PermanentProperty(self.__class__.__name__ + ".cipher", OPENVPN_CIPHER.aes_256_gcm)
        self.cipher.attach_observer(self._on_subitem_updated)

        self.driver = PermanentProperty(self.__class__.__name__ + ".driver", OPENVPN_DRIVER.wintun)
        self.driver.attach_observer(self._on_subitem_updated)

        self.tls_method = PermanentProperty(self.__class__.__name__ + ".tls_method", OPENVPN_TLS_METHOD.tls_crypt)
        self.tls_method.attach_observer(self._on_subitem_updated)

        self.port = PermanentProperty(self.__class__.__name__ + ".port", "auto")
        self.port.attach_observer(self._on_subitem_updated)

        self.cascading_max_hops = PermanentProperty(self.__class__.__name__ + ".cascading_max_hops", 2)
        self.cascading_max_hops.attach_observer(self._on_subitem_updated)

    def _on_subitem_updated(self, sender):
        self.notify_observers()


class Settings_Vpn_Ipsec(Observable):
    def __init__(self):
        super().__init__()

    def _on_subitem_updated(self, sender):
        self.notify_observers()


class Settings_Vpn(Observable):
    def __init__(self):
        super().__init__()

        self.vpn_protocol = PermanentProperty(self.__class__.__name__ + ".vpn_protocol",VPN_PROTOCOLS.openvpn)
        self.vpn_protocol.attach_observer(self._on_subitem_updated)

        self.openvpn = Settings_Vpn_OpenVPN()
        self.ipsec = Settings_Vpn_Ipsec()

    def _on_subitem_updated(self, sender):
        self.notify_observers()


class Settings_Account(Observable):
    def __init__(self):
        super().__init__()

        self.username         = PermanentProperty(self.__class__.__name__ + ".username", "")
        self.username.attach_observer(self._on_subitem_updated)

        self.password         = PermanentProperty(self.__class__.__name__ + ".password", "")
        self.password.attach_observer(self._on_subitem_updated)

        #self.account_expiry_date_utc    = PermanentProperty(self.__class__.__name__ + ".account_expiry_date_utc", None)
        #self.account_expiry_date_utc.attach_observer(self._on_subitem_updated)

        self.login_failed_count    = PermanentProperty(self.__class__.__name__ + ".login_failed_count", 0) # if username/password is wrong
        self.login_failed_count.attach_observer(self._on_subitem_updated)

    def _on_subitem_updated(self, sender):
        self.notify_observers()

    def logout(self):
        self.username.set("")
        self.password.set("")


class Settings_Startup(Observable):
    def __init__(self):
        super().__init__()
        self.start_on_boot         = PermanentProperty(self.__class__.__name__ + ".start_on_boot", True)
        self.start_on_boot.attach_observer(self._on_subitem_updated)
        #self.start_minimized       = PermanentProperty(self.__class__.__name__ + ".start_minimized", True)
        #self.start_minimized.attach_observer(self._on_subitem_updated)
        self.connect_on_start      = PermanentProperty(self.__class__.__name__ + ".connect_on_start", False)
        self.connect_on_start.attach_observer(self._on_subitem_updated)
        self.enable_background_mode = PermanentProperty(self.__class__.__name__ + ".enable_background_mode", False)
        self.enable_background_mode.attach_observer(self._on_subitem_updated)

    def _on_subitem_updated(self, sender):
        self.notify_observers()


class Settings(Observable):
    def __init__(self):
        super().__init__()
        self.leakprotection = Settings_Leakprotection()
        self.stealth = Settings_Stealth()
        self.vpn = Settings_Vpn()
        self.account = Settings_Account()
        self.startup = Settings_Startup()
        self.is_first_startup =  PermanentProperty(self.__class__.__name__ + ".is_first_startup", True)
        self.send_crashreports =  PermanentProperty(self.__class__.__name__ + ".send_crashreports", True)
        self.send_statistics =  PermanentProperty(self.__class__.__name__ + ".send_statistics", True)
        self.first_start_wizard_was_run = PermanentProperty(self.__class__.__name__ + ".first_start_wizard_was_run", False)
        self.first_start_wizard_was_run.attach_observer(self._on_subitem_updated)

        self.interface_level         = PermanentProperty(self.__class__.__name__ + ".interface_level", "simple")
        self.interface_level.attach_observer(self._on_subitem_updated)
        self.interface_level.attach_observer(self._on_interfacelevel_updated)

        self.installation_id         = PermanentProperty(self.__class__.__name__ + ".installation_id", "%s" % uuid.uuid4())
        self.language         = PermanentProperty(self.__class__.__name__ + ".language", "en")

        try:
            with open(os.path.join(Path.home(),".perfect_privacy.instid"), "r") as f:
                self.installation_id.set(f.read())
        except:
            with open(os.path.join(Path.home(),".perfect_privacy.instid"), "w") as f:
                f.write(self.installation_id.get())

    def _on_subitem_updated(self, sender ):
        self.notify_observers()

    def _on_interfacelevel_updated(self, sender):
        if self.interface_level.get() != "expert":
            self.vpn.openvpn.cipher.default()
            self.vpn.openvpn.tls_method.default()
            self.vpn.openvpn.driver.default()
            self.stealth.stealth_custom_node.default()
            self.leakprotection.allow_downloads_without_vpn.default()
            self.leakprotection.block_access_to_local_router.default()
            self.leakprotection.enable_deadrouting.default()
            self.leakprotection.enable_dnsleak_protection.default()
            self.leakprotection.enable_ipv6_leak_protection.default()
            self.leakprotection.enable_ms_leak_protection.default()
            self.leakprotection.enable_snmp_upnp_protection.default()
            self.leakprotection.enable_wrong_way_protection.default()
            self.leakprotection.use_custom_dns_servers.default()

            if self.interface_level.get() != "advanced":
                self.vpn.openvpn.cascading_max_hops.default()
                self.vpn.vpn_protocol.default()
                self.leakprotection.block_access_to_local_router.default()
                self.leakprotection.enable_dnsleak_protection.default()
                self.leakprotection.leakprotection_scope.default()
                self.stealth.stealth_port.default()
                self.stealth.stealth_method.default()

