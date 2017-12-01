import pytest
import rlp
from rlp.sedes import big_endian_int, binary

from tendermint.transactions import Transaction
from tendermint.keys import Key
from tendermint.utils import to_hex, from_hex, is_hex

class ExObj(rlp.Serializable):
    fields = [
        ('x', big_endian_int),
        ('y', big_endian_int),
        ('title', binary)
    ]

class NoUsed(rlp.Serializable):
    fields = [
        ('name', binary)
    ]


def test_transactions():
    bob = Key.generate()
    alice = Key.generate()

    t1 = Transaction()
    t1.to = alice.address()
    t1.nonce = 2
    t1.value = 11
    t1.call = 'CREATE'
    t1.params = ExObj(20, 0, 'dave')
    raw1 = t1.sign(bob).encode()
    assert(raw1)

    # decode outer transaction and check
    tback = Transaction.decode(raw1)
    assert(2 == tback.nonce)
    assert(11 == tback.value)
    assert(b'CREATE' == tback.call)
    assert(bob.address() == tback.sender)
    assert(alice.address() == tback.to)
    assert(Key.verify(bob.publickey(), tback.signature))

    # decode params and check
    pback = tback.decode_params(ExObj)
    assert(20 == pback.x)
    assert(b'dave' == pback.title)

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
    pback = tback.decode_params(ExObj)
    assert(None == pback)

def test_decoding_with_wrong_params():
    t1 = Transaction()
    t1.nonce = 2
    t1.value = 11
    t1.call = 'CREATE'
    t1.params = ExObj(20, 0, 'dave')
    raw1 = t1.encode()
    assert(raw1)

    tback = Transaction.decode(raw1)
    assert(2 == tback.nonce)
    assert(11 == tback.value)
    assert(b'CREATE' == tback.call)

    # decode with wrong params class raises and exception
    with pytest.raises(Exception):
        pback = tback.decode_params(NotUsed)
        assert(pback)

def test_format_convertions():
    t1 = Transaction()
    t1.nonce = 2
    t1.value = 11
    t1.call = 'CREATE'

    raw = t1.encode()
    hexvalue = to_hex(raw)

    assert(is_hex(hexvalue))

    tback = Transaction.decode(from_hex(hexvalue))
    assert(2 == tback.nonce)
    assert(11 == tback.value)

def test_tx():
    t2 = Transaction()
    t2.params = ('hello',1)
    raw2 = t2.encode()
    t2back = Transaction.decode(raw2)
    p = t2back.decode_params()
    assert(p == [b'hello',b'\x01'])
