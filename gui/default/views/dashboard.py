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
            {% if pyview.subject.userapi.valid_until_days != None and pyview.subject.userapi.valid_until_days < 23 %}
                <div style="width: fit-content; position: absolute; top: 3em; right: 3em;color:{% if pyview.subject.userapi.valid_until_days < 5 %}red{% else %}orange{% endif %}">
                    {% if pyview.subject.userapi.valid_until_days < 0 %}
                        {{_("Your account has expired")}}
                    {% else %}
                        {{ngettext("Your account will expire in %(num)d day", "Your account will expire in %(num)d days", pyview.subject.userapi.valid_until_days)}}
                    {% endif %}
                    , <a href="" onclick="pyhtmlapp.open_url('https://www.perfect-privacy.com/order')">{{_("click here to extend!")}}</a>
                </div>
            {% endif %}
        </div>
        
        <div class="inner">
            {% if pyview.subject.userapi.credentials_valid.get() %}
                {{ pyview.hop_list.render() }}
            {% else %}
                <div style="width: 40%;margin: auto;">
                    <input id="username" type="text" placeholder="{{_("Username")}}"  value="{{pyview.username_input}}"/>
                    <br>
                    <input id="password" type="password" placeholder="{{_("Password")}}"  />
                </div>
                <br>
                {% if pyview.subject.userapi.account_expired %}
                    <p class="warning">{{_("account expired")}}</p>
                {% endif %}
                {% if pyview.subject.userapi.account_disabled %}
                    <p class="warning">{{_("account disabled")}}</p>
                {% endif %}
                {% if pyview.subject.userapi.credentials_valid.get() == False %}
                    {{_("Failed to login")}}
                {% endif %}
                <br>
                <br>
                <button onclick='pyview.login(document.getElementById("username").value, document.getElementById("password").value)' style="width:100%">
                    {{_("login")}}
                </button>
            {% endif %}
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
        :type subject: core.Core2
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
        self.add_observable(subject.userapi.valid_until)
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
             <h3 class="status_red">{{_("VPN Not Connected")}}</h3>
        {% elif pyview.subject.session.state.get() == "connecting" %}
            {% if pyview.subject.leakprotection.state.get() == "ENABLEING" %}
                 <h3 class="status_orange">{{_("Activating Leak Protection")}}</h3>
            {% else %}
                 <h3 class="status_orange">{{_("Connecting VPN Server")}}</h3>
            {% endif %}
        {% elif pyview.subject.session.state.get() == "connected" %}
            {% if pyview.subject.leakprotection.state.get() == "ENABLEING" or pyview.subject.ipcheck.state == "ACTIVE" %}
                 <h3 class="{% if pyview.subject.ipcheck.vpn_connected == true %}status_green{% else %}status_orange{% endif %}">{{_("Verifying VPN Security")}} </h3>
            {% else %}
                {% if pyview.subject.ipcheck.vpn_connected == true %}
                     <h3 class="status_green">{{_("Connected to Perfect Privacy")}}</h3>
                {% else %}
                     <h3 class="status_orange">{{_("Connected to Perfect Privacy, waiting for verification")}}</h3>
                {% endif %}
            {% endif %}
        {% elif pyview.subject.session.state.get() == "disconnecting" %}
             <h3 class="status_orange">{{_("Disconnecting VPN")}}</h3>
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
             <h3 class="status_green">{{_("Ports %(port1)d, %(port2)d and %(port3)d forwarded", port1=ports[0], port2=ports[1], port3=ports[2])}} </h3>
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
             <h3 class="status_green">{{_("Verifying Leak Protection")}}</h3>
        {% elif pyview.subject.get() == "ENABLED" %}
             <h3 class="status_green">{{_("Leak Protection enabled, all non VPN traffic is blocked")}}</h3>
        {% endif %}
    '''

class HopListView(PyHtmlView):
    TEMPLATE_STR = '''
        <div>
            <h2 style="width:50%;float:left">Connections</h2>
            {% if pyview.core.session._should_be_connected.get()  %}
                {% if pyview.core.session.state.get() == "disconnecting" %}
                
                    <button disabled style="float:right">{{_("Disconnecting")}}</button>    
                {% else %}
                    <button onclick='pyview.core.session.disconnect()' style="float:right">{{_("Disconnect")}}</button>    
                {% endif %}   
            {% else %}
                {% if pyview.core.session.hops | length > 0  %}
                     {% if pyview.core.session._get_number_of_non_idle_connections() == 0 %}
                        <button  onclick='pyview.core.session.connect()' style="float:right;background-color:#33c533a6">{{_("Connect")}}</button>
                     {% else %}
                         {% if pyview.core.session.state.get() == "disconnecting" %}
                            <button style="float:right" disabled>{{_("Disconnecting")}}</button>
                         {% endif %}
                     {% endif %}
                {% endif %}
            {% endif %}
            {% if pyview.can_add_server()  %}
                <button style="float:right;margin-right:10px" onclick='pyview.parent.select_server_modal.show()'>{{_("Add Server")}}</button>
            {% endif %}  
        </div>
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

    '''

    def __init__(self, subject, parent):
        """
        :type subject: ObservableList
        :type parent: SelectServerView
        """
        super(HopListView, self).__init__(subject, parent)
        self.core = parent.parent.subject

        self.add_observable(self.core.session)
        self.add_observable(self.core.session.state)
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
                <p style="margin-bottom:0px; font-size:1.2em;">{{ pyview.subject.servergroup.name |title}} </p>
                {% if pyview.subject.selected_server and (pyview.subject.selected_server.name != pyview.subject.servergroup.name) %}
                    <p style="margin-bottom:0px; font-size:1em;">{{ pyview.subject.selected_server.name|title }} </p>
                {% endif %}
                {% if  pyview.subject.servergroup.is_online == False or pyview.subject.selected_server.is_online == False %}
                   <p style="margin-bottom:0px; font-size:0.9em;color:orange">{{_("down for maintenance")}}</p>
                {% endif %}                
            </td>
            <td>
                {% if pyview.subject.remove_after_disconnect %}
                    {{_("Removing")}}
                {% else %} 
                    {% if pyview.subject.state.get() != "idle" %}
                        {{ pyview.subject.connection.state.get() |title }}
                    {% else %} 
                        {% if pyview.subject.session._should_be_connected.get() == True %}
                            {% if  pyview.subject.last_connection_failed == True %}
                                <p style="margin-bottom:0px; font-size:1em;color:orange">{{_("Connection Failed")}}</p>
                                <p style="margin-bottom:0px; font-size:0.9em;color:orange">{{_("retrying in a few seconds")}}</p>
                            {% else %}  
                                 {{_("Waiting for connection")}}
                            {% endif %}   
                        {% endif %}  
                    {% endif %} 
                {% endif %} 
            </td>
            <td>
                <button onclick='pyview.core.session.remove_hop_by_index( {{ pyview.element_index() }})' >{{_("remove")}}</button>
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
            <div style="width:100%;text-align:center;display:flex">
                {% if pyview.subject.ipcheck.result4.public_ip != None %}
                    <div style="width:{% if pyview.subject.ipcheck.result4.public_ip == None or pyview.subject.ipcheck.result6.public_ip == None %}100%{% else  %}50%{% endif %};">
                        <h2 style="text-align:center">IP: {{ pyview.subject.ipcheck.result4.public_ip }}</h2>
                        <h3 style="text-align:center">{{ pyview.subject.ipcheck.result4.public_rdns }}</h3>
                        <h3 style="text-align:center">
                            {{ pyview.subject.ipcheck.result4.public_city }}{% if pyview.subject.ipcheck.result4.public_city != "" %},{% endif %}
                            {{ pyview.subject.ipcheck.result4.public_country }}
                        </h3>
                    </div>
                {% endif %}
                {% if pyview.subject.ipcheck.result6.public_ip != None %}
                    <div style="width:{% if pyview.subject.ipcheck.result4.public_ip == None or pyview.subject.ipcheck.result6.public_ip == None %}100%{% else  %}50%{% endif %};">
                        <h2 style="text-align:center">IP: {{ pyview.subject.ipcheck.result6.public_ip }}</h2>
                        <h3 style="text-align:center">{{ pyview.subject.ipcheck.result6.public_rdns }}</h3>
                        <h3 style="text-align:center">
                            {{ pyview.subject.ipcheck.result6.public_city }}{% if pyview.subject.ipcheck.result6.public_city != "" %},{% endif %}
                            {{ pyview.subject.ipcheck.result6.public_country }}
                        </h3>
                    </div>
                {% endif %}
            </div>
            <div style="width:100%;text-align:center;padding-bottom:20px">
                {% if pyview.subject.ipcheck.state == "ACTIVE"%}
                    <button disabled>{{_("Verify Connection..")}}</button> </h3>
                {% else %}
                    <button onclick="pyview.parent.subject.check_connection()">{{_("Check Connection")}}</button> </h3>
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

