from pyhtmlgui import PyHtmlView, ObservableListView
from gui.common.components import CheckboxComponent, SelectComponent
from config.constants import VPN_PROTOCOLS, OPENVPN_CIPHER,OPENVPN_PROTOCOLS, OPENVPN_TLS_METHOD,OPENVPN_DRIVER
import re

class LogsView(PyHtmlView):
    TEMPLATE_STR = '''
        <div class="inner">
            <button style="float:right" onclick='pyview.copy_to_clipboard()'>To Clipboard</button>
            <button style="float:right" onclick='pyview.clear_log()'>Clear</button>
            <h1 style="float:left">
                Internal Log
            </h1>           
            <input id="filter_str" type="text" onkeyup="pyview.set_filter(document.getElementById('filter_str').value)" value="{{filter_str}}" placeholder="filter"> </input>
            <div  style="max-height: 100vh;overflow: auto;margin-bottom: 30px;">
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

    def clear_log(self):
        self.subject.global_logger.clear()

    def copy_to_clipboard(self):
        lines = []
        for item in self.subject.global_logger.logs:
            lines.append("%s | %s | %s" % (item.timestamp.split(" ")[1], item.name, item.message ))
        self.eval_javascript("pyhtmlapp.copy_to_clipboard(args.lines)", skip_results=True, lines="\n".join(lines))

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
        {{pyview.timestamp()}} | {{pyview.subject.name}} | {{pyview.subject.message}}
    '''
    def __init__(self, subject, parent):
        self._on_subject_updated = None  # logs don't change, so don't observe every entry
        super().__init__(subject, parent)

    def timestamp(self):
        return self.subject.timestamp.split(" ")[1]