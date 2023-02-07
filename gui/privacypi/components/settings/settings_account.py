from pyhtmlgui import PyHtmlView


class Settings_account(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="row h-1of3 p-1o6">            
            <div class="col-4 ">
                 Username 
            </div>

            <div class="col-8 tile"> BLAH
            </div>

        </div>
        <div class="row h-1of3 p-1o6">            
            <div class="col-4 ">
                 PASSwORD 
            </div>

            <div class="col-8 tile"> BLAH
            </div>

        </div>


        <div class="row h-1of6 p-6of6 bottom_row">
            <div class="col-4 bottom_tile" onclick = 'pyview.pyview.on_back)'>
                 <div class="bottom_tile-body">
                    <h3 class="verticalcenter"><img class="bottom_row_icons" src="/static/img/footer/back.png" alt="back icon"> Back</h3>  
                </div>
            </div>

            <div class="col-4">
            </div>

            <div class="col-4 bottom_tile">
                <div class="bottom_tile-body">
                    logout/login
                </div>
            </div>
        </div>
    '''

    def __init__(self, subject, parent, on_back, **kwargs):
        """
        :type subject: core.settings.settings.Settings_Account
        :type parent: gui.privacypi.components.settings.settings.Settings
        :type on_back: function
        """
        super(Settings_account, self).__init__(subject, parent)
        self.on_back = on_back
        #self.add_observable(obj.settings.credentials, self._on_default_event_updated)

        #self.jscall('''
        #    $({{pyview.uid}}).find('.my_class')
        #
        #''')

    #def jscall(self, js):
    #    self.jscall()
    #    self.templateEnv.from_string(js).render({"this": self })