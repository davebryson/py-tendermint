import pytest
import rlp
from rlp.sedes import big_endian_int
from vanilla.app import VanillaApp
from vanilla.abci.messages import *
from vanilla.abci.application import Result
from vanilla.transactions import Transaction

"""
def test_setup():
    home = home_dir('.bad')
    with pytest.raises(Exception, message="Cannot find app directory: ".format(home)):
        setup_app(home)
"""

def test_validate_tx_decorator():
    app = VanillaApp("test")
    #app.test_mode = True

    with pytest.raises(TypeError, message="The hello function is missing the 2 required param(s)"):
        @app.validate_transaction()
        def hello():
            pass

    # Without any validation check - it just passes
    t = Transaction()
    t.nonce = 1
    raw = t.encode()

    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.check_tx.code == 0)

    # Bad callback
    @app.validate_transaction()
    def hello(tx, storage):
        pass

    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.check_tx.code == 1)

    # proper callback
    @app.validate_transaction()
    def hello(tx, storage):
        if tx.nonce == 1:
            return Result.ok()
        return Result.error()

    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.check_tx.code == 0)

    t = Transaction()
    t.nonce = 2
    raw = t.encode()

    r = to_request_check_tx(raw)
    resp = app.check_tx(r)
    assert(resp.check_tx.code == 1)

def test_tx_handler_decorator():
    app = VanillaApp("test")
    #app.test_mode = True

    with pytest.raises(TypeError, message="The hello function is missing the 2 required param(s)"):
        @app.process_transaction('transfer')
        def hello(tx):
            pass

    with pytest.raises(TypeError, message="Missing call name for the Tx handler"):
        @app.process_transaction()
        def hello(tx):
            pass

    # Test it errors on mis-matched call names
    t = Transaction()
    t.call = 'CREATE'
    raw = t.encode()

    @app.process_transaction("NO MATCH HERE")
    def hello(tx, storage):
        pass

    r = to_request_deliver_tx(raw)
    resp = app.deliver_tx(r)
    assert(resp.deliver_tx.code == 1)
    assert(resp.deliver_tx.log == "No matching Tx handler")


    # test it errors if the handler doesn't return an result
    @app.process_transaction('CREATE')
    def hello(tx, storage):
        pass

    r = to_request_deliver_tx(raw)
    resp = app.deliver_tx(r)
    assert(resp.deliver_tx.code == 1)
    assert(resp.deliver_tx.log == "Transaction handler did not return a result")


    # does it actually work?
    @app.process_transaction('CREATE')
    def do_create(tx, storage):
        return Result.ok(log="peachykeen")

    r = to_request_deliver_tx(raw)
    resp = app.deliver_tx(r)
    assert(resp.deliver_tx.code == 0)
    assert(resp.deliver_tx.log == "peachykeen")

## Setup for test below

def _delivertx(app, nonce,call,x, y=0):
    t = Transaction()
    t.nonce = nonce
    t.call = call
    t.params = Params(x,y)

    r = to_request_deliver_tx(t.encode())
    return app.deliver_tx(r)

def _checktx(app, nonce,call,x, y=0):
    t = Transaction()
    t.nonce = nonce
    t.call = call
    t.params = Params(x,y)

    r = to_request_check_tx(t.encode())
    return app.check_tx(r)

class Params(rlp.Serializable):
    fields = [
        ('x', big_endian_int),
        ('y', big_endian_int)
    ]
    def __init__(self, x, y):
        super().__init__(x,y)

def test_quasi_flow():
    BADNONCE = 3

    app = VanillaApp("test")
    #app.test_mode = True
    app.mock_test_state = 0

    @app.validate_transaction()
    def hello(tx, storage):
        if tx.nonce == app.mock_test_state:
            app.mock_test_state += 1
            return Result.ok()
        return Result.error(code=BADNONCE)

    @app.process_transaction('add')
    def add_values(tx, storage):
        p = tx.decode_params(Params)
        value = p.x + p.y
        return Result.ok(data=str(value))

    @app.process_transaction('sub')
    def sub_values(tx, storage):
        p = tx.decode_params(Params)
        value = p.x - p.y
        return Result.ok(data=str(value))

    r = _checktx(app, app.mock_test_state,'add',1)
    assert(r.check_tx.code == 0)
    r = _checktx(app, app.mock_test_state,'add',1)
    assert(r.check_tx.code == 0)
    r = _checktx(app, 10,'add',1)
    assert(r.check_tx.code == BADNONCE)

    r = _delivertx(app, app.mock_test_state,'add',1,2)
    assert(r.deliver_tx.code == 0)
    assert(r.deliver_tx.data == b'3')

    r = _delivertx(app, app.mock_test_state,'sub',10,9)
    assert(r.deliver_tx.code == 0)
    assert(r.deliver_tx.data == b'1')
