import threading
# import datetime

class VoteManager():

    def __init__(self):
        self._votes = {}
        self._lock = threading.Lock()

    def has_key(self, key):
        return key in self._votes

    def open_vote(self, key, timeout, callback):
        try:
            self._lock.acquire()
            if not key in self._votes.keys():
                item = VoteItem(callback)
                self._votes[key] = item
                timer = threading.Timer(timeout, item.close)
                timer.start()
        finally:
            self._lock.release()

    def vote(self, key, voter, vote=False, override=False):
        try:
            self._lock.acquire()
            if key in self._votes.keys():
                self._votes[key].vote(voter, vote, override)
        finally:
            self._lock.release()


class VoteItem:
    def __init__(self, callback):
        self._results = {}
        self._callback = callback

    def vote(self, key, vote=False, override=False):
        if override or not key in self._results.keys():
            self._results[key] = vote

    def close(self):
        return self._callback(self._results)

