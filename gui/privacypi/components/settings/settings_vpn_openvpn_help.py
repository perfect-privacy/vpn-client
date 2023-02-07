from pyhtmlgui import PyHtmlView


# ipsec/openvpn not need at the moment

class Settings_vpn_openvpn_help(PyHtmlView):
    TEMPLATE_STR = '''

        <div class="row h-1of6 p-6of6">
            <div class="col-4 tile" onclick = 'pyhtmlgui.call(pyview.on_back)'>
                <div class="bottom_tile-body">
                     <h3><img class="bottom_row_icons" src="/static/img/footer/back.png" alt="back icon"> Back</h3>  
                </div>
            </div>

            <div class="col-4">
            </div>

            <div class="col-4">
            </div>
        </div>
    '''

    def __init__(self, subject, parent, on_back, **kwargs):
        super(Settings_vpn_openvpn_help, self).__init__(subject, parent)
        self.on_back = on_back
