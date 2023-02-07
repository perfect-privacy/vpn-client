from pyhtmlgui import PyHtmlView
from gui.common.components import CheckboxComponent, SelectComponent
from config.constants import VPN_PROTOCOLS, OPENVPN_CIPHER, OPENVPN_PROTOCOLS, OPENVPN_TLS_METHOD, OPENVPN_DRIVER, \
    PLATFORMS
from config.config import PLATFORM


class PreferencesView(PyHtmlView):
    TEMPLATE_STR = '''
    <div class="inner">
        <h1>Preferences</h1>
        <div class="boxes">
            <section>
                <h3>
                    Start with Windows
                    <div class="input"> {{ pyview.start_on_boot.render() }} </div>
                </h3>
                <div>If checked, the application will automatically start when you log into your computer.</div>
            </section>
        </div>   
        <h2>External IP</h2>
        <div class="boxes">
            <section>
                <h3>
                    NeuroRouting
                    <div class="input"> {{ pyview.neuro_routing.render() }} </div>
                </h3> 
                <div>
                    Your traffic will brought as close as possible to the destination within 
                    the encrypted VPN network. That way, your traffic is only exposed to the internet where it is unavoidable.
                </div>
            </section>

            {% if pyview.subject.settings.interface_level.get() != "simple" %}
                <section>
                    <h3>
                        Enforce Primary Ip
                        <div class="input"> {{ pyview.random_exit_ip.render() }} </div>
                    </h3> 
                    <div>There are services that require a primary IP address. Turn it on only when you need it.</div>
                </section>
            {% endif %}
        </div> 
        <h2>Connection</h2>
        {% if pyview.PLATFORM == pyview.PLATFORMS.windows %}
            <div class="boxes">
                <section>
                    <h3>
                        Connection Protocol
                        <div class="input">{{ pyview.vpn_protocol.render() }} </div>
                    </h3> 
                    <div>
                        IPsec (Internet Protocol Security) is a secure network protocol suite that authenticates and encrypts the packets of data sent over a network. 
                        OpenVPN is an open-source software application that implements virtual private network (VPN) techniques to create secure point-to-point or site-to-site 
                        connections in routed or bridged configurations and remote access facilities. Choose the protocol that best suits your needs.
                    </div>
                </section>	    
            </div>  
        {% endif %}
        {% if pyview.subject.settings.vpn.vpn_protocol.get() == pyview.VPN_PROTOCOLS.openvpn and  pyview.subject.settings.interface_level.get() != "simple" %}
            <h3>Connection Details</h3>
            <div class="boxes">

                <section>
                    <h3>
                        OpenVPN Protocol
                        <div class="input">{{ pyview.openvpn_protocol.render() }}</div>
                    </h3> 
                    <div>Phasellus convallis elit id ullam corper amet et pulvinar. Duis aliquam turpis mauris, sed ultricies erat dapibus.</div>
                </section>

                <section>
                    <h3>
                        Maximum Cascading Hops
                        <div class="input" style="width:5em;"> {{ pyview.openvpn_cascading_max_hops.render() }}</div>
                    </h3> 
                    <div>
                        Please note that increasing the number of hops may also increase the risk of connection failures and slower performance
                    </div>
                </section>                              

                {% if pyview.subject.settings.interface_level.get() == "expert" %}
                    <section>
                        <h3>
                            OpenVPN Encryption Cipher
                            <div class="input" style="width:8em;"> {{ pyview.openvpn_cipher.render() }} </div>    
                        </h3> 
                        <div>
                            Select the desired encryption cipher for your OpenVPN connection. 
                            Different ciphers have different strengths and weaknesses, so choose the one that best meets your security needs.
                        </div>
                    </section>

                    <section>
                        <h3>
                            TLS Method
                            <div class="input" style="width:8em;"> {{ pyview.openvpn_tls_method.render() }} </div>
                        </h3> 
                        <div>
                            Phasellus convallis elit id ullam corper amet et pulvinar. Duis aliquam turpis mauris, sed ultricies erat dapibus.
                        </div>
                    </section>

                    {% if pyview.PLATFORM == pyview.PLATFORMS.windows %}
                        <section> 
                            <h3>
                                OpenVPN Driver
                                <div class="input" style="width:8em;"> {{ pyview.openvpn_driver.render() }} </div>
                            </h3> 
                            <div>
                                Phasellus convallis elit id ullam corper amet et pulvinar. Duis aliquam turpis mauris, sed ultricies erat dapibus.
                            </div>
                        </section>
                    {% endif %}

                {% endif %}            
            </div>
        {% endif %}            
        {{ pyview.updater.render() }}
        {% if pyview.subject.settings.interface_level.get() == "expert" %}
            {% if pyview.openvpndriver %}
                {{ pyview.openvpndriver.render() }}
            {% endif %}       
            {% if pyview.deviceManager %}
                {{ pyview.deviceManager.render() }} 
            {% endif %}
        {% endif %}  

    </div>
    '''

    def __init__(self, subject, parent):
        """
        :type subject: core.Core
        :type parent: gui.default.components.mainview.MainView
        """
        self._on_subject_updated = None  # don't listen on core, not needed here
        super(PreferencesView, self).__init__(subject, parent)
        self.VPN_PROTOCOLS = VPN_PROTOCOLS
        self.PLATFORM = PLATFORM
        self.PLATFORMS = PLATFORMS
        self.vpn_protocol = SelectComponent(subject.settings.vpn.vpn_protocol, self,
                                            options=[
                                                (VPN_PROTOCOLS.openvpn, "OpenVPN"),
                                                (VPN_PROTOCOLS.ipsec, "IPSEC"),
                                            ])

        self.add_observable(subject.settings.vpn.vpn_protocol, self._on_object_updated)
        self.openvpn_cipher = SelectComponent(subject.settings.vpn.openvpn.cipher, self,
                                              options=[
                                                  (OPENVPN_CIPHER.aes_128_gcm, OPENVPN_CIPHER.aes_128_gcm),
                                                  (OPENVPN_CIPHER.aes_256_gcm, OPENVPN_CIPHER.aes_256_gcm),
                                                  (OPENVPN_CIPHER.aes_128_cbc, OPENVPN_CIPHER.aes_128_cbc),
                                                  (OPENVPN_CIPHER.aes_256_cbc, OPENVPN_CIPHER.aes_256_cbc),
                                              ])
        self.openvpn_protocol = SelectComponent(subject.settings.vpn.openvpn.protocol, self,
                                                options=[
                                                    (OPENVPN_PROTOCOLS.tcp, "TCP"),
                                                    (OPENVPN_PROTOCOLS.udp, "UDP"),
                                                ])

        self.openvpn_tls_method = SelectComponent(subject.settings.vpn.openvpn.tls_method, self,
                                                  options=[
                                                      (OPENVPN_TLS_METHOD.tls_crypt, "TLS CRYPT"),
                                                      (OPENVPN_TLS_METHOD.tls_auth, "TLS AUTH"),
                                                  ])

        self.openvpn_cascading_max_hops = SelectComponent(subject.settings.vpn.openvpn.cascading_max_hops, self,
                                                          options=[
                                                              (1, 1),
                                                              (2, 2),
                                                              (3, 3),
                                                              (4, 4),
                                                          ])
        self.openvpn_driver = SelectComponent(subject.settings.vpn.openvpn.driver, self,
                                              options=[
                                                  (OPENVPN_DRIVER.wintun, "WinTUN"),
                                                  (OPENVPN_DRIVER.tap_windows6_latest, "TAP 9.24.6.601"),
                                                  (OPENVPN_DRIVER.tap_windows6_9_00_00_9, "TAP 9.0.0.9"),
                                                  (OPENVPN_DRIVER.tap_windows6_9_00_00_21, "TAP 9.0.0.21"),
                                              ])
        self.random_exit_ip = CheckboxComponent(subject.userapi.random_exit_ip, self, label="")
        self.neuro_routing = CheckboxComponent(subject.userapi.neuro_routing, self, label="")
        self.start_on_boot = CheckboxComponent(subject.settings.startup.start_on_boot, self)
        self.updater = UpdaterView(subject, self)
        if PLATFORM == PLATFORMS.windows:
            self.openvpndriver = StatusOpenVpnDriverView(subject.openVpnDriver, self)
            self.deviceManager = StatusNetworkDevicesView(subject.deviceManager, self)

    def _on_object_updated(self, source, **kwargs):
        self.update()


