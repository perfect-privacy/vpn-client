import time
from pyhtmlgui import PyHtmlView, ObservableListView
from gui.common.components import CheckboxComponent


class ServerGroupView(PyHtmlView):
    TEMPLATE_STR = '''
    <label for="select_servergroup"> </label>
        <div id="select_servergroup" class="nice-select" onclick="if(!this.classList.contains('open')){this.classList.toggle('open');this.children[0].focus();}">
            <input id="select_servergroup_input" value="{{pyview.get_current_valueid()}}" style="position:fixed;left:-9999px;"  onfocusout="setTimeout(function(){ document.getElementById('select_servergroup').classList.remove('open') }, 200);"></input>
            <div class="current">{{pyview.get_current_valuestr() }}</div>
            <ul class="list">
                {% for item in pyview.subject._server_groups %}
                    <li onclick="pyview.set_value('{{item['name']}}','{{item['id']}}')" class="option {% if pyview.subject.customPortForwardings.portforwardings.0 and pyview.subject.customPortForwardings.portforwardings.0.serverGroupId == item['id'] %}selected{% endif %}"> {{ item['name'] }}  </li>
                {% endfor %}
            </ul>
        </div>   
    '''
    def __init__(self, subject, parent, **kwargs):
        super().__init__(subject, parent, **kwargs)
        self.add_observable(self.subject._server_groups)
        self.add_observable(self.subject.customPortForwardings.portforwardings)
        self.local_value_str = ""
        self.local_value_id = ""

    def set_value(self, value_str, value_id):
        self.local_value_str = value_str
        self.local_value_id = value_id
        self.update()

    def get_current_valuestr(self):
        if len(self.subject.customPortForwardings.portforwardings) > 0:
            pf = self.subject.customPortForwardings.portforwardings[0]
            for servergroup in self.subject._server_groups:
                if servergroup["id"] == pf.serverGroupId:
                    return servergroup["name"]
        if self.local_value_str == "":
            for servergroup in self.subject._server_groups:
                return servergroup["name"]
        return self.local_value_str

    def get_current_valueid(self):
        if len(self.subject.customPortForwardings.portforwardings) > 0:
            pf = self.subject.customPortForwardings.portforwardings[0]
            for servergroup in self.subject._server_groups:
                if servergroup["id"] == pf.serverGroupId:
                    return servergroup["id"]
        if self.local_value_id == "":
            for servergroup in self.subject._server_groups:
                return servergroup["id"]
        return self.local_value_id

