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


'''
from pyhtmlgui import PyHtmlView, ObservableListView

from .vpn_settings import VpnSettingsView
from .public_ip import PublicIpView
from .stealth import StealthView
from .port_forwarding import PortForwardingView
from .preferences import PreferencesView
from .dashboard import DashboardView
from .trackstop import TrackstopView
from .leak_protection import LeakProtectionView
from .logs import LogsView
from .modals.confirm_exit import ConfirmExitModalView

class MainView(PyHtmlView):
    TEMPLATE_STR = ' ''
        {% set interface_level = pyview.subject.settings.interface_level.get() %}
        <section id="sidebar">
            <div class="inner">
                <select id="interface_level" class="form-control" style="text-align: center;text-align-last: center;position:absolute;top:0px" onchange='pyview.subject.settings.interface_level.set($("#interface_level").val())'>
                    <option value="simple"   {% if pyview.subject.settings.interface_level.get() == "simple" %}   selected {% endif %}> Simple  </option>
                    <option value="advanced" {% if pyview.subject.settings.interface_level.get() == "advanced" %} selected {% endif %}> Advanced  </option>
                    <option value="expert"   {% if pyview.subject.settings.interface_level.get() == "expert" %}   selected {% endif %}> Expert </option>
                </select>
                <nav>
                    <ul>
                        <li><a onclick="pyview.show_dashboard()">Dashboard</a></li>
                        <li><a onclick="pyview.show_publicIp()">Public IP</a></li>
                        <li><a onclick="pyview.show_trackstop()">TrackStop</a></li>
                        {% if interface_level  != "simple" %}
                            <li><a onclick="pyview.show_leakprotection()">Leak Protection</a></li>
                            <li><a onclick="pyview.show_portforwarding()">Port Forwarding</a></li>
                            <li><a onclick="pyview.show_vpnsettings()">VPN Settings</a></li>
                            <li><a onclick="pyview.show_stealth()">Stealth</a></li>
                            <li><a onclick="pyview.show_preferences()">Preferences</a></li>
                            {% if interface_level  != "advanced" %}
                                <li><a onclick="pyview.show_logs()">Log</a></li>
                            {% endif %}
                        {% endif %}

                    </ul>
                </nav>
                <button onclick="pyview.confirmExitModal.show()" style="width:100%;position:absolute;bottom:20px"> Exit </button>
            </div>
        </section>

        <div id="wrapper">

            <section class="wrapper style1 fullscreen fade-up">
                {{ pyview.current_view.render() }}
            </section>

            <section id="three" class="wrapper style1 fade-up" style="display:none">
                <div>
                    <div class="inner">
                        <h2>Get in touch</h2>
                        <p>Phasellus convallis elit id ullamcorper pulvinar. Duis aliquam turpis mauris, eu ultricies erat malesuada quis. Aliquam dapibus, lacus eget hendrerit bibendum, urna est aliquam sem, sit amet imperdiet est velit quis lorem.</p>
                        <div class="split style1">
                            <section>
                                <form method="post" action="#">
                                    <div class="field half first">
                                        <label for="name">Name</label>
                                        <input type="text" name="name" id="name" />
                                    </div>
                                    <div class="field half">
                                        <label for="email">Email</label>
                                        <input type="text" name="email" id="email" />
                                    </div>
                                    <div class="field">
                                        <label for="message">Message</label>
                                        <textarea name="message" id="message" rows="5"></textarea>
                                    </div>
                                    <ul class="actions">
                                        <li><a href="" class="button submit">Send Message</a></li>
                                    </ul>
                                </form>
                            </section>
                            <section>
                                <ul class="contact">
                                    <li>
                                        <h3>Address</h3>
                                        <span>12345 Somewhere Road #654<br />
                                        Nashville, TN 00000-0000<br />
                                        USA</span>
                                    </li>
                                    <li>
                                        <h3>Email</h3>
                                        <a href="#">user@untitled.tld</a>
                                    </li>
                                    <li>
                                        <h3>Phone</h3>
                                        <span>(000) 000-0000</span>
                                    </li>
                                    <li>
                                        <h3>Social</h3>
                                        <ul class="icons">
                                            <li><a href="#" class="fa-twitter"><span class="label">Twitter</span></a></li>
                                            <li><a href="#" class="fa-facebook"><span class="label">Facebook</span></a></li>
                                            <li><a href="#" class="fa-github"><span class="label">GitHub</span></a></li>
                                            <li><a href="#" class="fa-instagram"><span class="label">Instagram</span></a></li>
                                            <li><a href="#" class="fa-linkedin"><span class="label">LinkedIn</span></a></li>
                                        </ul>
                                    </li>
                                </ul>
                            </section>
                        </div>
                    </div>
                </div>
            </section>
        </div>

        {{ pyview.confirmExitModal.render() }}
    '' '


    def __init__(self, subject, parent):
        super(MainView, self).__init__(subject, parent)
        self.dashboard = DashboardView(subject, self)
        self.trackstop = TrackstopView(subject, self)
        self.leakprotection = LeakProtectionView(subject, self)
        self.portforwarding = PortForwardingView(subject, self)
        self.publicIp = PublicIpView(subject, self)
        self.vpnsettings = VpnSettingsView(subject, self)
        self.stealth = StealthView(subject, self)
        self.preferences = PreferencesView(subject, self)
        self.logs = LogsView(subject, self)
        self.current_view = self.dashboard
        self.confirmExitModal = ConfirmExitModalView(subject, self)
        self.add_observable(self.subject.userapi.credentials_valid, self._on_subject_updated)
        self.add_observable(self.subject.settings.interface_level,  self._on_interface_level_updated)

    def show_dashboard(self):
        if self.current_view != self.dashboard:
            self.current_view = self.dashboard
            self.update()

    def show_trackstop(self):
        if self.current_view != self.trackstop:
            self.current_view = self.trackstop
            self.update()

    def show_leakprotection(self):
        if self.current_view != self.leakprotection:
            self.current_view = self.leakprotection
            self.update()

    def show_portforwarding(self):
        if self.current_view != self.portforwarding:
            self.current_view = self.portforwarding
            self.update()

    def show_publicIp(self):
        if self.current_view != self.publicIp:
            self.current_view = self.publicIp
            self.update()

    def show_vpnsettings(self):
        if self.current_view != self.vpnsettings:
            self.current_view = self.vpnsettings
            self.update()

    def show_stealth(self):
        if self.current_view != self.stealth:
            self.current_view = self.stealth
            self.update()

    def show_preferences(self):
        if self.current_view != self.preferences:
            self.current_view = self.preferences
            self.update()

    def show_logs(self):
        if self.current_view != self.logs:
            self.current_view = self.logs
            self.update()



    def _on_interface_level_updated(self, source, **kwargs):
        self.update()
        self.eval_javascript("document.documentElement.scrollTop = 0;", skip_results=True)

    def exit_frontend_app(self):
        self.eval_javascript("exit_app()", skip_results=True)


'''