class UpdaterView(PyHtmlView):
    TEMPLATE_STR = '''
    <div class="boxes">
        <section>
            <h3>Updates
            <span class="input" style="width:20em"> 
                <label></label>
                <button onclick='pyview.check_now()'> Check now </button>
                {% if pyview.subject.softwareUpdater.state.get() == "READY_FOR_INSTALL" and pyview.subject.session.state.get() == "idle" %}
                    <button onclick='run_updates()'> update now</button>
                {% endif %}
            </span>
            </h3>
            <table class="table">
                <thead>
                    <tr>
                        <th scope="col">  </th>
                        <th scope="col"> Installed Version </th>
                        <th scope="col"> Available Version </th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td> Software </td>
                        <td> {{ pyview.subject.softwareUpdater.version_local }} </td>
                        <td> {{ pyview.subject.softwareUpdater.version_online }} </td>
                        <td> {{ pyview.subject.softwareUpdater.state.get() }}  </td>
                    </tr>
                    <tr>
                        <td> Config </td>
                        <td> {{ pyview.subject.configUpdater.version_local }} </td>
                        <td> {{ pyview.subject.configUpdater.version_online }} </td>
                        <td> {{ pyview.subject.configUpdater.state.get() }} </td>
                    </tr>                        

                </tbody>
            </table>
        </section>
    </div>
    '''

    def __init__(self, subject, parent):
        super(UpdaterView, self).__init__(subject, parent)
        self.add_observable(subject.softwareUpdater, self._on_subject_updated)
        self.add_observable(subject.softwareUpdater.state, self._on_subject_updated)
        self.add_observable(subject.configUpdater, self._on_subject_updated)
        self.add_observable(subject.configUpdater.state, self._on_subject_updated)
        self.add_observable(subject.session.state, self._on_subject_updated)

    def check_now(self):
        self.subject.softwareUpdater.check_now()
        self.subject.configUpdater.check_now()

    def update_now(self):
        self.subject.start_updater()


