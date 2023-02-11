from pyhtmlgui import PyHtmlView, ObservableListView

#from .vpn_settings import VpnSettingsView
from .public_ip import PublicIpView
from .stealth import StealthView
from .port_forwarding import PortForwardingView
from .preferences import PreferencesView
from .dashboard import DashboardView
from .trackstop import TrackstopView
from .leak_protection import LeakProtectionView
from .logs import LogsView
from .modals.confirm_exit import ConfirmExitModalView
from ...common.components import SelectComponent


class MainView(PyHtmlView):
    TEMPLATE_STR = '''
        <script>
            function confirm_exit(){
                pyview.confirmExitModal.show()
            }
        </script>
        {% set interface_level = pyview.subject.settings.interface_level.get() %}
        <section id="sidebar">
            <div class="inner">
                <div style="position:absolute;top:0px;width:100%">
                    {{ pyview.interface_level.render() }}
                </div>
                <nav>
                    <ul>
                        <li><a href="#intro">Dashboard</a></li>
                        <li><a href="#trackstop">TrackStop</a></li>
                        <li><a href="#leakprotection">Leak Protection</a></li>
                        {% if interface_level != "simple" %}
                            <li><a href="#stealth">Stealth</a></li>
                            <li><a href="#portforwarding">Port Forwarding</a></li>
                        {% endif %}
                        <li><a href="#preferences">Preferences</a></li>
                        {% if interface_level  == "expert" %}
                            <li><a href="#logs">Log</a></li>
                        {% endif %}
                    </ul>  
                </nav>
                <button onclick="pyview.confirmExitModal.show()" style="width:100%;position:absolute;bottom:20px"> Exit </button> 
            </div>
        </section>
        
        <div id="wrapper">
        
            <section id="intro" class="wrapper style1 fullheight fade-up">
                {{ pyview.dashboard.render() }}
            </section>
            
            <section id="trackstop" class="wrapper style2 fullheight fade-up">                
                {{ pyview.trackstop.render() }}
            </section>

            <section id="leakprotection" class="wrapper style3 fullheight fade-up">
                {{ pyview.leakprotection.render() }}
            </section>

            {% if interface_level != "simple" %}

                <section id="stealth" class="wrapper style1 fullheight fade-up">
                    {{ pyview.stealth.render() }}
                </section>

                <section id="portforwarding" class="wrapper style2 fullheight fade-up">                
                    {{ pyview.portforwarding.render() }}
                </section>
                                
            {% endif %}
            
            <section id="preferences" class="wrapper style1 fullheight fade-up">
                {{ pyview.preferences.render() }}
            </section>
            
            {% if interface_level == "expert" %}
                <section id="logs" class="wrapper style2 fullheight fade-up">
                    {{ pyview.logs.render() }}
                </section>
            {% endif %}
           
        </div>
        <script>
            function show_preferences(){
                
            }
        </script>
        {{ pyview.confirmExitModal.render() }} 
    '''


    def __init__(self, subject, parent):
        super(MainView, self).__init__(subject, parent)
        self.dashboard = DashboardView(subject, self)
        self.trackstop = TrackstopView(subject, self)
        self.leakprotection = LeakProtectionView(subject, self)
        self.portforwarding = PortForwardingView(subject, self)
        self.publicIp = PublicIpView(subject, self)
        #self.vpnsettings = VpnSettingsView(subject, self)
        self.stealth = StealthView(subject, self)
        self.preferences = PreferencesView(subject, self)
        self.logs = LogsView(subject, self)
        self.current_view = self.dashboard
        self.confirmExitModal = ConfirmExitModalView(subject, self)
        self.add_observable(self.subject.userapi.credentials_valid, self._on_subject_updated)
        self.add_observable(self.subject.settings.interface_level,  self._on_interface_level_updated)

        self.interface_level = SelectComponent(subject.settings.interface_level, self,
                                            options=[
                                                ("simple"  , "Simple" ),
                                                ("advance" , "Advanced"  ),
                                                ("expert"  , "Expert"  ),
                                            ])

    def show_dashboard(self):
        if self.current_view != self.dashboard:
            self.current_view = self.dashboard
            self.update()

    def _on_interface_level_updated(self, source, **kwargs):
        self.update()
        self.eval_javascript("document.documentElement.scrollTop = 0;", skip_results=True)

    def exit_frontend_app(self):
        self.eval_javascript("exit_app()", skip_results=True)
