from pyhtmlgui import PyHtmlView, ObservableListView
from gui.common.components import CheckboxComponent, SelectComponent
from config.constants import VPN_PROTOCOLS, OPENVPN_CIPHER,OPENVPN_PROTOCOLS, OPENVPN_TLS_METHOD,OPENVPN_DRIVER
import re

class LogsView(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="inner">
            <h1>Internal Log</h1>
            <p></p>
            
            <input id="filter_str" type="text" onkeyup="pyview.set_filter(document.getElementById('filter_str').value)" value="{{filter_str}}" placeholder="filter"> </input>
            <div  style="height:40em;overflow:auto;">
                {{ pyview.log.render() }}
            </div>
        </div> 
    '''

    def __init__(self, subject, parent):
        """
        :type subject: core.Core
        :type parent: gui.default.components.mainview.MainView
        """
        super(LogsView, self).__init__(subject, parent)
        self.log = ObservableListView(subject.global_logger.logs, self, filter_function=lambda x:self._filter(x), item_class=LogListItem)
        self.filter_str = ""

    def _filter(self, item): # element is removed by filter
        return (re.search(self.filter_str, item.subject.levelname, re.IGNORECASE) == None and
            re.search(self.filter_str, item.subject.message, re.IGNORECASE) == None and
            re.search(self.filter_str, item.subject.name, re.IGNORECASE) == None)

    def set_filter(self, value):
        if self.filter_str != value:
            self.filter_str = value
            if self.is_visible:
                self.log.update()


class LogListItem(PyHtmlView):
    DOM_ELEMENT = "div"
    TEMPLATE_STR = '''
        {{pyview.subject.timestamp}}, {{pyview.subject.levelname}}, {{pyview.subject.name}}, {{pyview.subject.message}}
    '''
    def __init__(self, subject, parent):
        self._on_subject_updated = None  # logs don't change, so don't observe every entry
        super().__init__(subject, parent)
