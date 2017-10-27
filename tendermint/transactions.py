import rlp
from rlp.sedes import big_endian_int, binary

from .keys import Key
from .utils import keccak

class Transaction(rlp.Serializable):
    fields = [
        ('sender', binary),
        ('to', binary),
        ('nonce', big_endian_int),
        ('value', big_endian_int),
        ('call', binary),
        ('signature', binary),
        ('params', binary)
    ]

    def __init__(
        self,
        sender=b'',
        to=b'',
        nonce=0,
        value=0,
        call=b'',
        signature=b'',
        params=b''
    ):
        super().__init__(sender, to, nonce, value, call, signature, params)

    def sign(self, key):
        if not isinstance(key, Key):
            raise Exception("Can only sign with a Key object")

        # Local variable to hold params for the signing process
        original_params = None

        # Set sender to signer... no tomfoolery allowed
        self.sender = key.address()

        if self.params:
            # make a copy to reset after signing
            original_params = self.params
            self.params = rlp.encode(self.params, sedes=self.params.__class__)

        encoded = rlp.encode(self, sedes=UnsignedTransaction)
        rawhash = keccak(encoded)
        self.signature = key.sign(rawhash)

        if original_params:
            self.params = original_params

        return self

    def encode(self):
        if self.params:
            self.params = rlp.encode(self.params, sedes=self.params.__class__)
        return rlp.encode(self, sedes=Transaction)

    @classmethod
    def decode(cls, bits):
        outer = rlp.decode(bits, sedes=cls)
        return outer

    def decode_params(self, dataclz):
        if self.params:
            try:
                return rlp.decode(self.params, sedes=dataclz)
            except:
                raise Exception("Can deserialize params. Are you decoding with the right class")
        # Just being explicit
        return None

UnsignedTransaction = Transaction.exclude(['signature'])
