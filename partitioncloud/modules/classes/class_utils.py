from enum import Enum
import sqlite3
import sys

class RealObject(Enum):
    USER       = 0
    GROUPE     = 1
    ALBUM      = 2
    PARTITION  = 3
    ATTACHMENT = 4
    NONE       = 5

class FakeObject:
    """
    Some times, you don't need access to the methods of a class,
    but just its data. We don't want to do unnecessary sql requests for that.

    When you try to access a method or an unknown attribute,
    a real object is created from the competent module

    TODO: we obviously don't want to call FakeObject(<FakeObject>, ..), as dict(<FakeObject>) does not behave well
    """
    def __init__(self, data: sqlite3.Row, proxy_class: RealObject):
        self.__data = dict(data)
        self.__proxy = None
        self.__proxy_class = proxy_class

    def __create_proxy(self):
        if self.__proxy is not None:
            return

        match self.__proxy_class:
            case RealObject.USER:
                from .user import User
                self.__proxy = User(user_id=self.id)
            case RealObject.GROUPE:
                from .groupe import Groupe
                self.__proxy = Groupe(self.uuid)
            case RealObject.ALBUM:
                from .album import Album
                self.__proxy = Album(uuid=self.uuid)
            case RealObject.PARTITION:
                from .partition import Partition
                self.__proxy = Partition(uuid=self.uuid)
            case RealObject.ATTACHMENT:
                from .attachment import Attachment
                self.__proxy = Attachment(uuid=self.uuid)

    def __getattr__(self, key):
        if key in self.__data and self.__proxy is None:
            return self.__data[key]

        match key:
            case "__proxy_class":
                return self.__proxy_class
            case "__proxy":
                return self.__proxy
            case "__data":
                return self.__data

        if key.startswith("_User") and self.__proxy_class == RealObject.USER:
            #TODO : this is really weird (and ugly as possible), but classes/user.py:395 tries to access _User__proxy_class
            return self.__getattr__(key[5:])

        self.__create_proxy()
        return getattr(self.__proxy, key)


    def __getitem__(self, key):
        self.__create_proxy()

        if self.__proxy is not None and key in self.__proxy:
            return self.__proxy[key]
        raise NotImplementedError(f"Hey, someone is accessing ['{key}'] via __getitem__")

    def __repr__(self):
        if self.__proxy is None:
            return "<FakeObject (no proxy)>"
        return f"<FakeObject {self.__proxy}>"