import gettext
import random

from pyhtmlgui import PyHtmlView, ObservableListView
from .modals.select_server import ObservableDictViewWithFilter
from ...common.translations import Translations


class TrayView(PyHtmlView):
    TEMPLATE_STR = '''
        <script>
            {% if pyview.subject.session.state.get() == "idle" %}
                pyhtmlapp.set_icon_state("disconnected")
            {% elif pyview.subject.session.state.get() == "connected" and pyview.subject.ipcheck.vpn_connected == true %}
                pyhtmlapp.set_icon_state("connected")
            {% else %}
                pyhtmlapp.set_icon_state("working")
            {% endif %}
        </script>
        
        <div id="wrapper">
            <section id="intro" class="wrapper style1 fullheight fade-up">
            {% if pyview.select_server == True %}
                {{ pyview.selectServerView.render()  }}
            {% else %}   
                <div class="head" style="height: 10vh;width: 100%;margin-bottom:10px;">
                    <img src="/static/img/logo_dark.png" style="width: 50%; position: absolute; top: 0.5em; left: 1em;">
                </div>
                {% if pyview.confirm_exit == True %}
                    <h2 style="padding: 2em;"> {{_("Are you sure you want to Exit?")}}</h2>
                    {% if pyview.subject.settings.startup.enable_background_mode.get() == False %}
                        {% if pyview.subject.session._get_number_of_non_idle_connections() != 0 %}
                            <h3 style="padding-bottom: 2em;"> {{_("This will <b>disconnect</b> all existing VPN Tunnels!")}} </h3>
                        {% endif %}
                    {% else %}
                         {% if pyview.subject.session._get_number_of_non_idle_connections() != 0 %}
                            <h3 style="padding-bottom: 2em;"> {{_("Background mode enabled, your VPN connections will stay active!")}}</h3>
                        {% else %}
                            {% if pyview.subject.settings.leakprotection.leakprotection_scope.get() == "program" %}
                                <h3 style="padding-bottom: 2em;"> {{_("Background mode enabled, Leak Protection will stay active!")}}</h3>
                            {% endif %}
                        {% endif %}
                    {% endif %}
                    <br>          
                    <div style="position: absolute; bottom: 5px; width: calc(100% - 5px);">
                         <div style="width:50%;text-align:center;float:left">
                            <button onclick="pyview.exit_app()">{{_("Yes")}}</button>
                         </div>     
                         <div style="width:50%;text-align:center;float:right">
                            <button onclick="pyview.hide_confirm_exit()">{{_("No")}}</button>
                         </div>     
                        </div>   
                {% else %}
                       

                    <div style="width:100%;text-align:center;">
                        {{ pyview.hop_list.render() }}
                    </div>
                    <br>
                    <div style="width:100%;text-align:center;">              
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
                    </div>

                    <div style="width:100%;text-align:center;">
                        {% if pyview.subject.leakprotection.state.get() == "ENABLEING" %}
                             <h3 class="status_green">{{_("Verifying Leak Protection")}}</h3>
                        {% elif pyview.subject.leakprotection.state.get() == "ENABLED" %}
                             <h3 class="status_green">{{_("Leak Protection enabled, all non VPN traffic is blocked")}}</h3>
                        {% endif %}
                    </div>     
                    <div style="display:none;width:100%;text-align:center;">
                        {% if pyview.subject.session._should_be_connected.get()  %}
                            <button onclick='pyview.subject.session.disconnect()'>{{_("Disconnect")}}</button>            
                        {% else %}
                            {% if pyview.subject.session.hops | length > 0 and pyview.subject.session._get_number_of_non_idle_connections() == 0 %}
                                <button onclick='pyview.subject.session.connect()' style="background-color:#33c533a6">{{_("Connect")}}</button>
                            {% endif %}
                        {% endif %}
                    </div>     
                    <div style="position: absolute; bottom: 5px; width: calc(100% - 5px);">
                         <div style="width:50%;text-align:center;float:left">
                            <button onclick='pyhtmlapp.show_app()'>{{_("Show App")}}</button>     
                         </div>     
                         <div style="width:50%;text-align:center;float:right">
                            <button onclick='pyview.ask_confirm_exit()'>{{_("Exit App")}}</button>     
                         </div>     
                    </div>         
                {% endif %}
              
             {% endif %}
            
            </section>

        </div>    
    '''

    def __init__(self, subject, parent):
        super(TrayView, self).__init__(subject, parent)
        self.hop_list = HopListView( subject.session.hops, self)
        self.selectServerView = SelectServerView(subject, self)
        self.add_observable(self.subject.userapi.credentials_valid, self._on_subject_updated)
        self.add_observable(subject.ipcheck, self._on_subject_updated)
        self.add_observable(subject.leakprotection.state, self._on_subject_updated)
        self.add_observable(subject.session.hops, self._on_subject_updated)
        self.add_observable(subject.session.state, self._on_subject_updated)
        self.add_observable(subject.userapi.default_port_forwarding, self._on_subject_updated)
        self.add_observable(subject.settings.vpn.openvpn.cascading_max_hops)
        self.add_observable(self.subject.settings.language, self._on_language_updated)
        self.confirm_exit = False
        self.select_server = False
        self.translations = Translations(self.subject.settings.language.get(), self._instance._template_env)

    def _on_language_updated(self, source, **kwargs):
        self.translations.update(self.subject.settings.language.get())
        self.update()

    def show_select_server(self):
        self.select_server = True
        if self.is_visible is True:
            self.update()

    def hide_select_server(self):
        self.select_server = False
        self.selectServerView.filter = ""
        self.selectServerView.select_subsection("Countries")
        if self.is_visible is True:
            self.update()

    def hide_confirm_exit(self):
        self.confirm_exit = False
        if self.is_visible is True:
            self.update()

    def ask_confirm_exit(self):
        self.confirm_exit = True
        if self.is_visible is True:
            self.update()

    def exit_app(self):
        self.subject.on_frontend_exit_by_user()
        self.eval_javascript("pyhtmlapp.exit_app()", skip_results=True)
        self.hide_confirm_exit()


