from pyhtmlgui import Observable

class RemoteProperty(Observable):
    def __init__(self, key, queue, readonly=False):
        super().__init__()
        self.key = key
        self.queue = queue
        self.value = None

    def set(self, value):
        if self.value != value:
            self.value = value
            self.queue.update({self.key: self.value})
            self.notify_observers()

    def get(self):
        return self.value

    def update(self, value): # data from api response
        if self.value != value:
            self.value = value
            self.notify_observers()

