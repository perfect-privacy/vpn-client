import time

from pyhtmlgui import PyHtmlView
from gui.common.components import CheckboxComponent, SelectComponent
from config.constants import VPN_PROTOCOLS, OPENVPN_CIPHER, OPENVPN_PROTOCOLS, OPENVPN_TLS_METHOD, OPENVPN_DRIVER, \
    PLATFORMS, OPENVPN_PORTS
from config.config import PLATFORM


class PreferencesView(PyHtmlView):
    TEMPLATE_STR = '''
    <div class="inner">
        <h1>Preferences</h1>
        <div class="boxes">
            <section>
                <h3>
                    Start with {{pyview.osname}}
                    <div class="input"> {{ pyview.start_on_boot.render() }} </div>
                </h3>
                <div>If checked, the application will automatically start when you log into your computer.</div>
            </section>
            <section>
                <h3>
                    Connect on start
                    <div class="input"> {{ pyview.connect_on_start.render() }} </div>
                </h3>
                <div>
                    Automatically connect to VPN if Perfect Privacy App is started{% if pyview.subject.settings.interface_level.get() == "expert" %} or directly after boot if background mode is active{% endif %}.
                </div>
            </section>
            {% if pyview.subject.settings.interface_level.get() == "expert" %}
                <section>
                    <h3>
                        Background Mode
                        <div class="input"> {{ pyview.enable_background_mode.render() }} </div>
                    </h3>
                    <div>
                        If background mode is enabled, 
                        all your VPN connections can be active even if the Perfect Privacy App is not running.&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                        <div class="tooltip" style="display:none">
                           Use this to hide your VPN App usage from screen, 
                           or to automatically connect all users to the vpn after boot, 
                           without them even seeing the App. "Start with OS" is not needed for background mode, 
                           as this will only start the frontend App. 
                           The background service will always start after boot.
                        </div>
                    </div>
                </section>

            {% endif %}
            
        </div>   
        <h2>External IP</h2>
        Note: It might take up to 3 minutes for any changes to apply on our Servers. 
        If you update your external ip settings on our website, it might take some time for the settings below to refresh. <a onclick="pyview.refresh()">Refresh Now</a> 

        <div class="boxes">
            <section>
                <h3>
                    NeuroRouting
                    <div class="input"> {{ pyview.neuro_routing.render() }} </div>
                </h3> 
                <div>
                    Use our AI-driven routing technology to keep your internet traffic within our encrypted network wherever possible. This makes sure your traffic is only routed 
                    though the open internet for as short as possible, making it way harder to do any kind of traffic analysis.  
                </div>
            </section>

            {% if pyview.subject.settings.interface_level.get() != "simple" %}
                <section>
                    <h3>
                        Enforce Primary Ip
                        <div class="input"> {{ pyview.enforce_primary_ip.render() }} </div>
                    </h3> 
                    <div>Make sure servers primary ip address is used as exit ip. Otherwise a random IP will be assigned.</div>
                </section>
            {% endif %}
        </div> 
        {% if (pyview.subject.settings.vpn.vpn_protocol.get() == pyview.VPN_PROTOCOLS.openvpn and  pyview.subject.settings.interface_level.get() != "simple" ) or pyview.PLATFORM == pyview.PLATFORMS.windows %}
            <h2>Connection</h2>
        {% endif %}
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
                    <div>
                        Select OpenVPN protocol, UDP is recommended in most cases, however in some networks TCP might work more reliable. TCP is automatically used if stealth is enabled.  
                    </div>
                </section>

                <section>
                    <h3>
                        Maximum Cascading Hops
                        <div class="input" style="width:5em;"> {{ pyview.openvpn_cascading_max_hops.render() }}</div>
                    </h3> 
                    <div>
                        Select the maximum number of available hops for cascading connections. 
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
                            OpenVPN Port
                            <div class="input" style="width:8em;"> {{ pyview.openvpn_port.render() }} </div>    
                        </h3> 
                        <div>
                            Select the desired port for your OpenVPN connection.
                        </div>
                    </section>

                    <section>
                        <h3>
                            TLS Method
                            <div class="input" style="width:8em;"> {{ pyview.openvpn_tls_method.render() }} </div>
                        </h3> 
                        <div>
                           Select prefered OpenVPN TLS Method. TLS-CRYPT is the newer, recommended way. 
                        </div>
                    </section>

                    {% if pyview.PLATFORM == pyview.PLATFORMS.windows %}
                        <section> 
                            <h3>
                                OpenVPN Driver
                                <div class="input" style="width:8em;"> {{ pyview.openvpn_driver.render() }} </div>
                            </h3> 
                            <div>
                                Select OpenVPN Driver. WinTUN is the newest, fastest OpenVPN driver, but some older Windows version might need some older driver. 
                            </div>
                        </section>
                    {% endif %}

                {% endif %}            
            </div>
        {% endif %}
        
        <h2>Updates</h2>
        {{ pyview.updater.render() }}
        
        {% if pyview.subject.settings.interface_level.get() == "expert" and pyview.PLATFORM == pyview.PLATFORMS.windows %}
            <h2>OpenVPN Driver</h2>
            {% if pyview.openvpndriver %}
                {{ pyview.openvpndriver.render() }}
            {% endif %}       
            {% if pyview.deviceManager %}
                {{ pyview.deviceManager.render() }} 
            {% endif %}
        {% endif %}  
        
        
        <h2>Help our community</h2>
        <div class="boxes">
            <section> 
                <h3>
                    Automatically send crash reports
                    <div class="input" style="width:8em;"> {{ pyview.send_crashreports.render() }} </div>
                </h3> 
                <div>
                    We, and all other users, would greatly appreciate if you keep this option active. If our VPN client, 
                    or some background component like leak protection crashes on your system, 
                    it might behave incorrectly for users whose life and liberty depends on a functioning VPN.&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                    <div class="tooltip" style="display:none">
                        Crash reports include the client version, installation ID, the OS, and the actual internal python stack trace of the crash.
                        They do not contain any of the bullshit information that causes us all to hate and block telemetry and is not assigned to a IP/User/Account or anything else. 
                    </div>
                </div>
            </section>
            <section> 
                <h3>
                    Automatically report local settings
                    <div class="input" style="width:8em;"> {{ pyview.send_statistics.render() }} </div>
                </h3> 
                <div>
                    This option helps us collect statistics about the actually used VPN settings, stealth options and openvpn drivers.
                    It does not collect any system information except your operating system (Windows, Mac, Linux).&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                    <div class="tooltip" style="display:none">
                        Statistics include the following information and nothing else:<br> 
                        Client version, OS (without exact version), interface level (simple,advanced, expert), leak protection settings, 
                        stealth settings (without private nodes), vpn protocol, openvpn driver, tls method, port, max cascading hops, 
                        the actual number of hops used, if you have an Ipv4, if you have an Ipv6 and if you are connected to the VPN.<br>
                        Reports are not assigned to a IP/User/Account/Installation or anything else (As you might expect from our service).
                        Statistics are only collected once approximatly every 500 days. 
                    </div>
                </div>
            </section>      
        </div>
        
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
        self.add_observable(subject.settings.vpn.openvpn.protocol, self._on_object_updated)
        self.add_observable(subject.settings.vpn.openvpn.tls_method, self._on_object_updated)
        self.add_observable(subject.settings.startup.enable_background_mode, self._on_object_updated)
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

        self.openvpn_port = SelectComponent(subject.settings.vpn.openvpn.port, self,
                                            options=[],
                                            label="")
        self.enforce_primary_ip = CheckboxComponent(subject.userapi.random_exit_ip, self, label="", inverted=True)
        self.neuro_routing = CheckboxComponent(subject.userapi.neuro_routing, self, label="")
        self.start_on_boot = CheckboxComponent(subject.settings.startup.start_on_boot, self)
        #self.connect_on_start = CheckboxComponent(subject.settings.startup.connect_on_start, self)
        self.enable_background_mode = CheckboxComponent(subject.settings.startup.enable_background_mode, self)
        self.connect_on_start = CheckboxComponent(subject.settings.startup.connect_on_start, self)


        self.send_crashreports = CheckboxComponent(subject.settings.send_crashreports, self)
        self.send_statistics = CheckboxComponent(subject.settings.send_statistics, self)
        self.updater = UpdaterView(subject, self)

        self.osname = ""
        if PLATFORM == PLATFORMS.windows:
            self.openvpndriver = StatusOpenVpnDriverView(subject.openVpnDriver, self)
            self.deviceManager = StatusNetworkDevicesView(subject.deviceManager, self)
            self.osname = "Windows"
        if PLATFORM == PLATFORMS.macos:
            self.osname = "macOS"
        self._last_update_requested = 0
        self.set_openvpn_port_options()

    def _on_object_updated(self, source, **kwargs):
        self.set_openvpn_port_options()
        self.update()

    def refresh(self):
        if self._last_update_requested + 3 > time.time():
            return
        self._last_update_requested = time.time()
        self.subject.userapi.request_update()

    def set_openvpn_port_options(self):
        if self.subject.settings.vpn.openvpn.tls_method.get() == OPENVPN_TLS_METHOD.tls_crypt:
            if self.subject.settings.vpn.openvpn.protocol.get() == OPENVPN_PROTOCOLS.udp:
                ports = OPENVPN_PORTS.TLSCRYPT.udp
            else:
                ports = OPENVPN_PORTS.TLSCRYPT.tcp
        else:
            if self.subject.settings.vpn.openvpn.protocol.get() == OPENVPN_PROTOCOLS.udp:
                ports = OPENVPN_PORTS.TLSAUTH.udp
            else:
                ports = OPENVPN_PORTS.TLSAUTH.tcp
        self.openvpn_port.options = [("auto", "auto")] + [(x, x) for x in ports]
        if self.subject.settings.vpn.openvpn.port.get() not in ports:
            self.subject.settings.vpn.openvpn.port.set("auto")

class UpdaterView(PyHtmlView):
    TEMPLATE_STR = '''
    <div class="boxes">
        <section>
            <h3>Updates
            <span class="input" style="width:20em"> 
                <label></label>
                <button onclick='pyview.check_now()'> Check now </button>
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