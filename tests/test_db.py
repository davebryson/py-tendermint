import os

from tendermint.db import VanillaDB
from tendermint.utils import home_dir

def test_database():
    dbfile = home_dir('temp', 'test.db')
    db = VanillaDB(dbfile)

    db.set(b'dave',b'one')
    result = db.get(b'dave')
    assert(b'one' == result)

    db.set(b'dave',b'two')
    result = db.get(b'dave')
    assert(b'two' == result)

    assert(None == db.get(b'doesntexist'))
    assert(db.exists(b'dave'))

    db.delete(b'dave')
    assert(db.exists(b'dave') == False)

    if os.path.exists(dbfile):
        os.remove(dbfile)
