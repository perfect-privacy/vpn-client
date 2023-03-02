import sqlite3
import json
from pyhtmlgui import Observable
from config.files import SETTINGS_FILE
from threading import Lock

class PermanentStorage():
    def __init__(self):
        self.tablename = "KVTABLE"
        self.connection = sqlite3.connect(SETTINGS_FILE, isolation_level=None, check_same_thread = False)
        self.cursor = self.connection.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS ' + self.tablename + ' (key text PRIMARY KEY, value text)')
        self.lock = Lock()

    def get(self, key):
        try:
            self.lock.acquire()
            self.cursor.execute('SELECT value FROM ' + self.tablename + ' WHERE key=?', [key, ])
            value = self.cursor.fetchone()[0]
        finally:
            self.lock.release()
        return json.loads(value)[0]

    def set(self, key, value):
        try:
            self.lock.acquire()
            value = json.dumps([value])
            self.cursor.execute('REPLACE INTO ' + self.tablename + ' (key, value) VALUES(?, ?)', [key, value])
        finally:
            self.lock.release()

class PermanentProperty(Observable):
    permanentStorage = None

    def __init__(self, name, default_value):
        self.name = name
        self._permanentStorage.set("%s_default_value" % name, default_value)
        try:
            self._permanentStorage.get(name)
        except Exception as e:
            self._permanentStorage.set(name, default_value)
        super().__init__()

    @property
    def _permanentStorage(self):
        if PermanentProperty.permanentStorage is None:
            PermanentProperty.permanentStorage = PermanentStorage()
        return PermanentProperty.permanentStorage

    def set(self, new_value, force_notify=False):
        changed = False
        if self.get() != new_value:
            changed = True
            self._permanentStorage.set(self.name, new_value)
        if changed is True or force_notify is True:
            self.notify_observers()

    def get(self):
        return self._permanentStorage.get(self.name)

    def default(self): # reset to default
        self.set(self._permanentStorage.get("%s_default_value" % self.name))

