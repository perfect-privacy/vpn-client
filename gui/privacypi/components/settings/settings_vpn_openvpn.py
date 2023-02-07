from pyhtmlgui import PyHtmlView
# ipsec/openvpn not need at the moment

from .settings_vpn_openvpn_port import Settings_vpn_openvpn_port
from .settings_vpn_openvpn_protocol import Settings_vpn_openvpn_protocol
from .settings_vpn_openvpn_help import Settings_vpn_openvpn_help

class Settings_vpn_openvpn(PyHtmlView):
    TEMPLATE_STR = '''

        <div class="row h-3of12">

            <div class="col-4 tile"  onclick='pyhtmlgui.call(pyview.open_settings_vpn_openvpn_protocol)'>
                <div class="row tile-body">
                   <h3 class="verticalcenter"> Protocol </h3>
                </div>
                <div class="row tile-footer">
                   {{ pyview.subject.vpn.openvpn.transport_layer_protocol.get() }} 
                </div>
            </div>
            <div class="col-4 tile"  onclick='pyhtmlgui.call(pyview.open_settings_vpn_openvpn_port)'>
                <div class="row tile-body">
                   <h3 class="verticalcenter"> Port </h3>
                </div>
                <div class="row tile-footer">
                   {{ pyview.subject.vpn.openvpn.port.get() }} 
                </div>
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

            <div class="col-4">
            </div>
        </div>
    '''

    def __init__(self, subject, parent, on_back, **kwargs):
        """
        :type subject: core.settings.settings.Settings
        :type parent: gui.privacypi.components.settings.settings.Settings
        :type on_back: function
        """
        super(Settings_vpn_openvpn, self).__init__(subject, parent)
        self.on_back = on_back
        self.settings_vpn_openvpn_help = Settings_vpn_openvpn_help(subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_vpn_openvpn_port = Settings_vpn_openvpn_port(subject, self, on_back=self.on_subsetting_exited, **kwargs)
        self.settings_vpn_openvpn_protocol = Settings_vpn_openvpn_protocol(subject, self, on_back=self.on_subsetting_exited, **kwargs)

    def open_settings_vpn_openvpn_help(self):
        self.set_currentpage(self.settings_vpn_openvpn_help)


    def open_settings_vpn_openvpn_protocol(self):
        self.set_currentpage(self.settings_vpn_openvpn_protocol)

    def open_settings_vpn_openvpn_port(self):
        self.set_currentpage(self.settings_vpn_openvpn_port)


    def set_currentpage(self, new_page):
        self.parent.set_currentpage(new_page)

    def on_subsetting_exited(self):
        self.parent.set_currentpage(self)
