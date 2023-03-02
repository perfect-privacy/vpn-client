import threading
import time

from pyhtmlgui import PyHtmlView, ObservableListView

from config.constants import VPN_PROTOCOLS
from .modals.confirm_logout import ConfirmLogoutModalView
from .modals.select_server import SelectServerModalView

class DashboardView(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="head" style="height: 10vh;width: 100%;">
            <img src="/static/img/logo_dark.png" style="width: fit-content; position: absolute; top: 1em; left: 2em;">
            <div style="width: fit-content; position: absolute; top: 1.5em; right: 3em;">
                {% if pyview.subject.userapi.credentials_valid.get() == True %}                    
                    <div style="float: left;line-height: 3em;padding-right: 1em;">
                        <h3><a>{{pyview.subject.settings.account.username.get()}}</a></h3>
                    </div>
                    <i class="fa fa-sign-out" style="font-size:1.5em;" onclick="pyview.confirm_logout_modal.show()"></i>
                {% endif %}
            </div>
        </div>
        
        <div class="inner">
            {% if pyview.subject.userapi.credentials_valid.get() %}
                {{ pyview.hop_list.render() }}
            {% else %}
                <div style="width: 40%;margin: auto;"> 
                    <input id="username" type="text" placeholder="Username"  value="{{pyview.username_input}}"/>
                    <br>
                    <input id="password" type="password" placeholder="Password"  />
                </div>
                <br>
                {% if pyview.subject.userapi.account_expired %}
                    <p class="warning">account expired</p>        
                {% endif %}
                {% if pyview.subject.userapi.account_disabled %}
                    <p class="warning">account disabled</p>   
                {% endif %}
                {% if pyview.subject.userapi.credentials_valid.get() == False %}
                    Failed to login
                {% endif %} 
                <br>
                <br>
                <button onclick='pyview.login(document.getElementById("username").value, document.getElementById("password").value)' style="width:100%">
                    login
                </button>
            {% endif %}
            <br>
            <br>

            {{ pyview.vpnStatusView.render() }}
            {{ pyview.leakProtectionStateView.render() }}
            {{ pyview.defaultPortforwardingView.render() }}
        </div>
        
        {{pyview.ipCheckView.render()}}
        
        {{ pyview.confirm_logout_modal.render() }}
        {{ pyview.select_server_modal.render() }}
    '''

    def __init__(self, subject, parent):
        """
        :type subject: core.Core
        :type parent: gui.default.components.mainview.MainView
        """
        super(DashboardView, self).__init__(subject, parent)
        self.hop_list = HopListView( subject.session.hops, self)
        self.confirm_logout_modal = ConfirmLogoutModalView(subject, self)
        self.select_server_modal = SelectServerModalView(subject, self)
        self.username_input = subject.settings.account.username.get()
        self.ipCheckView = IpCheckView(subject, self)
        self.leakProtectionStateView = LeakProtectionStateView(subject.leakprotection.state, self)
        self.defaultPortforwardingView = DefaultPortforwardingView(subject, self)
        self.vpnStatusView = VpnStatusView(subject, self)
        self.add_observable(subject.userapi.credentials_valid)
        self._bg_thread = threading.Thread(target=self.bg_thread, daemon=True)
        self._bg_thread.start()

    def login(self, username, password):
        self.username_input = username
        if username != "" and password != "":
            self.subject.userapi.new_credentials(username, password)

    def bg_thread(self):
        while True:
            if self.is_visible is True:
                self.subject.userapi.request_update()
            time.sleep(10*60)


class VpnStatusView(PyHtmlView):
    DOM_ELEMENT_EXTRAS = "style='width:100%;text-align:center;'"
    TEMPLATE_STR = '''    
        {% if pyview.subject.session.state.get() == "idle" %}
             <h3 class="status_red">VPN Not Connected</h3>
        {% elif pyview.subject.session.state.get() == "connecting" %}
            {% if pyview.subject.leakprotection.state.get() == "ENABLEING" %}
                 <h3 class="status_orange">Activating Leak Protection</h3>
            {% else %}
                 <h3 class="status_orange">Connecting VPN Server</h3>
            {% endif %}
        {% elif pyview.subject.session.state.get() == "connected" %}
            {% if pyview.subject.leakprotection.state.get() == "ENABLEING" or pyview.subject.ipcheck.state == "ACTIVE" %}
                 <h3 class="{% if pyview.subject.ipcheck.vpn_connected == true %}status_green{% else %}status_orange{% endif %}">Verifying VPN Security </h3>
            {% else %}            
                {% if pyview.subject.ipcheck.vpn_connected == true %}
                     <h3 class="status_green">Connected to Perfect Privacy</h3>
                {% else %}
                     <h3 class="status_orange">Connected to Perfect Privacy, waiting for verification</h3>
                {% endif %}
            {% endif %}
        {% elif pyview.subject.session.state.get() == "disconnecting" %}
             <h3 class="status_orange">Disconnecting VPN</h3>
        {% endif %}
    '''
    def __init__(self, subject, parent, **kwargs):
        super().__init__(subject, parent, **kwargs)
        self.remove_observable(subject)
        self.add_observable(subject.ipcheck)
        self.add_observable(subject.leakprotection.state)
        self.add_observable(subject.session.state)


class DefaultPortforwardingView(PyHtmlView):
    DOM_ELEMENT_EXTRAS = "style='width:100%;text-align:center;'"
    TEMPLATE_STR = '''
        {% set ports = pyview.subject.session.calculate_ports() %}
        {% if  pyview.subject.ipcheck.vpn_connected == True and pyview.subject.userapi.default_port_forwarding.get() == True and ports != None %}
             <h3 class="status_green">Ports {{ports[0]}}, {{ports[1]}} and {{ports[2]}} forwarded </h3>
        {% endif %}
    '''
    def __init__(self, subject, parent, **kwargs):
        super().__init__(subject, parent, **kwargs)
        self.remove_observable(subject)
        self.add_observable(subject.ipcheck)
        self.add_observable(subject.userapi.default_port_forwarding)


class LeakProtectionStateView(PyHtmlView):
    DOM_ELEMENT_EXTRAS = "style='width:100%;text-align:center;'"
    TEMPLATE_STR = '''
        {% if pyview.subject.get() == "ENABLEING" %}
             <h3 class="status_green">Verifying Leak Protection</h3>
        {% elif pyview.subject.get() == "ENABLED" %}
             <h3 class="status_green">Leak Protection enabled, all non VPN traffic is blocked</h3>
        {% endif %}
    '''

class HopListView(PyHtmlView):
    TEMPLATE_STR = '''
    <h2>Connections</h2>
        <table style="width:100%">
            <thead>
                <tr>
                    <th>  </th>
                    <th>  </th>
                    <th>  </th>
                    <th>  </th>
                </tr>
            </thead>
            {{pyview.items.render()}}
        </table>
        {% if pyview.core.session._should_be_connected.get()  %}
            <button  onclick='pyview.core.session.disconnect()'>Disconnect</button>            
        {% else %}
            {% if pyview.core.session.hops | length > 0 and pyview.core.session._get_number_of_non_idle_connections() == 0 %}
                <button  onclick='pyview.core.session.connect()' style="background-color:#33c533a6">Connect</button>
            {% endif %}
        {% endif %}
        {% if pyview.can_add_server()  %}
            <button  onclick='pyview.parent.select_server_modal.show()'>Add Server</button>
        {% endif %}  <!---  if pyview.core.session._should_be_connected.get() == false and ---->
    '''

    def __init__(self, subject, parent):
        """
        :type subject: ObservableList
        :type parent: SelectServerView
        """
        super(HopListView, self).__init__(subject, parent)
        self.core = parent.parent.subject

        self.add_observable(self.core.session)
        self.add_observable(self.core.session.hops)
        self.add_observable(self.core.settings.vpn.vpn_protocol)
        self.add_observable(self.core.settings.vpn.openvpn.cascading_max_hops)
        self.items = ObservableListView(subject, self, HopListItemView, dom_element="tbody")

    def can_add_server(self):
        if self.core.settings.vpn.vpn_protocol.get() == VPN_PROTOCOLS.openvpn:
            max_hops = self.core.settings.vpn.openvpn.cascading_max_hops.get()
        else:
            max_hops = 1
        return len(self.core.session.hops) < max_hops



class HopListItemView(PyHtmlView):
    DOM_ELEMENT = None
    TEMPLATE_STR = '''
        <tr id="{{pyview.uid}}" class="list_item">
            <td>
                <img src="/static/img/flags/flags-iso/flat/64/{{ pyview.subject.servergroup.country_shortcodes.0 | upper }}.png" style="opacity:0.9">
            </td>
            <td>
                {{ pyview.subject.servergroup.name }} <br>
                
                {% if pyview.subject.selected_server %}
                    {{ pyview.subject.selected_server.name|title }}
                {% endif %}
            </td>
            <td>
                {% if pyview.subject.connection != None %}
                    {{ pyview.subject.connection.state.get() |title }}
                {% endif %}             
            </td>
            <td>
                {% if pyview.core.session._get_number_of_non_idle_connections() == 0  %}
                    <button onclick='pyview.core.session.remove_hop_by_index( {{ pyview.element_index() }})' >remove</button>
                {% endif %}
            </td>
        </tr>
    '''
    '''
    <div class="row">
        <div class="col-md-12">
            {{ pyview.subject.servergroup }}, {{ pyview.subject.selected_server }}, {{ pyview.subject.connection }}                            
            {% if pyview.subject.connection != None %}
                    {{ pyview.subject.connection.selected_server }}
                    {{ pyview.subject.connection.external_host_ip }}
                    {{ pyview.subject.connection.external_host_port }}
                    {{ pyview.subject.connection.hop_number }}
                    {{ pyview.subject.connection.state.get() }}
            {% endif %}
        </div>
    </div>
    '''

    def __init__(self, subject, parent):
        """
        :type subject: ObservableList
        :type parent: ObservableListView
        """
        super(HopListItemView, self).__init__(subject, parent)
        self.core = parent.parent.parent.subject
        self.add_observable(self.core.session)

class IpCheckView(PyHtmlView):
    TEMPLATE_STR = ''' 
    
        {% if pyview.subject.session.state.get() == "connected" or  pyview.subject.session.state.get() == "idle"  %}

            {% if pyview.subject.ipcheck.result4.public_ip != None %}
                <div style="width:{% if pyview.subject.ipcheck.result4.public_ip == None or pyview.subject.ipcheck.result6.public_ip == None %}100%{% else  %}50%{% endif %};float:left">
                    <h2 style="text-align:center">IP: {{ pyview.subject.ipcheck.result4.public_ip }}</h2>
                    <h3 style="text-align:center">{{ pyview.subject.ipcheck.result4.public_rdns }}</h3>
                    <h3 style="text-align:center">
                        {{ pyview.subject.ipcheck.result4.public_city }}{% if pyview.subject.ipcheck.result4.public_city != "" %},{% endif %}
                        {{ pyview.subject.ipcheck.result4.public_country }}
                    </h3>
                </div>
            {% endif %}
            {% if pyview.subject.ipcheck.result6.public_ip != None %}
                <div style="width:{% if pyview.subject.ipcheck.result4.public_ip == None or pyview.subject.ipcheck.result6.public_ip == None %}100%{% else  %}50%{% endif %};float:left">
                    <h2 style="text-align:center">IP: {{ pyview.subject.ipcheck.result6.public_ip }}</h2>
                    <h3 style="text-align:center">{{ pyview.subject.ipcheck.result6.public_rdns }}</h3>
                    <h3 style="text-align:center">
                        {{ pyview.subject.ipcheck.result6.public_city }}{% if pyview.subject.ipcheck.result6.public_city != "" %},{% endif %}
                        {{ pyview.subject.ipcheck.result6.public_country }}
                    </h3>
                </div>
            {% endif %}
                
            <div style="width:100%;text-align:center;float:left">
                {% if pyview.subject.ipcheck.state == "ACTIVE"%}
                    <button disabled>Verify Connection..</button> </h3>
                {% else %}
                    <button onclick="pyview.parent.subject.check_connection()">Check Connection</button> </h3>
                {% endif %}
            </div>
        {% endif %}
    '''
    def __init__(self, subject, parent, **kwargs):
        super().__init__(subject, parent, **kwargs)
        self.remove_observable(subject)
        self.add_observable(subject.ipcheck)
        self.add_observable(subject.ipcheck.result4)
        self.add_observable(subject.ipcheck.result6)
        self.add_observable(subject.session.state)

