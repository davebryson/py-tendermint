import pytest

import rlp
from rlp.sedes import big_endian_int

# only used here for testing
from vanilla.abci.messages import *

from vanilla import VanillaApp, Result, Transaction

from vanilla.keys import Key
from vanilla.accounts import Account
from vanilla.utils import big_endian_to_int, int_to_big_endian

bob = Key.generate()
alice = Key.generate()

def test_queries():

    app = VanillaApp("")

    @app.on_initialize()
    def create_accts(storage):
        ba = Account.create_account(bob.publickey())
        aa = Account.create_account(alice.publickey())
        storage.confirmed.update_account(ba)
        storage.confirmed.update_account(aa)
        storage.confirmed.put_data(b'count', int_to_big_endian(10))
        storage.confirmed.put_data(b'name', b'dave')

    app.mock_run()


    req = to_request_query(path='nonce', data=bob.address())
    resp = app.query(req)
    assert(6 == resp.query.code)

    req = to_request_query(path='/data', data=b'count')
    resp = app.query(req)

    # Number are in big_endian format
    assert(0 == resp.query.code)
    assert(10 == big_endian_to_int(resp.query.value))