class HopListView(PyHtmlView):
    TEMPLATE_STR = '''
        <table style="width:100%;margin-bottom:10px">

            {{pyview.items.render()}}
        </table>
        <div style="text-align:center">
            {% if pyview.core.session._should_be_connected.get()  %}
                <button style="width:49%"  onclick='pyview.core.session.disconnect()'>{{_("Disconnect")}}</button>            
            {% else %}
                {% if pyview.core.session.hops | length > 0 and pyview.core.session._get_number_of_non_idle_connections() == 0 %}
                    <button style="width:49%;background-color:#33c533a6" onclick='pyview.core.session.connect()'>{{_("Connect")}}</button>
                {% endif %}
            {% endif %}
            {% if pyview.core.session.hops | length < pyview.core.settings.vpn.openvpn.cascading_max_hops.get()  %}
                <button style="width:49%"  onclick='pyview.parent.show_select_server()'>{{_("Add Server")}}</button>
            {% endif %}  <!---  if pyview.core.session._should_be_connected.get() == false and ---->
        </div>
    '''

    def __init__(self, subject, parent):

        super(HopListView, self).__init__(subject, parent)
        self.core = parent.subject

        self.add_observable(self.core.session)
        self.items = ObservableListView(subject, self, HopListItemView, dom_element="tbody")
        #self.add_observable(self.core.session.hops)
        #self.add_observable(self.core.settings.vpn.openvpn.cascading_max_hops)

class HopListItemView(PyHtmlView):
    DOM_ELEMENT = None
    TEMPLATE_STR = '''
        <tr id="{{pyview.uid}}" class="list_item">
            <td>
                <img style="max-width:25px" src="/static/img/flags/flags-iso/flat/64/{{ pyview.subject.servergroup.country_shortcodes.0 | upper }}.png" style="opacity:0.9">
            </td>
            <td>
                {{ pyview.subject.servergroup.name }} 
            </td>
            <td>
                {% if pyview.subject.connection != None %}
                    {{ pyview.subject.connection.state.get() |title }}
                {% else %}     
                    {% if pyview.core.session._get_number_of_non_idle_connections() == 0  %}
                        <button style="border-radius: 2em;height: calc(2.75em + 2px);line-height: 2.75em;padding: 0 1.75em;" class="" onclick='pyview.core.session.remove_hop_by_index( {{ pyview.element_index() }})' >{{_("remove")}}</button>
                    {% endif %}
                {% endif %}  
            </td>
        </tr>
    '''


    def __init__(self, subject, parent):
        """
        :type subject: ObservableList
        :type parent: ObservableListView
        """
        super(HopListItemView, self).__init__(subject, parent)
        self.core = parent.parent.parent.subject


