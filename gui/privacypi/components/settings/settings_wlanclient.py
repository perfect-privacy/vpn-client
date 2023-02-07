from pyhtmlgui import PyHtmlView


class Settings_wlan_client(PyHtmlView):
    TEMPLATE_STR = '''

        <div class="row h-1of3">
            <div class="col-4">
            on
            </div>

            <div class="col-4">
            info
            </div>

            <div class="col-4">
            off
            </div>
        </div>

        <div class="row h-1of6 p-6of6 bottom_row">
            <div class="col-4 tile" onclick = 'pyhtmlgui.call(pyview.on_back)'>
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
        :type subject: core.settings.settings.Settings_WlanClient
        :type parent: gui.privacypi.components.settings.settings.Settings
        :type on_back: function
        """
        super(Settings_wlan_client, self).__init__(subject, parent)
        self.on_back = on_back

    def set_currentpage(self, new_page):
        self.parent.set_currentpage(new_page)

    def on_subsetting_exited(self):
        self.parent.set_currentpage(self)
