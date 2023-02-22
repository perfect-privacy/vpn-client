from pyhtmlgui import PyHtmlView

from config.config import PLATFORM
from gui.common.components import CheckboxComponent, SelectComponent, TextinputComponent
from config.constants import STEALTH_METHODS, STEALTH_PORTS, VPN_PROTOCOLS, OPENVPN_TLS_METHOD, PLATFORMS


class StealthView(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="inner">
            <h1>Stealth</h1>
            <p>
Stealth VPN is designed to obfuscate your VPN traffic, making it difficult to block for network administrators or ISPs. When enabled, stealth VPN  uses encryption and obfuscation techniques to scramble your VPN traffic and make it difficult to identify as such.            </p>
        
            {% if pyview.subject.settings.vpn.vpn_protocol.get() == pyview.VPN_PROTOCOLS.openvpn %}
                <div class="boxes">
                    <section>
                        <h3>
                            Select Stealth Method
                            <div class="input"> {{ pyview.stealth_method.render() }} </div>
                        </h3>
                        <div>Choose a stealth method to obfuscate your VPN traffic</div>
                    </section>
                    {% if pyview.subject.settings.stealth.stealth_method.get() !=  pyview.STEALTH_METHODS.no_stealth %}
                        {% if pyview.subject.settings.stealth.stealth_custom_node.get() == False %}
                            <section>
                                <h3>
                                    Stealth Port
                                    <div class="input"> {{ pyview.stealth_port.render() }} </div>
                                </h3>
                                <div>Choose a port to use for the stealth VPN connection. Different ports may be more or less likely to be detected and blocked by network administrators or ISPs</div>
                            </section>
                        {% endif %}
                        {% if pyview.subject.settings.interface_level.get()  == "expert" %}
                            {% if pyview.subject.settings.stealth.stealth_method.get() !=  pyview.STEALTH_METHODS.obfs and pyview.subject.settings.stealth.stealth_method.get() !=  pyview.STEALTH_METHODS.stunnel %}
                                <section>
                                    
                                    <h3>
                                        Use Custom Stealth Node
                                        <div class="input"> {{ pyview.stealth_custom_node.render() }} </div>
                                    </h3>
                                    <div>Enable this option to specify a custom host or IP to use as a stealth tunneling node for your VPN traffic.</div>
                                </section>
            
                                {% if pyview.subject.settings.stealth.stealth_custom_node.get() == True %}
                                    <section>
                                        <div class="input">
                                            Host:{{ pyview.stealth_custom_hostname.render() }}
                                            Port:{{ pyview.stealth_custom_port.render() }}
                                        </div>
                                        <h3>Custom Tunneling Node Host and Port</h3>
                                        <div> Specify a custom host and port to use as the stealth tunneling node for your VPN traffic</div>
                                    </section>
            
                                    <section>
                                        <h3>
                                            Use Authentication for Tunneling Node
                                            <div class="input"> {{ pyview.stealth_custom_require_auth.render() }}  </div>
                                        </h3>
                                        <p>Enable this option to specify authentication credentials for the custom tunneling node. This may be required if the custom tunneling node requires authentication to establish a connection</p>
                                    </section>
            
                                    {% if pyview.subject.settings.stealth.stealth_custom_require_auth.get() ==  True %}
                                        <section>
                                            <div class="input">
                                                Username:{{ pyview.stealth_custom_auth_username.render() }}
                                                Password:{{ pyview.stealth_custom_auth_password.render() }}
                                                {% if pyview.subject.settings.stealth.stealth_method.get() ==  pyview.STEALTH_METHODS.ssh %}
                                                    Fingerprint{{ pyview.stealth_custom_ssh_fingerprint.render() }}
                                                {% endif %}
                                            </div>
                                            <h3>Username/password</h3>
                                            <p>Protect yourself by activating this filter and blocking over 30.000 tracking and advertisement domains.</p>
                                            {% if pyview.subject.settings.stealth.stealth_method.get() ==  pyview.STEALTH_METHODS.http %}
                                                NTLM Auth: {{ pyview.stealth_custom_proxy_auth_use_ntlm.render() }}
                                            {% endif %}
                                        </section>
                                    {% endif %}
                                {% endif %}
                            {% endif %}
                        {% endif %}
                    {% endif %}
                </div>
            {% endif %}
        </div>	
    '''

    def __init__(self, subject, parent):
        """
        :type subject: core.Core
        :type parent:  gui.default.components.settings_vpn.SettingsVpnView
        """
        super(StealthView, self).__init__(subject, parent)
        self.STEALTH_METHODS = STEALTH_METHODS  # make available in template
        self.VPN_PROTOCOLS = VPN_PROTOCOLS
        options = [
             (STEALTH_METHODS.no_stealth, "No Stealth"),
             (STEALTH_METHODS.stunnel   , "Stunnel"),
             (STEALTH_METHODS.socks     , "Socks"),
             (STEALTH_METHODS.http      , "HTTP"),
             (STEALTH_METHODS.obfs      , "OBFS"),
        ]
        if PLATFORM == PLATFORMS.windows:
            options.append((STEALTH_METHODS.ssh, "SSH"))
        self.stealth_method = SelectComponent(subject.settings.stealth.stealth_method, self, options=options)
        self.add_observable(self.subject.settings.stealth.stealth_method, self._on_stealth_method_changed)

        self.stealth_port = SelectComponent(subject.settings.stealth.stealth_port, self,
                                                options=[],
                                                label="")
        self.set_stealth_port_options()

        self.stealth_custom_node = CheckboxComponent(subject.settings.stealth.stealth_custom_node, self, label="")
        self.add_observable(self.subject.settings.stealth.stealth_custom_node, self._on_subject_updated)
        self.add_observable(subject.settings.vpn.vpn_protocol, self._on_subject_updated)
        self.add_observable(subject.settings.vpn.openvpn.tls_method, self._on_stealth_method_changed)

        self.stealth_custom_hostname = TextinputComponent(subject.settings.stealth.stealth_custom_hostname, self,label="")
        self.stealth_custom_port = TextinputComponent(subject.settings.stealth.stealth_custom_port, self,label="")
        self.stealth_custom_require_auth = CheckboxComponent(subject.settings.stealth.stealth_custom_require_auth, self, label="")
        self.add_observable(self.subject.settings.stealth.stealth_custom_require_auth, self._on_subject_updated)
        self.stealth_custom_auth_username = TextinputComponent(subject.settings.stealth.stealth_custom_auth_username, self,label="")
        self.stealth_custom_auth_password = TextinputComponent(subject.settings.stealth.stealth_custom_auth_password, self,label="")
        self.stealth_custom_ssh_fingerprint = TextinputComponent(subject.settings.stealth.stealth_custom_ssh_fingerprint, self,label="")
        self.stealth_custom_proxy_auth_use_ntlm = CheckboxComponent(subject.settings.stealth.stealth_custom_proxy_auth_use_ntlm, self, label="")

    def _on_stealth_method_changed(self, sender):
        self.subject.settings.stealth.stealth_port.set("auto")
        self.set_stealth_port_options()
        self.update()

    def set_stealth_port_options(self):
        if self.subject.settings.stealth.stealth_method.get() == STEALTH_METHODS.ssh:
            self.stealth_port.options = [( "auto", "auto") ] + [(x,x) for x in STEALTH_PORTS.ssh]
        if self.subject.settings.stealth.stealth_method.get() == STEALTH_METHODS.obfs:
            if self.subject.settings.vpn.openvpn.tls_method.get() == OPENVPN_TLS_METHOD.tls_crypt:
                self.stealth_port.options = [("auto", "auto")] + [(x, x) for x in STEALTH_PORTS.obfs_tlscrypt]
            else:
                self.stealth_port.options = [( "auto", "auto") ] + [(x,x) for x in STEALTH_PORTS.obfs]
        if self.subject.settings.stealth.stealth_method.get() == STEALTH_METHODS.stunnel:
            if self.subject.settings.vpn.openvpn.tls_method.get() == OPENVPN_TLS_METHOD.tls_crypt:
                self.stealth_port.options = [( "auto", "auto") ] + [(x,x) for x in STEALTH_PORTS.stunnel_tlscrypt]
            else:
                self.stealth_port.options = [("auto", "auto")] + [(x, x) for x in STEALTH_PORTS.stunnel]
        if self.subject.settings.stealth.stealth_method.get() == STEALTH_METHODS.socks:
            self.stealth_port.options = [( "auto", "auto") ] + [(x,x) for x in STEALTH_PORTS.socks]
        if self.subject.settings.stealth.stealth_method.get() == STEALTH_METHODS.http:
            self.stealth_port.options = [( "auto", "auto") ] + [(x,x) for x in STEALTH_PORTS.http]
        if self.subject.settings.stealth.stealth_method.get() == STEALTH_METHODS.no_stealth:
            self.stealth_port.options = [( "auto", "auto") ]
