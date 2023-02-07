from pyhtmlgui import PyHtmlView
from gui.common.components import CheckboxComponent, SelectComponent

class PublicIpItemView(PyHtmlView):
    TEMPLATE_STR = ''' 
    {% if pyview.subject.public_ip or pyview.proto == "IPv4" %}
        <h1>Public {{pyview.proto}}</h1>
        <h2 style="text-align:center">{{ pyview.subject.public_ip }}</h2>
        <h3 style="text-align:center">{{ pyview.subject.public_rdns }}</h3>
        <h3 style="text-align:center">
            {{ pyview.subject.public_city }}{% if pyview.subject.public_city != "" %},{% endif %}
            {{ pyview.subject.public_country }}
        </h3>
    {% endif %}
    '''
    def __init__(self, subject, parent, proto, **kwargs):
        super().__init__(subject, parent, **kwargs)
        self.proto = proto

class PublicIpView(PyHtmlView):
    TEMPLATE_STR = '''
        {% if pyview.subject.userapi.credentials_valid.get() != True %}
            <div class="not_logged_in"> Login to change your public ip settings. </div>
        {% endif %}    
            
        <div class="inner">
            {{ pyview.result4.render() }}
            {{ pyview.result6.render() }}
            <br>
            <h3 style="text-align:center">
                {% if pyview.subject.ipcheck.state == "ACTIVE"%}
                    <button disabled>Checking..</button> </h3>
                {% else %}
                    <button onclick="pyview.subject.ipcheck.check_now()">Check Now</button> </h3>
                {% endif %}
            <br>
            <div class="boxes">
                <section>
                    <h3>
                        NeuroRouting
                        <div class="input"> {{ pyview.neuro_routing.render() }} </div>
                    </h3> 
                    <div>
                        Your traffic will brought as close as possible to the destination within 
                        the encrypted VPN network. That way, your traffic is only exposed to the internet where it is unavoidable.
                    </div>
                </section>
                
                {% if pyview.subject.settings.interface_level.get() != "simple" %}
                    <section>
                        <h3>
                            Enforce Primary Ip
                            <div class="input"> {{ pyview.random_exit_ip.render() }} </div>
                        </h3> 
                        <div>There are services that require a primary IP address. Turn it on only when you need it.</div>
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
        super(PublicIpView, self).__init__(subject, parent)
        self.random_exit_ip = CheckboxComponent(subject.userapi.random_exit_ip, self, label="")
        self.neuro_routing = CheckboxComponent(subject.userapi.neuro_routing, self, label="")
        self.result4 = PublicIpItemView(subject.ipcheck.result4, self, proto="IPv4")
        self.result6 = PublicIpItemView(subject.ipcheck.result6, self, proto="IPv6")
        self.add_observable(subject.ipcheck, self._on_subject_updated)