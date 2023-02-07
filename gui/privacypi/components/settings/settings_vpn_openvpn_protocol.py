from pyhtmlgui import PyHtmlView


# ipsec/openvpn not need at the moment

class Settings_vpn_openvpn_protocol(PyHtmlView):
    TEMPLATE_STR = '''

        <div class="row h-3of12">
        
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.vpn.openvpn.transport_layer_protocol.set, "udp" )'>
                <div class="row tile-body {% if pyview.subject.vpn.openvpn.transport_layer_protocol.get() == "udp" %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> udp </h3>
                </div>
            </div>

            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.vpn.openvpn.transport_layer_protocol.set, "tcp" )'>
                <div class="row tile-body {% if pyview.subject.vpn.openvpn.transport_layer_protocol.get() == "tcp" %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> tcp </h3>
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
        :type parent: gui.privacypi.components.settings.settings.Settings_vpn_openvpn
        :type on_back: function
        """
        super(Settings_vpn_openvpn_protocol, self).__init__(subject, parent)
        self.add_observable(subject.vpn.openvpn.protocol, self._on_default_event_updated)
        self.on_back = on_back
