class SessionProvider():
    def __init__(self):
        self._sessions = {}

    def get_keys(self):
        return self._sessions.keys()

    def get_session(self, key):
        return self._sessions[key]

    def add_session(self, key, session):
        self._sessions[key] = session

    def remove_session(self, key):
        if key in self._sessions:
            del self._sessions[key]

    def clear(self):
        for key in self._sessions.keys():
            del self._sessions[key]