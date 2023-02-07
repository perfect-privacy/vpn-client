from pyhtmlgui import PyHtmlView
from .wizard import Wizard

class Wizard_WlanAP(Wizard):
    TEMPLATE_STR = '''
        {{ pyview.current_page.render() }}
    '''

    def __init__(self, subject, parent, on_back, after_last, **kwargs):
        super(Wizard_WlanAP, self).__init__(subject, parent, on_back, after_last, **kwargs)
        self.pages = [
            Wizard_WlanAP_Page_1_Info(subject, self),
            Wizard_WlanAP_Page_2_Username(subject, self),
        ]
        self.current_page_index = 0
        self.current_page = self.pages[self.current_page_index]

class Wizard_WlanAP_Page_1_Info(PyHtmlView):
    TEMPLATE_STR = '''
      Wizard_WlanAP_Page_1_Info
           <button onclick='pyhtmlgui.call(pyview.parent.prev)'>prev</button>
       <button onclick='pyhtmlgui.call(pyview.parent.next)'>next</button>
    '''
    def __init__(self, subject, parent):
        super(Wizard_WlanAP_Page_1_Info, self).__init__(subject, parent)

class Wizard_WlanAP_Page_2_Username(PyHtmlView):
    TEMPLATE_STR = '''
        Wizard_WlanAP_Page_2_Username
               <button onclick='pyhtmlgui.call(pyview.parent.prev)'>prev</button>
       <button onclick='pyhtmlgui.call(pyview.parent.next)'>next</button>
    '''

    def __init__(self, subject, parent):
        super(Wizard_WlanAP_Page_2_Username, self).__init__(subject, parent)

