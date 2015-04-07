import threading


class ActiveChatsManager():
    #dictionary of active chats.
    _active_chats = {}
    _lock = None

    def __init__(self):
        self._lock = threading.Lock()

    def get_keys(self):
        return self._active_chats.keys()

    def has_key(self, key):
        return key in self._active_chats

    def get(self, key, default=[]):
        return self._active_chats.get(key, default)

    def add(self, key, connection):
        try:
            self._lock.acquire()
            if not key in self._active_chats:
                self._active_chats[key] = []
            if not connection in self._active_chats[key]:
                self._active_chats[key].append(connection)
        finally:
            self._lock.release()

    def remove(self, key, connection):
        try:
            self._lock.acquire()
            if key in self._active_chats:
                self._active_chats[key].remove(connection)
                if len(self._active_chats[key]) == 0:
                    del self._active_chats[key]
        finally:
            self._lock.release()



