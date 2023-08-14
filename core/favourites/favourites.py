import json
from pyhtmlgui import Observable, ObservableDict
from core.libs.permanent_property import PermanentProperty

class Favourites(Observable):
    def __init__(self, core):
        super().__init__()
        self._core = core
        self._identifiers_str = PermanentProperty(self.__class__.__name__ + ".favourites_str", json.dumps([]))
        self._identifiers_list = json.loads(self._identifiers_str.get())
        self.favourites = ObservableDict()
        for identifier in self._identifiers_list:
            systems = self._core.vpnGroupPlanet.search_by_identifier(identifier)
            if systems is not None and len(systems) > 0:
                self.favourites[identifier] = systems

    def add(self, identifier):
        if identifier not in self._identifiers_list:
            systems = self._core.vpnGroupPlanet.search_by_identifier(identifier)
            if systems is not None and len(systems) > 0:
                self._identifiers_list.append(identifier)
                self._identifiers_str.set(json.dumps(self._identifiers_list))
                self.favourites[identifier] = systems
                self.notify_observers()

    def remove(self, identifier):
        if identifier in self._identifiers_list:
            self._identifiers_list.remove(identifier)
            self._identifiers_str.set(json.dumps(self._identifiers_list))
            if identifier in self.favourites:
                del self.favourites[identifier]
            self.notify_observers()

    def contains(self, identifier):
        return identifier in self._identifiers_list


