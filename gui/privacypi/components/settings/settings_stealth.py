from pyhtmlgui import PyHtmlView

#from .settings_stealth_method import Settings_stealth_method

class Settings_stealth(PyHtmlView):
    TEMPLATE_STR = '''

        <div class="row h-3of12" >
        
            <div class="col-4 tile" onclick = 'pyhtmlgui.call(pyview.subject.stealth.stealth_method.set, "None" )'>
                <div class="row tile-body {% if pyview.subject.stealth.stealth_method.get() == "None" %}tile-selected{% endif %}">
                    No Stealth
                </div>
            </div>
            
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.stealth.stealth_method.set, "ssh" )'>
                <div class="row tile-body {% if pyview.subject.stealth.stealth_method.get() == "ssh" %}tile-selected{% endif %}">
                   ssh
                </div>
            </div>
  
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.stealth.stealth_method.set, "obfs" )'>
                <div class="row tile-body {% if pyview.subject.stealth.stealth_method.get() == "obfs" %}tile-selected{% endif %}">
                   obfs
                </div>
            </div>
                    

        </div>

        <div class="row h-3of12">

            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.stealth.stealth_method.set, "stunnel" )'>
                <div class="row tile-body {% if pyview.subject.stealth.stealth_method.get() == "stunnel" %}tile-selected{% endif %}">
                   stunnel
                </div>
            </div>
             
            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.stealth.stealth_method.set, "httpproxy" )'>
                <div class="row tile-body {% if pyview.subject.stealth.stealth_method.get() == "httpproxy" %}tile-selected{% endif %}">
                   httpproxy
                </div>
            </div>

            <div class="col-4 tile"  onclick = 'pyhtmlgui.call(pyview.subject.stealth.stealth_method.set, "socksproxy" )'>
                <div class="row tile-body {% if pyview.subject.stealth.stealth_method.get() == "socksproxy" %}tile-selected{% endif %}">
                   socksproxy
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

            <div class="col-4 bottom_tile">
                {% if pyview.subject.enable_expert_mode.get() and pyview.subject.stealth.stealth_method.get() != "None" %}
                    <div class="row" style="height: 100%;">
                        <div style="width: 100%;text-align: center;font-size: 1.4em;font-weight: 600;">Stealth Host</div>
                        <div style="width: 100%;text-align: center;position: absolute;bottom: 0px;">Automatic</div>    
                    </div>
                {% endif %}
            </div>


        </div>
    '''
    def __init__(self, subject, parent, on_back, **kwargs):
        """
        :type subject: core.settings.settings.Settings
        :type parent: gui.privacypi.components.settings.settings.Settings
        :type on_back: function
        """
        super(Settings_stealth, self).__init__(subject, parent)
        self.add_observable(subject.stealth,  self._on_default_event_updated)
        self.on_back = on_back

    #def open_settings_stealth_method(self):
    #    self.parent.set_currentpage(self.settings_stealth_method)

    def on_subsetting_exited(self):
        self.parent.set_currentpage(self)

