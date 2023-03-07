import random
from pyhtmlgui import PyHtmlView, ObservableDictView, ObservableDict
from .modal import Modal

class SelectServerModalView(Modal):
    TEMPLATE_STR = '''   
   {% if pyview.display %}
    <div id="myModal" class="modal">
        <div class="modal-content">
            <div style="width:20%;height:100%;float:left;position:relative">
                <p style="{% if pyview.current_subsection_name  == "Favourites" %}color:#eee{% endif %};border-bottom:1px solid #aaa;margin-right:30px" onclick="pyview.select_subsection_with_filterclear('Favourites')">Favourites</p>
                <p style="{% if pyview.current_subsection_name  == "Countries" %}color:#eee{% endif %};border-bottom:1px solid #aaa;margin-right:30px" onclick="pyview.select_subsection_with_filterclear('Countries')">Countries</p> 
                <p style="{% if pyview.current_subsection_name  == "Cities" %}color:#eee{% endif %};border-bottom:1px solid #aaa;margin-right:30px" onclick="pyview.select_subsection_with_filterclear('Cities')">Cities </p>
                <p style="{% if pyview.current_subsection_name  == "Servers" %}color:#eee{% endif %};border-bottom:1px solid #aaa;margin-right:30px" onclick="pyview.select_subsection_with_filterclear('Servers')">All Servers </p>
                <div style="position:absolute;bottom:1em;" onclick="pyview.select_button()"><button>Select</button></div>    
            </div>
             
            <div style="width:80%;float:left;height:100%;font-size: 1.2em">
                <div style="float:left" onclick='pyview.select_subsection(
                    {% if pyview.current_subsection_name  == "Favourites" %}"Favourites"{% endif %}
                    {% if pyview.current_subsection_name  == "Zones" %}"Zones"{% endif %}
                    {% if pyview.current_subsection_name  == "Countries"%}"Countries"{% endif %}
                    {% if pyview.current_subsection_name  == "Cities" %}"Cities"{% endif %}
                    {% if pyview.current_subsection_name  == "Servers" %}"Servers"{% endif %}
                    )'> {{pyview.current_subsection_name}}  
                </div>                                
                <div style="float:right;font-size: 2em;line-height: 1em;" class="" onclick="pyview.hide()">
                    &times;
                </div>
                {% for item in pyview.slug %}
                    <div style="float:left"  onclick='pyview.open_subitem( "{{item}}")'>
                        &nbsp;>&nbsp;{{pyview.slug_names[loop.index0]}}
                    </div>
                {% endfor %}
                <input id="filter" type="text" value="{{pyview.filter}}" placeholder="Search" onkeyup='pyview.set_filter($("#filter").val())'></input>

                <div style="overflow: auto;height: 90%;float:left; width:100%">        
                    {{pyview.current_list.render()}}
                </div>
            </div>
        </div>
    </div>
    {% endif %}
    '''

    def __init__(self, subject, parent, **kwargs):
        """
        :type subject: core.Core
        :type parent: gui.default.components.dashboard.DashboardView
        """
        super(SelectServerModalView, self).__init__(subject, parent)

        self.subsections = {
            "Favourites" : ServerListView(subject.favourites.favourites, self),
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
        self.current_subsection_name =  name
        self.slug = []
        self.slug_names = []
        self.current_list.set_filter(self.filter)
        self.update()

    def open_subitem(self, identifier):
        try:
            index =self.slug.index(identifier)
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
        <thead>
            <tr>
                <th>  </th>
                <th> Name </th>
                <th> Bandwidth </th>
                <th> Load </th>
                <th> Favorite </th>
                <th>  </th>
            </tr>
        </thead>
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
        <tr id="{{pyview.uid}}" style="line-height: 2em;" class="list_item {% if pyview.core.session.can_add_hop(pyview.subject) == false %}can_not_add{% endif %}{% if pyview.selected %}active{% endif %}"
            onclick   ='pyview.select()'
            ondblclick='pyview.add_hop()'
        >
            <td style="line-height: 2em;" >
                <img style="height:2.5em;margin-top:-4px;margin-bottom:-18px;" src="/static/img/flags/flags-iso/flat/64/{{ pyview.subject.country_shortcodes.0 | upper}}.png">
            </td>
            <td>
                <b>{{ pyview.subject.name|title }}</b>
            </td>
            <td>
                {{ pyview.subject.bandwidth_max }} Mbit
            </td>
            <td>
                {{ pyview.subject.bandwidth_used_percent }}%
            </td>
            <td>
                {% if pyview.core.favourites.contains(pyview.subject.identifier) == false %}
                    <i class="fa fa-star-o" style="font-size:1.5em;padding-top:0.25em" onclick="event.stopPropagation();pyview.add_to_favourites();"></i>
                {% else %}
                    <i class="fa fa-star" style="font-size:1.5em;padding-top:0.25em;color:#ffff1d" onclick="event.stopPropagation();pyview.remove_from_favourites();"></i>
                {% endif %}
            </td>
            {% if pyview.subject.subitems %}
                <td>
                    <i class="fa fa-arrow-right" style="font-size:1.5em;padding-top:0.25em" onclick="event.stopPropagation();pyview.open_subitem();"></i>
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
        self.parent.parent.parent.hide()

    def add_to_favourites(self):
        self.core.favourites.add(self.subject.identifier)
        self.update()

    def remove_from_favourites(self):
        self.core.favourites.remove(self.subject.identifier)
        self.update()

    def open_subitem(self):
        self.parent.parent.open_subitem(self.subject.identifier)


class ObservableDictViewWithFilter(ObservableDictView):
    def __init__(self, subject, parent, item_class, dom_element = PyHtmlView.DOM_ELEMENT, sort_lambda=None, sort_reverse=False, **kwargs):
        """
        :type subject: subject: core.vpnconfigs.vpn_groups.VpnServerOrGroup
        :type parent: ServerListView
        """
        super().__init__(subject, parent, item_class, dom_element, sort_lambda, sort_reverse, **kwargs)
        self._filter = ""

    def get_items(self):
        return [item for item in super().get_items() if item.subject.match_filter(self._filter)]

    def set_filter(self, value):
        if self._filter != value:
            self._filter = value
            if self.is_visible:
                self.update()
