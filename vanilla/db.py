"""
 Using sqlite3 for key/value store...what!?  Here's why:
 existing tech (leveldb, codernitydb, etc...) either doesn't
 support windows, not ported to Python 3, or both. This approach
 gives the most flexibility for now...and it works.
"""
import sqlite3
import os.path
from trie.db.base import BaseDB

KVTABLE = "CREATE TABLE blobkey(k BLOB PRIMARY KEY, v BLOB)"

class VanillaDB(BaseDB):

    def __init__(self, dbname):
        self.dbfile = dbname
        self.is_new = not os.path.exists(self.dbfile)
        self.db = None
        self.db = sqlite3.connect(self.dbfile)
        if self.is_new:
            cursor = self.db.cursor()
            cursor.execute(KVTABLE)
            self.db.commit()

    def get(self, key):
        cursor = self.db.cursor()
        cursor.execute("SELECT v FROM blobkey WHERE k=?", (key,))
        row = cursor.fetchone()
        return row[0] if row is not None else None

    def set(self, key, value):
        cursor = self.db.cursor()
        if self.exists(key):
            # Do update
            cursor.execute("UPDATE blobkey SET v=? WHERE k=?", (value, key))
        else:
            # Do insert
            cursor.execute("INSERT INTO blobkey (k,v) VALUES (?,?)",(key,value))
        self.db.commit()

    def exists(self, key):
        if self.get(key):
            return True
        return False

    def delete(self, key):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM blobkey WHERE k = ?", (key,))
        self.db.commit()

    def close(self):
        if self.db:
            self.db.close()

    #
    # Snapshot API (ignored, even in Trie)
    #
    def snapshot(self):
        return b''

    def restore(self, snapshot):
        pass
