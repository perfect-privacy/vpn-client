from pyhtmlgui import PyHtmlView
import gettext
from .modals.confirm_exit_update import ConfirmExitUpdateModalView
from .stealth import StealthView
from .port_forwarding import PortForwardingView
from .preferences import PreferencesView
from .dashboard import DashboardView
from .trackstop import TrackstopView
from .leak_protection import LeakProtectionView
from .logs import LogsView
from .modals.confirm_exit import ConfirmExitModalView
from ...common.components import SelectComponent
from ...common.translations import Translations


class MainView(PyHtmlView):
    TEMPLATE_STR = '''
        <script> 
            // is called by qt app, for example in reaction to osx menu exit button clicked.
            function confirm_exit(){ 
                pyview.confirmExitModal.show() 
            } 
        </script>
        
        <section id="sidebar">
            <div class="inner">
                <div style="position:absolute;top:0px;width:100%">
                    <!--- {{_("Simple")}} , {{_("Advanced")}} , {{_("Expert")}} --->
                    {{ pyview.interface_level.render() }}
                </div>
                <nav>
                    <ul>
                        <li><a href="#intro">{{_("Dashboard")}}</a></li>
                        <li><a href="#trackstop">{{_("TrackStop")}}</a></li>
                        <li><a href="#leakprotection">{{_("Leak Protection")}}</a></li>
                        {% if pyview.subject.settings.interface_level.get() != "simple" %}
                            <li><a href="#stealth">{{_("Stealth")}}</a></li>
                            <li><a href="#portforwarding">{{_("Port Forwarding")}}</a></li>
                        {% endif %}
                        <li><a href="#preferences">{{_("Preferences")}}</a></li>
                        {% if pyview.subject.settings.interface_level.get()  == "expert" %}
                            <li><a href="#logs">{{_("Log")}}</a></li>
                        {% endif %}
                    </ul>  
                </nav>
                <button onclick="pyview.confirmExitModal.show()" style="width:100%;position:absolute;bottom:20px">{{_("Exit")}}</button> 
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

            {% if pyview.subject.settings.interface_level.get() != "simple" %}

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
            
            {% if pyview.subject.settings.interface_level.get() == "expert" %}
                <section id="logs" class="wrapper style2 fullheight fade-up">
                    {{ pyview.logs.render() }}
                </section>
            {% endif %}

            {{ pyview.softwareUpdateHint.render() }}  
        </div>
        {{ pyview.confirmExitModal.render() }} 
        {{ pyview.confirmExitUpdateModal.render() }} 
    '''


    def __init__(self, subject, parent):
        super(MainView, self).__init__(subject, parent)
        self.dashboard = DashboardView(subject, self)
        self.trackstop = TrackstopView(subject, self)
        self.leakprotection = LeakProtectionView(subject, self)
        self.portforwarding = PortForwardingView(subject, self)
        self.stealth = StealthView(subject, self)
        self.preferences = PreferencesView(subject, self)
        self.logs = LogsView(subject, self)
        self.current_view = self.dashboard
        self.confirmExitModal = ConfirmExitModalView(subject, self)
        self.confirmExitUpdateModal = ConfirmExitUpdateModalView(subject, self)
        self.add_observable(self.subject.userapi.credentials_valid, self._on_subject_updated)
        self.add_observable(self.subject.settings.interface_level,  self._on_interface_level_updated)
        self.add_observable(self.subject.settings.language, self._on_language_updated)
        self.interface_level = SelectComponent(subject.settings.interface_level, self,
                                            options=[
                                                ("simple"  , "Simple" ),
                                                ("advance" , "Advanced"  ),
                                                ("expert"  , "Expert"  ),
                                            ])
        self.softwareUpdateHint = SoftwareUpdateHint(self.subject.softwareUpdater.state, self)
        self.translations = Translations(self.subject.settings.language.get(), self._instance._template_env)

    def show_dashboard(self):
        if self.current_view != self.dashboard:
            self.current_view = self.dashboard
            self.update()

    def _on_language_updated(self, source, **kwargs):
        self.translations.update(self.subject.settings.language.get())
        self.update()

    def _on_interface_level_updated(self, source, **kwargs):
        self.update()
        self.eval_javascript("document.documentElement.scrollTop = 0;", skip_results=True)

class SoftwareUpdateHint(PyHtmlView):
    TEMPLATE_STR = '''
        {% if pyview.subject.get() == "READY_FOR_INSTALL" %}
            <div style="height:30px;position:fixed;bottom:0px;background-color:green;width:calc(100% - 15em);text-align:center">
                <b style="cursor:pointer" onclick="pyview.ask_update()">{{_("Software update available, click here to install")}}</b>
            </div>
        {% endif %}
    '''
    def ask_update(self):
        self.parent.confirmExitUpdateModal.show()
