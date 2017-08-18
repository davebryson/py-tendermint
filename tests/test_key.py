
import pytest
import nacl.bindings
import nacl.exceptions
from vanilla.keys import Key, create_address
from vanilla.utils import from_hex, str_to_bytes, keccak

def test_signing():
    bob = Key.generate()
    alice = Key.generate()

    # Check the address
    addy = bob.address(tohex=False)
    assert(addy)
    assert(len(addy) == 20)

    # Check the publickey
    assert(len(bob.publickey()) == nacl.bindings.crypto_sign_PUBLICKEYBYTES)

    # Sign and verify
    bob_sig = bob.sign(b'hello')
    bob_raw_pk = bob.publickey()
    bob_hex_pk = bob.publickey(tohex=True)

    assert(Key.verify(bob_raw_pk, bob_sig))
    assert(Key.verify(bob_hex_pk, bob_sig))

    # Check it fails on by wrong key
    alice = Key.generate()
    assert(Key.verify(alice.publickey(), bob_sig) == False)

    # can load key from privatekey hex
    #bob_again = Key(bob.privatekey(tohex=True))
    #assert(Key.verify(bob_again.publickey(), bob_sig))
    a = bob.privatekey()
    b = from_hex(bob.privatekey(tohex=True))
    assert(a == b)

    z = Key.fromPrivateKey(bob.privatekey(tohex=True))
    assert(z.privatekey() == bob.privatekey())
    assert(z.publickey() == bob.publickey())
    assert(z.address() == bob.address())

    assert(Key.verify(z.publickey(), bob_sig))

    seed1 = keccak(b'bob')
    h = Key.generate(seed=seed1)
    i = Key.generate(seed=seed1)
    assert(len(h.address()) == 20)
    assert(i.address() == h.address())

    # Test create_address
    addy2 = create_address(bob.publickey(tohex=True))
    assert(addy2 == bob.address())
