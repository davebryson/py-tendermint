import hashlib, json

import nacl.bindings
from nacl import encoding
from nacl.utils import random

from .utils import to_hex, from_hex, is_hex, str_to_bytes

def create_address(pubkey):
    if is_hex(pubkey):
        pubkey = from_hex(pubkey)

    h = hashlib.new('ripemd160')
    h.update(pubkey)
    return h.digest()

class Key(object):

    def __init__(self, public_key,secret_key):
        self._pubkey = public_key
        self._privkey = secret_key
        self._address = create_address(self._pubkey)

    @classmethod
    def generate(cls, seed=None):
        if seed:
            if not isinstance(seed, bytes):
                raise Exception("Seed must be bytes")

            if len(seed) != nacl.bindings.crypto_sign_SEEDBYTES:
                raise Exception(
                    "The seed must be exactly {} bytes long".format(nacl.bindings.crypto_sign_SEEDBYTES)
                )

            public_key, secret_key = nacl.bindings.crypto_sign_seed_keypair(seed)
        else:
            r = random(nacl.bindings.crypto_sign_SEEDBYTES)
            public_key, secret_key = nacl.bindings.crypto_sign_seed_keypair(r)

        return cls(public_key, secret_key)

    @classmethod
    def fromPrivateKey(cls, sk):
        if len(sk) < 64:
            raise Exception('Not a private key')

        if is_hex(sk):
            sk = from_hex(sk)
        pubkey = sk[32:]
        return cls(pubkey, sk)

    @classmethod
    def verify(cls, pubkey, message):
        if is_hex(pubkey):
            pubkey = from_hex(pubkey)

        smessage = encoding.RawEncoder.decode(message)
        pk = encoding.RawEncoder.decode(pubkey)
        try:
            return nacl.bindings.crypto_sign_open(smessage, pk)
        except:
            # Bad or forged signature
            return False

    def sign(self, msg):
        message = str_to_bytes(msg)
        raw_signed = nacl.bindings.crypto_sign(message, self._privkey)
        return encoding.RawEncoder.encode(raw_signed)

    def address(self, tohex=False):
        if tohex:
            return to_hex(self._address)
        return self._address

    def publickey(self, tohex=False):
        if tohex:
            return to_hex(self._pubkey)
        return self._pubkey

    def privatekey(self, tohex=False):
        if tohex:
            return to_hex(self._privkey)
        return self._privkey

    def to_json(self):
        result = {
            'address': self.address(tohex=True),
            'publickey': self.publickey(tohex=True),
            'privatekey': self.privatekey(tohex=True)
        }
        return json.dumps(result,indent=2)
