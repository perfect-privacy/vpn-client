from pyhtmlgui import PyHtmlView

class Wizard(PyHtmlView):
    def __init__(self, subject, parent, on_back, after_last, **kwargs):
        super(Wizard, self).__init__(subject, parent)
        self.pages = []
        self.current_page_index = 0
        self.on_back = on_back
        self.after_last = after_last

    def prev(self):
        self.current_page_index -= 1
        if self.current_page_index < 0:
            self.current_page_index = 0
            if self.on_back is not None:
                self.on_back()
        else:
            self.current_page = self.pages[self.current_page_index]
            self.update()

    def next(self):
        self.current_page_index += 1
        if self.current_page_index == len(self.pages):
            self.current_page_index = 0
            self.after_last()
        else:
            self.current_page = self.pages[self.current_page_index]
            self.update()
