from pyhtmlgui import PyHtmlView

from .dashboard import Dashboard
from .wizards.wizard_full_setup import Wizard_full_setup

class MainView(PyHtmlView):

    TEMPLATE_STR = '''
        <div class="container-fluid">
            <div class="row h-1of12 top_row" >
                <div class="col-4">
                    <img class="top_icons" src="/static/img/header/pp_top.png" alt="logo">
                </div>
                <div class="top_corner col-8">
                    <img class="top_icons" src="/static/img/header/power2.png" alt="power"> 74% | 
                    <img class="top_icons" src="/static/img/header/connected.png" alt="connected"> Amsterdam
                </div>      
            </div>
            {{ pyview.current_page.render() }}
        </div>
    '''

    def __init__(self, subject, parent):
        """
        :type subject: core.Core
        :type parent: None
        """
        super(MainView, self).__init__(subject, parent)
        self.dashboard = Dashboard(subject, self)
        self.wizard_full_setup = Wizard_full_setup(subject, self, after_last=self.on_wizard_full_setup_finished, on_back=self.on_wizard_full_setup_exit)

        if self.subject.settings.first_start_wizard_was_run.get() is True: # FIXME
            self.current_page = self.wizard_full_setup
        else:
            self.current_page = self.dashboard

    def on_wizard_full_setup_finished(self):
        if self.subject.settings.first_start_wizard_was_run.get() is False:
            self.subject.settings.first_start_wizard_was_run.set(True)
        self.set_currentpage(self.dashboard)
    def on_wizard_full_setup_exit(self):
        self.set_currentpage(self.dashboard)


    def set_currentpage(self, new_page):
        if self.current_page != new_page:
            self.current_page = new_page
            self.update()