class PortForwardingView(PyHtmlView):
    TEMPLATE_STR = '''
        {% if pyview.subject.userapi.credentials_valid.get() != True %}
            <div class="not_logged_in">
                Login to change your Portforwarding settings.
            </div>
        {% endif %}

        <div class="inner">
            <h1>Port Forwarding</h1>
            <p>Port forwardings are helpful to optimize the speed for certain games or Peer-to-peer software like torrent clients. You can designate up to five specific ports to forward to your computer.
            Note: It might take up to 3 minutes for any changes to apply on our Servers. 
            If you update your port forwarding settings on our website, it might take some time for the settings below to refresh. <a onclick="pyview.refresh()">Refresh Now</a> 
            </p>
            <div class="boxes">
                <section>
                    <h3>
                        Default Port Forwarding
                        <div class="input"> {{ pyview.default_port_forwarding.render() }}</div>
                    </h3>
                    <div>
                        Enable standard port forwarding.&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                        <div class="tooltip" style="display:none">
                            If default port forwarding is enabled, three random ports will be forwarded to your computer.
                        </div>
                    </div>
                </section>
                <section>
                    <h3>
                        Enable Custom Port Forwarding
                        <div class="input">
                            <div class="CheckboxComponent">
                                <input onchange='pyview.set_custom_port_forwarding($("#checkbox_custom_port_forwarding").prop("checked") === true )'
                                    class="form-check-input" type="checkbox" value="" id="checkbox_custom_port_forwarding"
                                    {% if pyview.custom_port_forwarding_enabled() %} checked {% endif %}
                                    {% if pyview.subject.userapi.customPortForwardings.portforwardings | length > 0 %} disabled {% endif %}
                                >
                                <label class="form-check-label" for="checkbox_custom_port_forwarding"></label>
                            </div>
                        </div>
                    </h3>
                    <div>
                        Enable configurable port forwarding.&nbsp;<a class="tooltip_more_less" onclick="show_tooltip(this)" data-txt_less="less" data-txt_more="more">more</a>
                        <div class="tooltip" style="display:none">
                            If this option is enabled, you can configure up to five port forwardings from Perfect Privacy servers to your computer. The ports are set randomly on the server side.
                        </div>
                    </div>
                    {% if pyview.custom_port_forwarding_enabled() == True %}
                        {{pyview.serverGroupView.render()}}
                        <br>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th scope="col"> Server</th>
                                    <th scope="col"> Server Port</th>
                                    <th scope="col"> Local Port</th>
                                    <th scope="col"> Valid until</th>
                                    <th scope="col"></th>
                                </tr>
                            </thead>
                            {{ pyview.custom_port_forwardings.render() }}           
                        </table>
                        <div class="row">
                            <div class="col-6">Forward to local port</div>
                            <div class="col-3">
                                <input class="form-check-input" type="text" value="12345" id="local_port_input">
                                <label class="form-check-label" for="local_port_input"> </label>
                            </div>
                            <div class="col-3">
                                <button onclick='pyview.subject.userapi.customPortForwardings.add($("#select_servergroup_input").val(), $("#local_port_input").val() )'>add</button>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-9">1-to-1 Port Forwarding</div>
                            <div class="col-3">
                                <button onclick='pyview.subject.userapi.customPortForwardings.add_one_to_one($("#select_servergroup").val() )'> add </button>
                            </div>
                        </div>
                    {% endif %}
                </section>
                {% if pyview.custom_port_forwarding_enabled() == True %}
                    <section>
                        <h3>
                            Auto Renew Port Forwarding
                            <div class="input">{{ pyview.auto_renew_port_forwarding.render() }} </div>
                        </h3>
                        <div>Automatically renew port forwarding after expiration</div>
                    </section>
                    <section>
                        <h3>
                            Email Notifications for Port Forwarding Renewal
                            <div class="input"> {{ pyview.email_port_forwarding_updates.render() }} </div>
                        </h3>
                        <div>Receive an email notification when port forwarding is renewed</div>
                    </section>
                {% endif %}
            </div>
        </div>
    '''

    def __init__(self, subject, parent):
        """
        :type subject: core.Core
        :type parent: gui.default.components.mainview.MainView
        """
        super(PortForwardingView, self).__init__(subject, parent)
        self.default_port_forwarding = CheckboxComponent(subject.userapi.default_port_forwarding, self)
        self.auto_renew_port_forwarding = CheckboxComponent(subject.userapi.auto_renew_port_forwarding, self)
        self.email_port_forwarding_updates = CheckboxComponent(subject.userapi.email_port_forwarding_updates,self)
        self.gpg_mail_only = CheckboxComponent(subject.userapi.gpg_mail_only, self)
        self.custom_port_forwardings = ObservableListView(self.subject.userapi.customPortForwardings.portforwardings, self, item_class=CustomPortForwardingRowItem, dom_element="tbody")
        self._custom_port_forwarding_enabled = len(self.subject.userapi.customPortForwardings.portforwardings) > 0
        self.serverGroupView = ServerGroupView(self.subject.userapi, self)
        self.add_observable(subject.userapi.customPortForwardings)
        self.add_observable(subject.userapi._server_groups)
        self._last_update_requested = 0

    def custom_port_forwarding_enabled(self):
        if self._custom_port_forwarding_enabled is True:
            return True
        return len(self.subject.userapi.customPortForwardings.portforwardings) > 0

    def set_custom_port_forwarding(self, value):
        if value is False and len(self.subject.userapi.customPortForwardings.portforwardings) > 0:
            return
        self._custom_port_forwarding_enabled = value
        self.update()

    def refresh(self):
        if self._last_update_requested + 3 > time.time():
            return
        self._last_update_requested = time.time()
        self.subject.userapi.request_update()


class CustomPortForwardingRowItem(PyHtmlView):
    DOM_ELEMENT = "tr"
    TEMPLATE_STR = '''
        <td> {{ pyview.subject.serverGroupId }}</td>
        <td> {{ pyview.subject.srcPort }}    </td>
        <td> {{ pyview.subject.dstPort }}    </td>
        <td> {{ pyview.subject.validUntil }} </td>
        <td> <button onclick='pyview.subject.remove()'>delete</button> </td>
    '''