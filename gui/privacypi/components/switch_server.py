from pyhtmlgui import PyHtmlView, DictWrapperComponent
import random
import time



class ServerListsItem(PyHtmlView):

    TEMPLATE_STR = '''
        <div class="list_item  {% if pyview.selected %}active{% endif %}">
            <div class="row "
                style="height:50px;"
                onclick   ='pyview.select()       '
                ondblclick='pyview.connect_or_add()'
            >
                <div class="col-4 list_text">
                    <img class="list_flags" src="/static/img/flags/GB.png" alt="back icon"> {{ pyview.subject.name }}                    
                </div>
    
                <div class="col-3">
                      <div class="list_text">1000 MBit/s</div>
                </div>
    
                <div class="col-5">
                   <div class="progress_outer">
                        &nbsp;
                        free: 73%
                        <div class="progress_bar" style="max-width: 73%">
                        &nbsp;
                        </div>
                    </div> 
                </div>
            </div>
        </div>
    '''

    def __init__(self, subject, parent):

        super(ServerListsItem, self).__init__(subject, parent)
        self.selected = False

    def select(self):
        self.parent.select_item(self)
        # TODO EXAMPLE CODE

        #js = '$pyview.find( ".row" ).css( "background-color", "blue" );'
        #self.javascript_call(js)

        #jsf = 'return 2+2;'
        #self.javascript_call(jsf, callback=lambda result:print(result) )

        #jsf = 'return 4+2;'
        #r = self.javascript_call(jsf )() # this will block and fail at this point because this function is called from javascript and the js loop is waiting for the result of this function
        #print("result:", r)

    def connect_or_add(self):
        self.parent.parent.subject.settings.enable_expert_mode.set(True)  # TODO test foo
        self.parent.parent.subject.session.connect_or_add(self.subject)
        print("connect or add")


class ServerList(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="row">
            <div class="col-12 list_container">
                {% for  item in pyview.current_items()  %}
                    <div class="{{ loop.cycle('odd', '') }}">
                        {{ item.render() }}
                    </div>
                {% endfor %}        
            </div>
        </div>
    '''

    def __init__(self, subject, parent):
        """

        """
        super(ServerList, self).__init__(subject, parent)
        self.items = DictWrapperComponent(subject, self, ServerListsItem)
        self.limit = 0

    def current_items(self):
        return sorted([item for key,item in self.items.get().items()], key=lambda x: x.subject.identifier)

    def unselect_all(self):
        for key, z in self.items.get().items():
            if z.selected is True:
                z.selected = False
                z.update()

    def select_item(self, item):
        for key, z in self.items.get().items():
            if z.selected is True and z != item:
                z.selected = False
                z.update()
            if z.selected is False and z == item:
                z.selected = True
                z.update()

    def get_selected(self):
        for key, z in self.items.get().items():
            if z.selected == True:
                return z
        return None

    def get_random(self):
        return random.choice([item for _, item in self.items.get().items()])


class Switch_server(PyHtmlView):
    TEMPLATE_STR = '''

        <div class="row h-9of12" style="overflow:auto">
            <style>
                /* width */
                ::-webkit-scrollbar {
                  width: 80px;
                }
                
                /* Track */
                ::-webkit-scrollbar-track {
                  background: #f1f1f1;
                }
                
                /* Handle */
                ::-webkit-scrollbar-thumb {
                  background: #888;
                }
                
                /* Handle on hover */
                ::-webkit-scrollbar-thumb:hover {
                  background: #555;
                }
            
            </style>
        
            <div class="col-12">
                  {{pyview.current_list.render()}}
            </div>
        </div>

        <div class="row h-1of6 p-6of6 bottom_row">
            <div class="col-4 bottom_tile" onclick = 'pyhtmlgui.call(pyview.on_back)'>
                <div class="bottom_tile-body">
                     <h3 class="verticalcenter"><img class="bottom_row_icons" src="/static/img/footer/back.png" alt="back icon"> Back</h3>  
                </div>
            </div>
            
            <div class="col-4 bottom_tile" onclick ='pyhtmlgui.call(pyview.next_scope) '>
                <div class="bottom_tile-body">
                        <div class="row">
                            <div class="col-12" style="padding-top: 5px;">
                                <h3 class="verticalcenter">{{ pyview.current_list_name }} </h3>
                            </div>
                            <div class="col-12">
                                <div class="row">
                                    <div class="col-2"></div>
                                    <div class="col-2 {% if pyview.current_list_name  == "Zones" %}   active_scope{% endif %}">o</div>
                                    <div class="col-2 {% if pyview.current_list_name  == "Countrys"%} active_scope{% endif %}">o</div>
                                    <div class="col-2 {% if pyview.current_list_name  == "Citys" %}   active_scope{% endif %}">o</div>
                                    <div class="col-2 {% if pyview.current_list_name  == "Servers" %} active_scope{% endif %}">o</div>
                                </div>
                            </div>
                        </div>
                    
                </div>
            </div>
            
            
            <div class="col-4 bottom_tile" onclick ='pyhtmlgui.call(pyview.connect_button)'>
                <div class="bottom_tile-body">
                    <p><h3 class="verticalcenter"> Connect </h3></p>
                </div>
            </div>
        </div>

    '''

    def __init__(self, subject, parent, on_back, **kwargs):
        """
        :type subject: core.Core
        :type parent: gui.privacypi.components.dashboard.Dashboard
        """
        super(Switch_server, self).__init__(subject, parent)
        self.on_back = on_back
        self.zone_list    = ServerList(subject.vpnGroupPlanet.zones   , self)
        self.country_list = ServerList(subject.vpnGroupPlanet.countrys, self)
        self.city_list    = ServerList(subject.vpnGroupPlanet.citys   , self)
        self.server_list  = ServerList(subject.vpnGroupPlanet.servers , self)
        self.lists = [
            ("Zones", self.zone_list),
            ("Countrys", self.country_list),
            ("Citys", self.city_list),
            ("Servers", self.server_list),
        ]
        self.current_index = 0
        self.current_list = self.lists[self.current_index][1]
        self.current_list_name =  self.lists[self.current_index][0]

    def prev_scope(self):
        self.current_list.unselect_all()
        self.current_index -= 1
        if self.current_index < 0:
            self.current_index = 0
        self.current_list = self.lists[self.current_index][1]
        self.current_list_name =  self.lists[self.current_index][0]
        self.update()

    def next_scope(self):
        self.current_list.unselect_all()
        self.current_index += 1
        if self.current_index == len(self.lists):
            self.current_index = 0
        self.current_list = self.lists[self.current_index][1]
        self.current_list_name =  self.lists[self.current_index][0]
        self.update()


    def connect_button(self):
        selected = self.current_list.get_selected()
        if selected is not None:
            selected.connect_or_add()
        else:
            self.current_list.get_random().connect_or_add()

    def on_subsetting_exited(self):
        self.parent.set_currentpage(self)
