from pyhtmlgui import PyHtmlView
from .wizard import Wizard

from .wizard_login import Wizard_Login
from .wizard_accesspoint import Wizard_WlanAP

class Wizard_full_setup(Wizard):
    TEMPLATE_STR = '''
        {{ pyview.current_page.render() }}
    '''

    def __init__(self, subject, parent, on_back, after_last, **kwargs):
        """
        :type subject: core.Core
        :type parent: gui.privacypi.components.mainview.MainView
        """
        super(Wizard_full_setup, self).__init__(subject, parent, on_back, after_last, **kwargs)
        self.pages = [
            Wizard_Login( subject, parent, on_back=self.prev, after_last=self.next),
            Wizard_WlanAP(subject, parent, on_back=self.prev, after_last=self.next),
        ]
        self.current_page_index = 0
        self.current_page = self.pages[self.current_page_index]
        self.on_back = on_back
        self.after_last = after_last

