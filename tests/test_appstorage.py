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
        storage.unconfirmed.put_data(b'count', int_to_big_endian(10))
        storage.unconfirmed.put_data(b'name', b'dave')

    @app.querystate('nonce')
    def get_nonce(req, storage):
        acct = storage.confirmed.get_account(req)
        if acct:
            return Result.ok(data=acct.nonce)
        return Result.ok()

    @app.querystate('count')
    def get_count(req, storage):
        v = storage.unconfirmed.get_data(req)
        return Result.ok(data=v)

    @app.querystate('name')
    def get_name(req, storage):
        v = storage.unconfirmed.get_data(req)
        return Result.ok(data=v)

    app.mock_run()


    req = to_request_query(path='nonce', data=bob.address())
    resp = app.query(req)
    # Number are in big_endian format
    assert(0 == big_endian_to_int(resp.query.value))

    req = to_request_query(path='count', data=b'count')
    resp = app.query(req)
    # Number are in big_endian format
    assert(10 == big_endian_to_int(resp.query.value))

    req = to_request_query(path='name', data=b'name')
    resp = app.query(req)
    assert(b'dave' == resp.query.value)