class StatusOpenVpnDriverView(PyHtmlView):
    TEMPLATE_STR = '''
    <div class="boxes">
        <section>
            <h3>Network drivers
                <span class="input" style="width:20em;"> 
                    <label></label>
                    {% if pyview.subject.state.get() == "IDLE" %}
                        <button onclick='pyview.subject.reinstall()'> Reinstall </button>
                    {% else %}
                        {{ pyview.subject.state.get() }}
                    {% endif %}
                </span>
            </h3>
            <table class="table">
                <thead>
                    <tr>
                        <th scope="col"> Driver </th>
                        <th scope="col"> Installed Version </th>
                        <th scope="col"> Available Version </th>
                    </tr>
                </thead>
                <tbody>
                        <tr>
                            <td> Wintun </td>
                            <td> 
                                {% for installed_driver in pyview.subject.wintun.installed_drivers %}
                                    {{ installed_driver.version_date }} {{ installed_driver.version_number }} <br>
                                {% endfor %}   
                            </td>
                            <td> {{ pyview.subject.wintun.available_version_date }} {{ pyview.subject.wintun.available_version_number }} </td>
                        </tr>  
                        <tr>
                            <td> TapWindows </td>
                            <td> 
                                {% for installed_driver in pyview.subject.tapwindows.installed_drivers %}
                                    {{ installed_driver.version_date }} {{ installed_driver.version_number }} <br>
                                {% endfor  %}
                            </td>
                            <td> {{ pyview.subject.tapwindows.available_version_date }} {{ pyview.subject.tapwindows.available_version_number }} </td>
                        </tr>
                </tbody>
            </table>
        </section>
    </div>
    '''

    def __init__(self, subject, parent):
        super(StatusOpenVpnDriverView, self).__init__(subject, parent)
        self.add_observable(subject.state, self._on_subject_updated)


class StatusNetworkDevicesView(PyHtmlView):
    TEMPLATE_STR = '''
    <div class="boxes">
        <section>
            <h3>Network devices
                <span class="input" style="width:20em;"> 
                    <label></label>
                    {% if pyview.subject.state.get() == "IDLE" %}
                        <button onclick='pyview.subject.reinstall()'> Reinstall </button>
                    {% else %}
                        {{ pyview.subject.state.get() }}
                    {% endif %}
                </span>
            </h3>
            <table class="table">
                <thead>
                    <tr>
                        <th scope="col"> Name </th>
                        <th scope="col"> Type </th>
                        <th scope="col"> Uid </th>
                    </tr>
                </thead>
                <tbody>
                    {% for wintun_device in pyview.subject.wintun_devices %}
                        <tr>
                            <td> {{ wintun_device.name }} </td>
                            <td> {{ wintun_device.type }} </td>
                            <td> {{ wintun_device.guid }} </td>
                        </tr>
                    {% endfor  %}
                    {% for tapwindows_device in pyview.subject.tapwindows_devices %}
                        <tr>
                            <td> {{ tapwindows_device.name }} </td>
                            <td> {{ tapwindows_device.type }} </td>
                            <td> {{ tapwindows_device.guid }} </td>
                        </tr>
                    {% endfor  %}
                </tbody>
            </table>
        </section>
    </div>
    '''

    def __init__(self, subject, parent):
        super(StatusNetworkDevicesView, self).__init__(subject, parent)
        self.add_observable(subject.state, self._on_subject_updated)