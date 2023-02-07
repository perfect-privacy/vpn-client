from pyhtmlgui import Observable


class GenericState(Observable):
    _DEFAULT = None
    def __init__(self):
        super().__init__()
        self._current_state = self.__class__._DEFAULT
        self._current_message = None
        self._valid_states = [value for key,value in self.__class__.__dict__.items() if not (key.startswith("__") and key.endswith("__")) ]

    def set(self, value, message = None):
        if value not in self._valid_states:
            raise Exception("Unknown state '%s' for '%s'" %  (value, self.__class__.__name__))
        if self._current_state != value or self._current_message != message:
            self._current_state = value
            self._current_message = message
            self.notify_observers(new_state=value)

    def get(self):
        return self._current_state

