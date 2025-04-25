import sqlite3

class FakeObject:
    """
    Some times, you don't need access to the methods of a class,
    but just its data. We don't want to do unnecessary sql requests for that.

    Obviously, we trade a small performance gain for a future headache,
    but that's assumed
    """
    def __init__(self, data: sqlite3.Row):
        self._data = dict(data)

    def __getattr__(self, key):
        return self._data[key]