
import rlp
from trie import Trie
from trie.db.memory import MemoryDB
from rlp.sedes import big_endian_int, binary

from .db import VanillaDB
from .accounts import Account
from .utils import keccak,int_to_big_endian

BLANK_ROOT_HASH = b''
CHAIN_METADATA_KEY = b'vanilla_meta_data'

def validate_address(value):
    if not isinstance(value, bytes) or not len(value) == 20:
        raise TypeError("Value {0} is not a valid canonical address".format(value))

def validate_is_bytes(value):
    if not isinstance(value, bytes):
        raise TypeError("Value must be a byte string.  Got: {0}".format(type(value)))

class chainMetaData(rlp.Serializable):
    fields = [
        ('chainid', binary),
        ('height', big_endian_int),
        ('apphash', binary)
    ]
    def __init__(self, chainid, height, apphash):
        super().__init__(chainid, height, apphash)

class StateTrie(object):
    def __init__(self, trie):
        self.trie = trie

    def __setitem__(self, key, value):
        self.trie[keccak(key)] = value

    def __getitem__(self, key):
        return self.trie[keccak(key)]

    def __delitem__(self, key):
        del self.trie[keccak(key)]

    def __contains__(self, key):
        return keccak(key) in self.trie

    @property
    def root_hash(self):
        return self.trie.root_hash

    def snapshot(self):
        return self.trie.snapshot()

    def revert(self, snapshot):
        return self.trie.revert(snapshot)

class State(object):
    """
    Talks directly to cold storage and the merkle
    only
    """
    def __init__(self, db, chainid, height, apphash):
        self.db = db
        self.chain_id = chainid
        self.last_block_height = height
        self.last_block_hash = apphash
        self.storage = StateTrie(Trie(self.db, apphash))
        """
        if dbfile:
            self.storage = StateTrie(Trie(VanillaDB(dbfile), root_hash))
        else:
            # in memory - testing
            self.storage = StateTrie(Trie(MemoryDB(), root_hash))
        """

    @classmethod
    def load_state(cls, dbfile):
        """ Create or load State.
        returns: (State, is_new) where 'is_new' is T|F indicating whether
        this the first run.
        """
        if not dbfile:
            return (cls(MemoryDB(), b'testchain', 0, BLANK_ROOT_HASH), True)

        # ASSSUMES THE PATH TO THE FILE EXISTS - IF NEW
        db = VanillaDB(dbfile)
        serial = db.get(CHAIN_METADATA_KEY)
        if serial:
            meta = rlp.decode(serial,sedes=chainMetaData)
            return (cls(db, meta.chainid, meta.height, meta.apphash), db.is_new)

        return (cls(db, b'', 0, BLANK_ROOT_HASH), db.is_new)

    def save(self):
        apphash = self.storage.root_hash
        # Save to storage
        meta = chainMetaData(self.chain_id, self.last_block_height, apphash)
        serial = rlp.encode(meta, sedes=chainMetaData)
        self.db.set(CHAIN_METADATA_KEY, serial)
        return apphash

    def close(self):
        if self.db and isinstance(self.db, VanillaDB):
            self.db.close()

    def put_storage(self, key, value):
        if not key:
            raise TypeError("Key cannot be blank")
        validate_is_bytes(value)
        self.storage[key] = value

    def get_storage(self, key):
        if key in self.storage:
            return self.storage[key]
        return b''

    def get_account(self, address):
        validate_address(address)
        acctbits = self.get_storage(address)
        if acctbits:
            acct = rlp.decode(acctbits, sedes=Account)
            acct.allow_changes()
            return acct
        return None

    def update_account(self, acct):
        if acct and isinstance(acct, Account):
            self.storage[acct.address()] = rlp.encode(acct, sedes=Account)

class cachedValue(object):
    def __init__(self, value=b'', dirty=False):
        self.dirty = dirty
        self.value = value

    def is_dirty(self):
        return self.dirty

class StateCache(object):
    def __init__(self, stateobj):
        self.backend = stateobj
        self.storage_cache = {}
        self.account_cache = {}

    def put_data(self, key, value):
        if not key:
            raise TypeError("Key cannot be blank")
        validate_is_bytes(value)
        self.storage_cache[key] = cachedValue(value=value, dirty=True)

    def get_data(self, key):
        if key in self.storage_cache:
            return self.storage_cache[key].value
        # not in cache go to storage
        value = self.backend.get_storage(key)
        if value:
            # put in the cache
            self.storage_cache[key] = cachedValue(value=value)
            return value
        return b''

    def get_account(self, address):
        if address in self.account_cache:
            return self.account_cache[address].value
        # not in cache go to account storage
        acct = self.backend.get_account(address)
        if acct:
            self.account_cache[address] = cachedValue(value=acct)
            return acct
        return b''

    def increment_nonce(self, address):
        validate_address(address)
        acct = self.get_account(address)
        if acct:
            acct.nonce += 1
            self.update_account(acct)

    def update_account(self, acct):
        if acct and isinstance(acct, Account):
            self.account_cache[acct.address()] = cachedValue(value=acct, dirty=True)

    def commit(self):
        # update storage
        for k1, c1 in self.storage_cache.items():
            if c1.is_dirty():
                self.backend.put_storage(k1, c1.value)

        for _, c2 in self.account_cache.items():
            if c2.is_dirty():
                self.backend.update_account(c2.value)

        return self.backend.storage.root_hash

class Storage(object):
    """ Wrapper of state and cache(s) used in the app and passed to handlers.
    commit is called on abci.commit to persist to the apphash and other metadata
    while also resetting the unconfirmed cache
    """
    def __init__(self, state):
        self.state = state
        self._confirmed = StateCache(state)
        self._unconfirmed = StateCache(state)

    @property
    def unconfirmed(self):
        return self._unconfirmed

    @property
    def confirmed(self):
        return self._confirmed

    def commit(self):
        # commit to storage
        self._confirmed.commit()
        # save
        apphash = self.state.save()
        # reset caches
        self._unconfirmed = StateCache(self.state)
        self._confirmed = StateCache(self.state)

        return apphash
