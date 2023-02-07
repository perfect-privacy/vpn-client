from pyhtmlgui import PyHtmlView

from .settings_account import Settings_account
from .settings_wlanaccesspoint import Settings_wlan_accesspoint
from .settings_wlanclient import Settings_wlan_client
from .settings_stealth import  Settings_stealth
from .settings_neurorouting import Settings_neurorouting
from .settings_trackstop import  Settings_trackstop
from .settings_smartnet import Settings_smartnet
from .settings_vpn_openvpn import Settings_vpn_openvpn

from .settings_more import Settings_more


class Settings(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="row h-3of12" >
            <div class="col-4 tile" onclick='pyview.open_settings_account()'>
                <div class="row tile-body">
                    <div class="col-12">
                        <img class="tile-icons" src="/static/img/settings/settings.png" alt="config icon">
                    </div>
                    <div class="col-12">
                        Account
                    </div>
                </div>
            </div>

            <div class="col-4 tile" onclick='pyview.open_settings_wlan_client()'>
                <div class="row tile-body">
                    <div class="col-12">
                        <img class="tile-icons" src="/static/img/settings/settings.png" alt="config icon">
                    </div>
                    <div class="col-12">
                        Wlan Client
                    </div>
                </div>
            </div>

            <div class="col-4 tile" onclick='pyview.open_settings_wlan_accesspoint()'>
                <div class="row tile-body">
                    <div class="col-12">
                        <img class="tile-icons" src="/static/img/settings/settings.png" alt="config icon">
                    </div>
                    <div class="col-12">
                        Wlan AP
                    </div>
                </div>
            </div>

        </div>

        <div class="row h-3of12">

            <div class="col-4 tile"  onclick='pyview.open_settings_stealth()'>
                <div class="row tile-body">
                    <div class="col-12">
                        <img class="tile-icons" src="/static/img/settings/stealth.png" alt="config icon">
                    </div>
                    <div class="col-12">
                        Stealth
                    </div>
                    <div class="row tile-footer">
                       {{ pyview.subject.stealth.stealth_method.get() }} 
                    </div>
                </div>
            </div>

            <div class="col-4 tile" onclick='pyhtmlgui.call(pyview.open_settings_neurorouting)'>
                <div class="row tile-body">
                    <div class="col-12">
                        <img class="tile-icons" src="/static/img/settings/neuro.png" alt="config icon">
                    </div>
                    <div class="col-12">
                        Neuro Routing
                    </div>
                </div>
            </div>

            <div class="col-4 tile" onclick='pyhtmlgui.call(pyview.open_settings_trackstop)'>
                <div class="row tile-body">
                    <div class="col-12">
                        <img class="tile-icons" src="/static/img/settings/trackstop.png" alt="config icon">
                    </div>
                    <div class="col-12">
                        Trackstop
                    </div>
                </div>
            </div>

        </div>



        <div class="row h-3of12">

            <div class="col-4 tile" onclick='pyhtmlgui.call(pyview.open_settings_vpn_openvpn)'>
               <div class="row tile-body">
                    <div class="col-12">
                        <img class="tile-icons" src="/static/img/settings/settings.png" alt="config icon">
                    </div>
                    <div class="col-12">
                        OpenVPN
                    </div>
                </div>
            </div>
            
            <div class="col-4 tile" onclick='pyhtmlgui.call(pyview.open_settings_smartnet)'>
               <div class="row tile-body">
                    <div class="col-12">
                        <img class="tile-icons" src="/static/img/settings/settings.png" alt="config icon">
                    </div>
                    <div class="col-12">
                        SmartNet
                    </div>
                </div>
            </div>
            
            <div class="col-4 tile">
            </div>
            
        </div>


        <div class="row h-1of6 p-6of6 bottom_row">
            <div class="col-4 bottom_tile" onclick = 'pyhtmlgui.call(pyview.on_back)'>
                <div class="bottom_tile-body">
                     <h3 class="verticalcenter"><img class="bottom_row_icons" src="/static/img/footer/back.png" alt="back icon"> Back</h3>  
                </div>
            </div>

            <div class="col-4">
            </div>

            <div class="col-4 bottom_tile"  onclick = 'pyhtmlgui.call(pyview.open_settings_more)'>
                <div class="bottom_tile-body">
                    <h3 class="verticalcenter">More <img class="bottom_row_icons" src="/static/img/footer/more.png" alt="more icon"></h3>
                </div>
            </div>
        </div>
    '''

    def __init__(self, subject, parent, on_back = None):
        """
        :type subject: core.settings.Settings
        :type parent: gui.privacypi.components.dashboard.Dashboard
        """
        super(Settings, self).__init__(subject, parent)

        self.settings_account          = Settings_account(subject.account, self, on_back=self.on_subsetting_exited)
        self.settings_wlan_accesspoint = Settings_wlan_accesspoint(subject.wlanaccesspoint, self, on_back=self.on_subsetting_exited, )
        self.settings_wlan_client      = Settings_wlan_client(     subject.wlanclient, self, on_back=self.on_subsetting_exited, )

        self.settings_stealth          = Settings_stealth(         subject, self, on_back=self.on_subsetting_exited, )
        self.settings_neurorouting     = Settings_neurorouting(    subject, self, on_back=self.on_subsetting_exited, )
        self.settings_trackstop        = Settings_trackstop(       subject, self, on_back=self.on_subsetting_exited, )

        self.settings_smartnet          = Settings_smartnet(        subject, self, on_back=self.on_subsetting_exited, )
        self.settings_vpn_openvpn       = Settings_vpn_openvpn(     subject, self, on_back=self.on_subsetting_exited, )


        self.settings_more             = Settings_more(            subject, self, on_back=self.on_subsetting_exited,  )
        self.on_back = on_back

    def open_settings_account(self):
        self.set_currentpage(self.settings_account)

    def open_settings_wlan_accesspoint(self):
        self.set_currentpage(self.settings_wlan_accesspoint)

    def open_settings_wlan_client(self):
        self.set_currentpage(self.settings_wlan_client)

    def open_settings_stealth(self):
        self.set_currentpage(self.settings_stealth)

    def open_settings_neurorouting(self):
        self.set_currentpage(self.settings_neurorouting)

    def open_settings_trackstop(self):
        self.set_currentpage(self.settings_trackstop)

    def open_settings_more(self):
        self.set_currentpage(self.settings_more)

    def on_subsetting_exited(self):
        self.parent.set_currentpage(self)

    def open_settings_smartnet(self):
        self.set_currentpage(self.settings_smartnet)

    def open_settings_vpn_openvpn(self):
        self.set_currentpage(self.settings_vpn_openvpn)

    def set_currentpage(self, new_page):
        self.parent.set_currentpage(new_page)
