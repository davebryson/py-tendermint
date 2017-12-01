import rlp
from rlp.sedes import big_endian_int, binary, raw

from .utils import from_hex, is_hex
from .keys import create_address

class Account(rlp.Serializable):
    fields = [
        ('nonce', big_endian_int),
        ('balance', big_endian_int),
        ('pubkey', binary)
    ]

    def __init__(self, nonce, balance, pubkey):
        super(Account, self).__init__(nonce, balance, pubkey)

    @classmethod
    def create_account(cls, pubkey, nonce=0, balance=0):
        if is_hex(pubkey):
            pubkey = from_hex(pubkey)
        return cls(nonce, balance, pubkey)

    def address(self):
        return create_address(self.pubkey)

    def allow_changes(self):
        self._mutable = True
