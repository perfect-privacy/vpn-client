from pyhtmlgui import PyHtmlView


# ipsec/openvpn not need at the moment

class Settings_vpn_openvpn_port(PyHtmlView):
    TEMPLATE_STR = '''
                
        <div class="row h-3of12">

            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.vpn.openvpn.port.set, "23" )'>
                <div class="row tile-body {% if pyview.subject.vpn.openvpn.port.get() == "23" %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> 23 </h3>
                </div>
            </div>
            
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.vpn.openvpn.port.set, "42" )'>
                <div class="row tile-body {% if pyview.subject.vpn.openvpn.port.get() == "42" %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> 42 </h3>
                </div>
            </div>
            
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.vpn.openvpn.port.set, "11" )'>
                <div class="row tile-body {% if pyview.subject.vpn.openvpn.port.get() == "11" %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> 11 </h3>
                </div>
            </div>

        </div>
        

        <div class="row h-3of12">
        
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.vpn.openvpn.port.set, "111" )'>
                <div class="row tile-body {% if pyview.subject.vpn.openvpn.port.get() == "111" %}tile-selected{% endif %}">
                   <h3 class="verticalcenter"> 111 </h3>
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
        super(Settings_vpn_openvpn_port, self).__init__(subject, parent)
        self.add_observable(subject.vpn.openvpn.port,  self._on_default_event_updated)
        self.on_back = on_back
