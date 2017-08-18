import pytest
import rlp
from rlp.sedes import big_endian_int, binary

from vanilla.transactions import Transaction
from vanilla.keys import Key


class Params1(rlp.Serializable):
    fields = [
        ('x', big_endian_int),
        ('name', binary)
    ]
    def __init__(self, x, name):
        super().__init__(x,name)

class Params2(rlp.Serializable):
    fields = [
        ('y', big_endian_int),
        ('place', binary)
    ]
    def __init__(self, y, place):
        super().__init__(y,place)

class Params3(rlp.Serializable):
    fields = [
        ('z', big_endian_int)
    ]
    def __init__(self, z):
        super().__init__(y)


def test_transactions():
    p1 = Params1(20, 'dave')

    t1 = Transaction()
    t1.nonce = 2
    t1.value = 11
    t1.call = 'CREATE'
    t1.params = p1
    raw1 = t1.encode()
    assert(raw1)

    # decode outer and check
    tback = Transaction.decode(raw1)
    assert(2 == tback.nonce)
    assert(11 == tback.value)
    assert(b'CREATE' == tback.call)

    # decode inner and check
    pback = tback.decode_params(Params1)
    assert(20 == pback.x)
    assert(b'dave' == pback.name)

def test_signing_txs():
    bob = Key.generate()
    alice = Key.generate()

    # Bob send Tx to alice
    p2 = Params2(10, 'here')
    t1 = Transaction()
    t1.to = alice.address()
    t1.nonce = 1
    t1.value = 0
    t1.call = 'TRANSFER'
    t1.params = p2
    raw1 = t1.sign(bob).encode()
    assert(raw1)

    # Thaw the tx and check it
    tback = Transaction.decode(raw1)
    assert(1 == tback.nonce)
    assert(0 == tback.value)
    assert(b'TRANSFER' == tback.call)
    # sender was set in the sign
    assert(bob.address() == tback.sender)
    assert(alice.address() == tback.to)

    assert(Key.verify(bob.publickey(), tback.signature))
    # Just for the heck of it...
    assert(Key.verify(alice.publickey(), tback.signature) == False)

    pback = tback.decode_params(Params1)
    assert(10 == pback.x)
    assert(b'here' == pback.name)

def test_ok_with_no_params():
    bob = Key.generate()
    alice = Key.generate()

    # Bob send Tx to alice
    t1 = Transaction()
    t1.to = alice.address()
    t1.nonce = 1
    t1.value = 0
    t1.call = 'TRANSFER'
    raw1 = t1.sign(bob).encode()
    assert(raw1)

    # Thaw the tx and check it
    tback = Transaction.decode(raw1)
    assert(1 == tback.nonce)
    assert(0 == tback.value)
    assert(b'TRANSFER' == tback.call)
    # sender was set in the sign
    assert(bob.address() == tback.sender)
    assert(alice.address() == tback.to)

    assert(Key.verify(bob.publickey(), tback.signature))
    # Just for the heck of it...
    assert(Key.verify(alice.publickey(), tback.signature) == False)

    # Try to decode_params even through there's none
    pback = tback.decode_params(Params1)
    assert(None == pback)

def test_decoding_with_no_params():
    t1 = Transaction()
    t1.nonce = 2
    t1.value = 11
    t1.call = 'CREATE'
    raw1 = t1.encode()
    assert(raw1)

    tback = Transaction.decode(raw1)
    assert(2 == tback.nonce)
    assert(11 == tback.value)
    assert(b'CREATE' == tback.call)

    # nothing to decode = no params
    pback = tback.decode_params(Params1)
    assert(None == pback)


def test_decoding_with_wrong_params():
    p1 = Params1(20, 'dave')
    
    t1 = Transaction()
    t1.nonce = 2
    t1.value = 11
    t1.call = 'CREATE'
    t1.params = p1
    raw1 = t1.encode()
    assert(raw1)

    tback = Transaction.decode(raw1)
    assert(2 == tback.nonce)
    assert(11 == tback.value)
    assert(b'CREATE' == tback.call)

    # decode with wrong params class raises and exception
    with pytest.raises(Exception):
        pback = tback.decode_params(Params3)
        assert(pback)
