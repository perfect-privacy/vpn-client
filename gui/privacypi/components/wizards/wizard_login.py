from pyhtmlgui import PyHtmlView
from .wizard import Wizard

class Wizard_Login(Wizard):
    TEMPLATE_STR = '''
        {{ pyview.current_page.render() }}
    '''

    def __init__(self, subject, parent, on_back, after_last, **kwargs):
        super(Wizard_Login, self).__init__(subject, parent, on_back, after_last, **kwargs)
        self.pages = [
            Wizard_Login_Page_1_Info(subject, parent),
            Wizard_Login_Page_2_Username(subject, parent),
            Wizard_Login_Page_3_Password(subject, parent),
        ]
        self.current_page_index = 0
        self.current_page = self.pages[self.current_page_index]
        self.on_back = on_back
        self.after_last = after_last


class Wizard_Login_Page_1_Info(PyHtmlView):
    TEMPLATE_STR = '''
       pp login eingeben
       <button onclick='pyhtmlgui.call(pyview.parent.prev)'>prev</button>
       <button onclick='pyhtmlgui.call(pyview.parent.next)'>next</button>

    '''

    def __init__(self, subject, parent):
        super(Wizard_Login_Page_1_Info, self).__init__(subject, parent)


class Wizard_Login_Page_2_Username(PyHtmlView):
    TEMPLATE_STR = '''
        input username
               <button onclick='pyhtmlgui.call(pyview.parent.prev)'>prev</button>
       <button onclick='pyhtmlgui.call(pyview.parent.next)'>next</button>
    '''

    def __init__(self, subject, parent):
        super(Wizard_Login_Page_2_Username, self).__init__(subject, parent)


class Wizard_Login_Page_3_Password(PyHtmlView):
    TEMPLATE_STR = '''
        input password
               <button onclick='pyhtmlgui.call(pyview.parent.prev)'>prev</button>
       <button onclick='pyhtmlgui.call(pyview.parent.next)'>next</button>
    '''

    def __init__(self, subject, parent):
        super(Wizard_Login_Page_3_Password, self).__init__(subject, parent)

