import pytest

import rlp
from rlp.sedes import big_endian_int

# only used here for testing
from abci.messages import *

from tendermint import TendermintApp, Transaction

from tendermint.keys import Key
from tendermint.accounts import Account
from tendermint.utils import big_endian_to_int, int_to_big_endian

bob = Key.generate()
alice = Key.generate()

def test_app_api():
    app = TendermintApp("")

    @app.on_initialize()
    def create_accts(db):
        ba = Account.create_account(bob.publickey())
        aa = Account.create_account(alice.publickey())
        db.update_account(ba)
        db.update_account(aa)
        db.put_data(b'count', int_to_big_endian(10))
        db.put_data(b'name', b'dave')

    @app.on_query('/count')
    def get_count(key, db):
        return db.get_data(key)

    # Run the app in mock mode (doesn't need tendermint)
    app.mock_run()

    # Run requests against API

    # Note: /tx_nonce is built in
    req = to_request_query(path='/tx_nonce', data=bob.address())
    resp = app.query(req)
    assert(resp.code == 0)
    assert(0 == big_endian_to_int(resp.value))

    req = to_request_query(path='/count', data=b'count')
    resp = app.query(req)
    assert(0 == resp.code)
    assert(10 == big_endian_to_int(resp.value))

    # Try some transactions

    # Check tx First
    # Missing sender - signature
    t = Transaction()
    raw = t.encode()
    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.code == 1)
    assert(resp.log == 'No Sender - is the Tx signed?')

    # No account
    n = Key.generate()
    t = Transaction()
    t.sender = n.address()
    raw = t.encode()
    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.code == 1)
    assert(resp.log == 'Account not found')

    # Bad nonce
    t = Transaction()
    t.nonce = 10
    raw = t.sign(bob).encode()
    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.code == 1)
    assert(resp.log == 'Bad nonce')

    # Bad balance
    t = Transaction()
    t.nonce = 0
    t.value = 100
    raw = t.sign(alice).encode()
    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.code == 1)
    assert(resp.log == 'Insufficient balance for transfer')

    # Finally good check transaction
    t = Transaction()
    t.nonce = 1
    raw = t.sign(alice).encode()
    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.code == 0)


    # Test deliver Tx
