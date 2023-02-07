from pyhtmlgui import PyHtmlView

from .settings_vpn_openvpn import Settings_vpn_openvpn
from .settings_neurorouting import Settings_neurorouting
from .settings_stealth import Settings_stealth
from .settings_trackstop import Settings_trackstop
from .settings_wlanaccesspoint import Settings_wlan_accesspoint
from .settings_wlanclient import Settings_wlan_client
from .settings_smartnet import Settings_smartnet
from .settings_account import Settings_account

from .settings_expert import Settings_expert

class Settings_more(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="row h-1of6" >
            Settings page2
        </div>


        <div class="row h-1of3">

            <div class="col-4 tile" onclick='pyhtmlgui.call(pyview.open_settings_vpn_openvpn)'>
               openvpn
            </div>
            
            <div class="col-4 tile" onclick='pyhtmlgui.call(pyview.open_settings_smartnet)'>
                Smartnet
            </div>
            
            <div class="col-4">
            </div>
            
        </div>

        <div class="row h-1of3">

        </div>

        <div class="row h-1of6">
            <div class="col-4 bottom_tile" onclick = 'pyhtmlgui.call(pyview.on_back)'>
                 <h3 class="verticalcenter"><img class="bottom_row_icons" src="/static/img/footer/back.png" alt="back icon"> Back</h3>  
            </div>

            <div class="col-4">
            </div>

            <div class="col-4 bottom_tile"  onclick = 'pyhtmlgui.call(pyview.open_settings_expert)'>
                Expert
            </div>
        </div>
    '''

    def __init__(self, subject, parent, on_back, **kwargs):
        super(Settings_more, self).__init__(subject, parent)
        self.settings_vpn_openvpn       = Settings_vpn_openvpn(     subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_wlan_accesspoint  = Settings_wlan_accesspoint(subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_wlan_client       = Settings_wlan_client(     subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_neurorouting      = Settings_neurorouting(    subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_stealth           = Settings_stealth(         subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_trackstop         = Settings_trackstop(       subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_trackstop         = Settings_trackstop(       subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_smartnet          = Settings_smartnet(        subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_account           = Settings_account(         subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_expert            = Settings_expert(          subject, self, on_back=self.on_subsetting_exited, **kwargs)

        self.on_back = on_back

    def open_settings_vpn_openvpn(self):
        self.set_currentpage(self.settings_vpn_openvpn)

    def open_settings_wlan_accesspoint(self):
        self.set_currentpage(self.settings_wlan_accesspoint)

    def open_settings_wlan_client(self):
        self.set_currentpage(self.settings_wlan_client)

    def open_settings_neurorouting(self):
        self.set_currentpage(self.settings_neurorouting)

    def open_settings_stealth(self):
        self.set_currentpage(self.settings_stealth)

    def open_settings_trackstop(self):
        self.set_currentpage(self.settings_trackstop)

    def open_settings_smartnet(self):
        self.set_currentpage(self.settings_smartnet)

    def open_settings_account(self):
        self.set_currentpage(self.settings_account)

    def open_settings_expert(self):
        self.set_currentpage(self.settings_expert)

    def set_currentpage(self, new_page):
        self.parent.set_currentpage(new_page)

    def on_subsetting_exited(self):
        self.parent.set_currentpage(self)