class SelectServerView(PyHtmlView):
    TEMPLATE_STR = '''   
        <div style="width:100%;height:100vh;">
            <div style="float:left;font-size:0.8em" onclick='pyview.select_subsection(
                {% if pyview.current_subsection_name  == "Favourites" %}"{{_("Favourites")}}"{% endif %}
                {% if pyview.current_subsection_name  == "Zones" %}"{{_("Zones")}}"{% endif %}
                {% if pyview.current_subsection_name  == "Countries"%}"{{_("Countries")}}"{% endif %}
                {% if pyview.current_subsection_name  == "Cityies" %}"{{_("Cityies")}}"{% endif %}
                {% if pyview.current_subsection_name  == "Servers" %}"{{_("Servers")}}"{% endif %}
                )'> {{pyview.current_subsection_name}}  
            </div>                                
            <div style="cursor:pointer;float:right;font-size: 2em;line-height: 1em;" class="" onclick="pyview.parent.hide_select_server()">
                &times;
            </div>

            {% for item in pyview.slug %}
                <div style="font-size:0.8em;float:left"  onclick='pyview.open_subitem( "{{item}}")'>
                    &nbsp;>&nbsp;{{pyview.slug_names[loop.index0]}}
                </div>
            {% endfor %}
            <input style="height:1.75em"id="filter" type="text" value="{{pyview.filter}}" placeholder="Search" onkeyup='pyview.set_filter($("#filter").val())'></input>

            <div style="overflow: auto;height: 80%;float:left; width:100%;margin-top:5px">        
                {{pyview.current_list.render()}}
            </div>
        </div>
    '''

    def __init__(self, subject, parent, **kwargs):
        super(SelectServerView, self).__init__(subject, parent)

        self.subsections = {
            "Favourites": ServerListView(subject.favourites.favourites, self),
            "Zones": ServerListView(subject.vpnGroupPlanet.zones, self),
            "Countries": ServerListView(subject.vpnGroupPlanet.countrys, self),
            "Cities": ServerListView(subject.vpnGroupPlanet.citys, self),
            "Servers": ServerListView(subject.vpnGroupPlanet.servers, self),
        }
        self.current_subsection_name = "Countries"
        self.current_list = self.subsections[self.current_subsection_name]
        self.slug = []
        self.slug_names = []
        self.filter = ""

    def select_subsection_with_filterclear(self, name):
        self.filter = ""
        self.select_subsection(name)

    def select_subsection(self, name):
        self.current_list.unselect_all()
        self.current_list = self.subsections[name]
        self.current_subsection_name = name
        self.slug = []
        self.slug_names = []
        self.current_list.set_filter(self.filter)
        self.update()

    def open_subitem(self, identifier):
        try:
            index = self.slug.index(identifier)
            del self.slug[index:]
            del self.slug_names[index:]
        except:
            pass
        self.slug.append(identifier)
        self.slug_names.append(identifier.split("=")[1])
        selected = self.subject.vpnGroupPlanet.search_by_identifier(identifier)
        self.current_list = ServerListView(selected.subitems, self)
        if self.filter != "":
            self.current_list.set_filter(self.filter)
        self.update()

    def set_filter(self, value):
        self.filter = value
        self.current_list.set_filter(value)

    def select_button(self):
        selected = self.current_list.get_selected()
        if selected is not None:
            selected.add_hop()


class ServerListView(PyHtmlView):
    TEMPLATE_STR = '''
    <table style="width:100%">
        {{pyview.items.render()}}
    </table>
    '''

    def __init__(self, subject, parent):
        """
        :type subject: ObservableDict
        :type parent: SelectServerModalView
        """
        super(ServerListView, self).__init__(subject, parent)
        self.items = ObservableDictViewWithFilter(subject, self, ServerListsItemView, dom_element="tbody")

    def set_filter(self, value):
        self.items.set_filter(value)

    def unselect_all(self):
        for item in self.items.get_items():
            if item.selected is True:
                item.selected = False
                item.update()

    def select_item(self, _item):
        for item in self.items.get_items():
            if item.selected is True and item != _item:
                item.selected = False
                item.update()
            if item.selected is False and item == _item:
                item.selected = True
                item.update()

    def get_selected(self):
        for item in self.items.get_items():
            if item.selected == True:
                return item
        return None

    def get_random(self):
        return random.choice([item for _, item in self.items.get_items()])

    def open_subitem(self, identifier):
        self.parent.open_subitem(identifier)


class ServerListsItemView(PyHtmlView):
    DOM_ELEMENT = None
    TEMPLATE_STR = '''
        <tr style="line-height:1em;" id="{{pyview.uid}}" class="list_item {% if pyview.core.session.can_add_hop(pyview.subject) == false %}can_not_add{% endif %}{% if pyview.selected %}active{% endif %}"
            onclick   ='pyview.select()'
            ondblclick='pyview.add_hop()'
        >
            <td>
                <img src="/static/img/flags/flags-iso/flat/64/{{ pyview.subject.country_shortcodes.0 | upper}}.png" style="width:25px">
            </td>
            <td>
                <h4 style="padding-top:4px">{{ pyview.subject.name|title }}
                {% if pyview.subject.is_online == False %}
                    <p style="margin:0px;padding:0px;font-size:0.8em;color:orange">{{_("maintenance")}}</p>
                {% endif %}
                </h4>
            </td>
            {% if pyview.subject.subitems %}
                <td>
                    <i class="fa fa-arrow-right" style="cursor:pointer;font-size:1.0em;" onclick="event.stopPropagation();pyview.open_subitem();"></i>
                </td> 
            {% else %}
                <td></td> 
            {% endif %}
        </tr>
    '''

    def __init__(self, subject, parent):
        """
        :type subject: ObservableDict
        :type parent: ObservableDictViewWithFilter
        """
        super(ServerListsItemView, self).__init__(subject, parent)
        self.selected = False
        self.core = parent.parent.parent.subject

    def select(self):
        self.parent.parent.select_item(self)

    def add_hop(self):
        self.core.session.add_hop(self.subject)
        self.parent.parent.parent.parent.hide_select_server()

    def open_subitem(self):
        self.parent.parent.open_subitem(self.subject.identifier)


