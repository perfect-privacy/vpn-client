from pyhtmlgui import PyHtmlView

from config.constants import PROTECTION_SCOPES, PLATFORMS
from config.config import PLATFORM
from gui.common.components import CheckboxComponent,SelectComponent,TextinputComponent

class LeakProtectionView(PyHtmlView):
    TEMPLATE_STR = '''        
        <div class="inner">
          <h1>Leak Protection</h1>
          {% if pyview.subject.settings.interface_level.get()  == "simple" %}
            <div class="boxes">
                <section>
                    <h3>
                        Leak Protection Mode:
                        <div class="input"> 
                        <label for="select_auto">  </label>
                        <select id="select_auto" disabled class="form-control">            
                            <option value="auto"> AUTO </option>
                         </select>
                        </div>    
                    </h3> 
                     <div> In simple mode, leak protection is automatically managed for you</div>
                </section>	    
            </div> 
          {% else %}
         
          
          
          <p>Use these settings to protect against data leaks in case your VPN connection drops.</p>
            <div class="boxes">
                <section>
                    <h3>
                        Leak Protection Scope:
                        <div class="input"> {{ pyview.firewall_scope.render() }} </div>    
                    </h3> 
                    <div> You can choose from three different security levels for leak protection: 
                    <a onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                    <div class="tooltip" style="display:none">
                        <b>Tunnel:</b> In this mode, leak protection is only active when you are connected to the VPN. If you disconnect the VPN manually, leak protection is deactivated and you can access the internet without VPN.
                        <br>
                        <b>Program:</b> In this mode, leak protection is always active as long as the VPN manager is running. If you disconnect the VPN, no program can access the internet until you establish a new connection.
                        <br>
                        <b>Permanent:</b> In this mode, leak protection is always active, even when the VPN software is not running. This is useful for devices that should never send unencrypted traffic and should always use the VPN for internet connectivity.
                    </div>
                </section>	    
            </div>  
                        
            {% if pyview.subject.settings.leakprotection.leakprotection_scope.get() != "disabled"  %}
                <span>You can also use the following specific settings to protect against leaks. </span>
                <br>
                
                {% if pyview.PLATFORM == pyview.PLATFORMS.windows %}
                    <h3>Details</h3>
                    <div class="boxes">
                    

                        <section>
                            <h3>
                                Block access to local router
                                <div class="input"> {{ pyview.block_access_to_local_router.render() }} </div>
                            </h3> 
                            <div>
                                Prevent programs from determining your external IP address 
                                <a onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                                <div class="tooltip" style="display:none">
                                    This setting prevents programs from determining your external IP address through SMTP and XSS, which is possible with some routers. Please note that access to network printers or hard drives connected to the router may also be blocked by the firewall
                                </div>
                        </section> 
                        
                        {% if pyview.subject.settings.interface_level.get()  == "expert" %}
                            <section> 
                                <h3>
                                    Deadrouting
                                    <div class="input"> {{ pyview.enable_deadrouting.render() }} </div>
                                </h3> 
                                <div>
                                    Deadrouting is a secondary routing-based protection. 
                                    <a onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                                    <div class="tooltip" style="display:none">
                                        There is a potential issue with virtual Hyper-V networking used by Windows Subsystem for Linux 2 (WSL2) whereby data packets can bypass the host's firewall. 
                                        This allows the virtual Hyper-V Ethernet adapter to send and receive all packets from the Linux guest without being checked by the Windows Firewall. In the lower layers of the Windows Filtering Platform (OSI layer 2), NATed packets are treated as normal Ethernet frames, which can also lead to a leak in Windows Sandbox or Docker if the guest uses Hyper-V for networking.
                                        To address this issue, we can redirect the route where the leak may occur to a non-existent IP address, effectively blocking the leak.
                                    </div>
                                </div>
                            </section> 
                            <section>
                                <h3>
                                    Enable MS leak protection
                                    <div class="input">{{ pyview.enable_ms_leak_protection.render() }} </div>
                                </h3> 
                                <div>
                                    Prevent the leak of your Windows login and password information
                                    <a onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                                    <div class="tooltip" style="display:none">
                                        If enabled, this feature protects against attacks that may leak your Windows login and password information. Our VPN Manager prevents the sending of login information to network shares over the internet, and Perfect Privacy servers block requests on port 445.
                                    </div> 
                                    
                                </div>
                            </section>
                            
                            <section>
                                <h3>
                                    Prevent "Wrong Way" Leak
                                    <div class="input"> {{ pyview.enable_wrong_way_protection.render() }} </div>    
                                </h3> 
                                <div>
                                    Block the potential leak of your real IP address through a routing feature. 
                                    <a onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                                    <div class="tooltip" style="display:none">
                                        There is a potential issue where packets received over the real IP may be answered via the VPN interface under certain conditions, potentially revealing your real IP address. Enable this feature to prevent this type of leak.
                                    </div>
                                </div>
                            </section>
                            
                            <section>                         
                                <h3>
                                    SNMP/UPnP Leak Protection
                                    <div class="input"> {{ pyview.enable_snmp_upnp_protection.render() }} </div>
                                </h3> 
                                <div>
                                    Block SNMP/UPnP access to local router
                                    <a onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                                    <div class="tooltip" style="display:none">
                                        Enabling this feature will prevent programs on your computer from accessing the local router through the SNMP and UPnP protocols. This prevents potentially sensitive information, such as your public IP address, from being revealed to programs on you computer. However, please note that blocking access to these protocols may also prevent certain programs or services from functioning properly.
                                    </div>
                                </div>
                            </section>            
                     
                            <section>
                                 <h3>
                                    Prevent IPv6 Leak
                                    <div class="input"> {{ pyview.enable_ipv6_leak_protection.render() }} </div>                            
                                </h3> 
                                <div>
                                    Prevent the leak of your public IP address assigned by your ISP through your local IPv6 address.
                                    <a onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                                    <div class="tooltip" style="display:none">
                                        If your ISP provides an IPv6 address, it is possible that it will assign your computer a local IPv6 address that includes your public IP address assigned by the ISP. Enable this option to prevent this type of leak.
                                    </div>
                                </div>
                                
                            </section> 
                                                                

                        {% endif %}    
                        <section>
                           <h3>
                                Prevent DNS Leak
                                <div class="input"> {{ pyview.enable_dnsleak_protection.render() }} </div>
                            </h3> 
                            <div>
                                Ensure that you are using the VPN tunnel for Domain Name Service (DNS) requests.
                                <a onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                                <div class="tooltip" style="display:none">
                                DNS translates the domain name of a website into IP addresses, which is necessary to establish a connection to the server hosting the web page or service. A DNS leak occurs when you are using your provider's DNS server instead of the VPN tunnel.
                                </div>    
                            </div>
                        </section>     
                        {% if pyview.subject.settings.leakprotection.enable_dnsleak_protection.get() == true and pyview.subject.settings.interface_level.get()  == "expert" %}             
                            <section>
                                <h3>
                                    Custom DNS Servers
                                    <div class="input"> {{ pyview.use_custom_dns_servers.render() }} </div>
                                </h3>  
                                <div>
                                   You may want to use your own DNS servers instead of automatically selected Perfect Privacy Servers. 
                                </div>
                                <div style="width:45%;float:left;margin:10px;">
                                    {{pyview.custom_dns_server_1.render()}}
                                </div>
                                <div style="width:45%;float:left;margin:10px;">
                                    {{pyview.custom_dns_server_2.render()}}
                                </div>
                                
                            </section>        
                        {% endif %}        
                    </div>	
                {% endif %}					
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
                                                (PROTECTION_SCOPES.program  , "Program"  ),
                                                (PROTECTION_SCOPES.tunnel   , "Tunnel"   ),
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
        self.add_observable(subject.settings.leakprotection.leakprotection_scope     , self._on_object_updated)


    def _on_object_updated(self, source, **kwargs):
        self.update()