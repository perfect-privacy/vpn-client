from pyhtmlgui import PyHtmlView

from .settings.settings import Settings as SettingsGui
from .switch_server import Switch_server


class Dashboard(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="row h-9of12" >
            <div class="col-4">
            
                   {% for hop in pyview.subject.session.hops %}
                    <div class="row">
                        <div class="col-md-12">
                            {{ hop.servergroup }}, {{ hop.selected_server }}, {{ hop.connection }}
                            
                            {% if pyview.subject.session._get_number_of_non_idle_connections() == 0  %}
                                <button   onclick='pyhtmlgui.call(pyview.subject.session.remove_hop_by_index, {{ loop.index0 }})' >remove</button>
                            {% endif %}
                            {% if hop.connection != None %}
                                    {{ hop.connection.selected_server }}
                                    {{ hop.connection.external_host_ip }}
                                    {{ hop.connection.external_host_port }}
                                    {{ hop.connection.hop_number }}
                                    {{ hop.connection.state.get() }}
                            {% endif %}
                        </div>
                    </div>>
                {% endfor %}
                
            </div>
        </div>
        
        <div class="row h-1of6 p-6of6 bottom_row">
            <div class="col-4 bottom_tile" onclick='pyhtmlgui.call(pyview.open_settings)'>
                <div class="bottom_tile-body">
                    <h3 class="verticalcenter">Settings <img class="bottom_row_icons" src="/static/img/footer/more.png" alt="more icon"></h3>
                </div>
                
            </div>
            
            <div class="col-4 bottom_tile" onclick='pyview.open_switch_server()'>
                <div class="bottom_tile-body">
                    <h3 class="verticalcenter">Server list<img class="bottom_row_icons" src="/static/img/footer/more.png" alt="more icon"></h3>
                </div>
            </div>
            
            {% if pyview.subject.session.state == "idle" %}
                <div class="col-4 bottom_tile" onclick='pyhtmlgui.call(pyview.subject.session.connect_current_configuration)'>
                    <div class="bottom_tile-body">
                        <h3 class="verticalcenter">Connect</h3>
                    </div>
                </div>
            {% else %}
                <div class="col-4 bottom_tile" onclick='pyview.subject.session.disconnect()'>
                    <div class="bottom_tile-body">
                       <h3 class="verticalcenter"> Disconnect</h3>
                    </div>
                </div>
            {% endif %}
            
         </div>
        
    '''

    def __init__(self, subject, parent):
        """
        :type subject: core.Core
        :type parent: gui.privacypi.components.mainview.MainView
        """
        super(Dashboard, self).__init__(subject, parent)
        self.settings      = SettingsGui(   subject.settings      , self, on_back=self.on_settings_exited  )
        self.switch_server = Switch_server( subject, self, on_back=self.on_settings_exited)
        self.add_observable(subject.session, self.state_change)

    def state_change(self, *args, **kwargs):
        self.update()

    def open_settings(self):
        self.set_currentpage(self.settings)

    def open_switch_server(self):
        self.set_currentpage(self.switch_server)

    def on_settings_exited(self):
        self.set_currentpage(self)

    def set_currentpage(self, page):
        self.parent.set_currentpage(page)