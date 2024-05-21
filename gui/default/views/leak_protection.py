import time

from pyhtmlgui import PyHtmlView

from config.constants import PROTECTION_SCOPES, PLATFORMS
from config.config import PLATFORM
from gui.common.components import CheckboxComponent,SelectComponent,TextinputComponent

class LeakProtectionView(PyHtmlView):
    TEMPLATE_STR = '''        
    <div class="inner">
        <h1>{{_("Leak Protection")}}</h1>
        {% if pyview.subject.settings.interface_level.get()  == "simple" %}
            <div class="boxes">
                <section>
                    <h3>
                        {{_("Leak Protection Mode:")}}
                        <div class="input">
                            <label for="select_auto">  </label>
                            <select id="select_auto" disabled class="form-control">
                                <option value="auto"> AUTO </option>
                            </select>
                        </div>
                    </h3>
                    <div> {{_("In simple mode, leak protection is automatically managed for you")}}</div>
                </section>
            </div>
        {% else %}
            <p>{{_("Use these settings to protect against data leaks in case your VPN connection drops.")}}</p>
            <div class="boxes">
                <section>
                    <h3>
                        {{_("Leak Protection Scope:")}}
                         <!--- {{_("Disabled")}} , {{_("Tunnel")}} , {{_("Program")}} , {{_("Permanent")}} --->
                        <div class="input"> {{ pyview.firewall_scope.render() }} </div>    
                    </h3>
                    <div> {{_("Depending on your needs, you can choose how and when leak protection is activated for your system.")}}&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">{{_("more")}}</a>
                        <div class="tooltip" style="display:none">
                            {{_("<b>Tunnel:</b> In this mode, leak protection is only active when you are connected to the VPN. If you disconnect the VPN manually, leak protection is deactivated and you can access the internet without VPN.<br><b>Program:</b> In this mode, leak protection is always active as long as the VPN manager is running. If you disconnect the VPN, no program can access the internet until you establish a new connection.<br><b>Permanent:</b> In this mode, leak protection is always active, even when the VPN software is not running. This is useful for devices that should never send unencrypted traffic and should always use the VPN for internet connectivity.")}}
                        </div>
                    </div>
                </section>
            </div>
                
            {% if pyview.subject.settings.leakprotection.leakprotection_scope.get() != "disabled"  %}
                <span>{{_("You can also use the following specific settings to protect against leaks.")}} </span>
                <br>
                <h3>{{_("Details")}}</h3>
                <div class="boxes">                    
                    {% if pyview.subject.settings.interface_level.get()  == "expert" %}
                        <section> 
                            <h3>
                                {{_("Deadrouting")}}
                                <div class="input"> {{ pyview.enable_deadrouting.render() }} </div>
                            </h3> 
                            <div>
                                {{_("Deadrouting is a secondary routing-based protection layer in addition to the normal firewall.")}}&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">{{_("more")}}</a>
                                <div class="tooltip" style="display:none">
                                    {{_("Deadrouting adds a secondary security layer below the actual firewall that will capture all non VPN internet traffic that might escape the normal routing and firewalling.")}}
                                </div>
                            </div>
                        </section> 
                        
                        <section>
                            <h3>
                                {{_("Prevent Local IPv6 Exposure")}}
                                <div class="input"> {{ pyview.enable_ipv6_leak_protection.render() }} </div>                            
                            </h3> 
                            <div>
                                {{_("Prevent local apps from guessing parts of your public IPv6 address.")}}&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">{{_("more")}}</a>
                                <div class="tooltip" style="display:none">
                                    {{_("Depending on your network configuration, your local IPv6 may have the same prefix as your public Ipv6. This might allow local software like your browser or filesharing app to guess large parts of your public IP, even if no traffic actually leaks around the VPN. This protection will remove all public prefixed IPv6 from network interfaces and block IPv6 DHCP to prevent a new address from being assigned.")}}
                                </div>
                            </div>
                        </section> 
                        
                        <section>                         
                            <h3>
                                {{_("SNMP/UPnP Leak Protection")}}
                                <div class="input"> {{ pyview.enable_snmp_upnp_protection.render() }} </div>
                            </h3> 
                            <div>
                                {{_("Block SNMP/UPnP Ports.")}}&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">{{_("more")}}</a>
                                <div class="tooltip" style="display:none">
                                    {{_("Enabling this feature will prevent programs on your computer from accessing other devices via SNMP and UPnP protocols. This prevents potentially sensitive information, such as your public IP address, from being revealed to programs on your computer from other devices in your network. However, please note that blocking access to these protocols may also prevent certain programs or services from functioning properly.")}}
                                </div>
                            </div>
                        </section> 
                          
                        <section>
                            <h3>
                                {{_("Block access to local router")}}
                                <div class="input"> {{ pyview.block_access_to_local_router.render() }} </div>
                            </h3>
                            <div>
                                {{_("Prevent programs from determining your external IP address from your local Router.")}}
                                &nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">{{_("more")}}</a>
                                <div class="tooltip" style="display:none">
                                    {{_("This setting prevents programs from determining your external IP address through SMTP and XSS, which is possible with some routers.  Please note that access to network printers or hard drives connected to the router may also be blocked by the firewall")}}
                                </div>
                            </div>
                        </section>
                        
                        {% if pyview.PLATFORM == pyview.PLATFORMS.windows %}
                            <section>
                                <h3>
                                    {{_("Enable MS leak protection")}}
                                    <div class="input">{{ pyview.enable_ms_leak_protection.render() }} </div>
                                </h3> 
                                <div>
                                    {{_("Prevent the leak of your Windows login and password information.")}}
                                    &nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">{{_("more")}}</a>
                                    <div class="tooltip" style="display:none">
                                        {{_("If enabled, this feature protects against attacks that may leak your Windows login and password information. Our VPN Manager prevents the sending of login information to network shares over the internet, and Perfect Privacy servers block requests on port 445.")}}
                                    </div> 
                                </div>
                            </section>
                        
                            <section>
                                <h3>
                                    {{_("Prevent 'Wrong Way' Leak")}}
                                    <div class="input"> {{ pyview.enable_wrong_way_protection.render() }} </div>    
                                </h3> 
                                <div>
                                    {{_("Block the potential leak of your real IP address through a routing feature.")}}&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">{{_("more")}}</a>
                                    <div class="tooltip" style="display:none">
                                        {{_("There is a potential issue where packets received over the real IP may be answered via the VPN interface under certain conditions, potentially revealing your real IP address. Enable this feature to prevent this type of leak.")}}
                                    </div>
                                </div>
                            </section>          
                        {% endif %}  
 
                        <section>
                            <h3>
                                {{_("Prevent DNS Leaks")}}
                                <div class="input"> {{ pyview.enable_dnsleak_protection.render() }} </div>
                            </h3>
                            <div>
                                {{_("Ensure that you are using the VPN tunnel for Domain Name Service (DNS) requests.")}}&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">{{_("more")}}</a>
                                <div class="tooltip" style="display:none">
                                    {{_("DNS translates the domain name of a website into IP addresses, which is necessary to establish a connection to the server hosting the web page or service. A DNS leak occurs when you are using your provider's DNS server instead of the VPN tunnel or use a DNS server in your local network, bypassing the VPN.")}}
                                </div>
                            </div>
                        </section>
                    
                        {% if pyview.subject.settings.leakprotection.enable_dnsleak_protection.get() == true and pyview.subject.settings.interface_level.get()  == "expert" %}             
                            <section>
                                <h3>
                                    {{_("Custom DNS Servers")}}
                                    <div class="input"> {{ pyview.use_custom_dns_servers.render() }} </div>
                                </h3>
                                <div>
                                    {{_("You may want to use your own Nameservers instead of automatically selected Perfect Privacy Servers. Note that setting custom nameservers interfers with TrackStop. TrackStop might not work, or you custom servers might not be used.")}}  
                                </div>
                                {% if pyview.subject.settings.leakprotection.use_custom_dns_servers.get() == true %}
                                    <div style="width:45%;float:left;margin:10px;">
                                        {{pyview.custom_dns_server_1.render()}}
                                    </div>
                                    <div style="width:45%;float:left;margin:10px;">
                                        {{pyview.custom_dns_server_2.render()}}
                                    </div>
                                {% endif %}
                            </section>
                        {% endif %}
                        
                    {% endif %}		
                </div>
            {% endif %}
        {% endif %}
    </div>
    '''

    def __init__(self, subject, parent):
        '''
        :type subject : core.Core
        :param parent: gui.modern.components.mainview.MainView
        '''
        self._on_subject_updated = None # don't observe core, this is not needed
        super(LeakProtectionView, self).__init__(subject, parent)
        self.PLATFORM = PLATFORM
        self.PLATFORMS = PLATFORMS

        self.firewall_scope = SelectComponent(subject.settings.leakprotection.leakprotection_scope, self,
                                            options=[
                                                (PROTECTION_SCOPES.disabled , "Disabled" ),
                                                (PROTECTION_SCOPES.tunnel   , "Tunnel"   ),
                                                (PROTECTION_SCOPES.program  , "Program"),
                                                (PROTECTION_SCOPES.permanent, "Permanent"),
                                            ])
        #self.allow_downloads_without_vpn  = CheckboxComponent(subject.settings.leakprotection.allow_downloads_without_vpn , self, label="allow_downloads_without_vpn")
        self.enable_ms_leak_protection    = CheckboxComponent(subject.settings.leakprotection.enable_ms_leak_protection   , self)
        self.enable_wrong_way_protection  = CheckboxComponent(subject.settings.leakprotection.enable_wrong_way_protection , self)
        self.enable_snmp_upnp_protection  = CheckboxComponent(subject.settings.leakprotection.enable_snmp_upnp_protection , self)
        self.block_access_to_local_router = CheckboxComponent(subject.settings.leakprotection.block_access_to_local_router, self)
        self.enable_ipv6_leak_protection  = CheckboxComponent(subject.settings.leakprotection.enable_ipv6_leak_protection , self)
        self.enable_deadrouting           = CheckboxComponent(subject.settings.leakprotection.enable_deadrouting          , self)
        self.enable_dnsleak_protection    = CheckboxComponent(subject.settings.leakprotection.enable_dnsleak_protection   , self)
        self.use_custom_dns_servers       = CheckboxComponent(subject.settings.leakprotection.use_custom_dns_servers      , self)
        self.custom_dns_server_1          = TextinputComponent(subject.settings.leakprotection.custom_dns_server_1        , self, label="Nameserver 1")
        self.custom_dns_server_2          = TextinputComponent(subject.settings.leakprotection.custom_dns_server_2        , self, label="Nameserver 2")
        self.add_observable(subject.settings.leakprotection.enable_dnsleak_protection, self._on_object_updated)
        self.add_observable(subject.settings.leakprotection.use_custom_dns_servers, self._on_object_updated)
        self.add_observable(subject.settings.leakprotection.leakprotection_scope     , self._on_object_updated)

    def _on_object_updated(self, source, **kwargs):
        self.update()
