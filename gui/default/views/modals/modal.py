from pyhtmlgui import PyHtmlView


class Modal(PyHtmlView):
    def __init__(self, subject, parent):
        """
        :type subject: core.Core
        :type parent: MainView
        """
        super().__init__(subject, parent)
        self.display = False

    def show(self):
        self.display = True
        if self.is_visible is True:
            self.update()

    def hide(self):
        self.display = False
        if self.is_visible is True:
            self.update()
